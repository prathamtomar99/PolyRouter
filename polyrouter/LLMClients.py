# File act as a interface between user defined universal call functions and llm clients specific invoke functions


# ALL the clients to which i can make calls

from abc import ABC, abstractmethod
import os
import groq
from dotenv import load_dotenv
import json
import threading
from groq import Groq
from google import genai
from google.genai import types
from polyrouter.config import (
    GROQ_MODEL, GROQ_KEY, GEMINI_MODEL, GEMINI_KEY,
    UTILS_DIR, DEBUG, IN_DEPTH_DEBUG, CEREBRAS_KEY, CEREBRAS_MODEL
)
from polyrouter.Exceptions import (
    NoAPIKeysError, NoModelMentioned, UnknownError
)
from cerebras.cloud.sdk import Cerebras

load_dotenv()
CURR_DIR = UTILS_DIR / "LLMClients.py"

class LLM(ABC):
    """
    Each LLM subclass manages its own keys and models.
    call() returns None when fully exhausted (all keys x all models tried).
    InitLLM uses this signal to switch to the next client.
    """
    @abstractmethod
    def call(self, user_input, json_mode=False):
        pass


# ------------------------------------------- GEMINI ------------------------------------------- 
# cannot move proactively as gemini doesn't provide the TPM left
# check if it is giving response, if it stucks then rotate model 
class GeminiLLM(LLM):
    def __init__(self, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=500):
        if len(GEMINI_MODEL) == 0:
            raise NoModelMentioned("GEMINI : No models listed in GEMINI_MODEL.")

        self.prompt = prompt
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._lock = threading.Lock()
        self.clients = []

        # storing all client so that we dont get any issue once clients are build 
        for key_no in range(GEMINI_KEY):
            api_key = os.getenv(f"GEMINI_API_KEY{key_no}")
            if api_key and api_key.startswith("AIz"):

                # check if key is really valid or not -> pipeline doenst break inbetween 
                try:
                    client = genai.Client(api_key=api_key)
                    contents = [
                        types.Content(
                            role="user",
                            parts=[types.Part(text="Reply: ok")]
                        )
                    ]
                    response = client.models.generate_content(
                        model=GEMINI_MODEL[0],
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=100,
                        )
                    )
                    self.clients.append(client)

                    if(IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI : Working Key {key_no} -> {api_key}")
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : Output: ",response.text)

                    # # What is the current api fails for 1/2 model and works on other -> just give a warning to user 
                    # for model in GEMINI_MODEL:
                    #     try:
                    #         response = client.models.generate_content(
                    #             model=model,
                    #             contents=contents,
                    #             config=types.GenerateContentConfig(
                    #                 temperature=0.1,
                    #                 max_output_tokens=100,
                    #             )
                    #         )

                    #         if(IN_DEPTH_DEBUG):
                    #             print("===============================================================")
                    #             print(f"\tGEMINI : Working Model {model}")
                    #             print("Output: ",response.text)

                        
                    #     except Exception as e:
                    #         print("===============================================================")
                    #         print(f"GEMINI : Model usage failed {key_no} -> {api_key} : {model}")
                    #         print("===============================================================")
                    #         # # Uncomment if you want to stop in between if model fails
                    #         # raise UnknownError(f"GEMINI : Model usage failed {key_no} -> {api_key} : {model}")
                        

                except Exception as e:
                    print("===============================================================")
                    print(f"[{CURR_DIR}] : GEMINI : API usage failed {key_no} -> {api_key} ")
                    print("===============================================================")
                    # # Uncomment if you want to fail if api key fails
                    # raise UnknownError(f"GEMINI : API Error Initialising or 1st Model in GEMINI_LLM failed : with API key {key_no} -> {api_key}")
                    # print("===============================================================")

            else:
                raise NoAPIKeysError(f"GEMINI : Key {key_no} is missing or has an invalid format.")

        if len(self.clients) == 0:
            raise NoAPIKeysError("GEMINI : No valid API keys found.")

        self.models = list(GEMINI_MODEL)  
        self.current_model_idx = 0
        self.current_client_idx = 0


    def _get_current(self):
        with self._lock:
            if DEBUG:
                print(f"Using Model : {self.models[self.current_model_idx]}")
            return (
                self.clients[self.current_client_idx],
                self.models[self.current_model_idx]
            )


    def _rotate_client(self):
        """Move to next key. Returns True if a full cycle of all keys is complete."""
        with self._lock:
            self.current_client_idx += 1
            if self.current_client_idx == len(self.clients):
                self.current_client_idx = 0


    def _rotate_model(self):
        """Move to next model. Returns True if all models are exhausted."""
        with self._lock:
            self.current_model_idx += 1
            self.current_client_idx = 0
            if self.current_model_idx == len(self.models):
                self.current_model_idx = 0


    def call(self, user_input, json_mode=False):
        """
        Rotation strategy:
          1. Try current key on current model.
          2. On failure -> rotate key.
          3. All keys exhausted on current model -> rotate model, reset keys.
          4. All models exhausted -> return None (signals InitLLM to switch client).
        """
        models_tried = 0

        while models_tried < len(self.models):
            keys_tried = 0

            while keys_tried < len(self.clients):
                client, model = self._get_current()
                try:

                    contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]
                    config = types.GenerateContentConfig(
                        system_instruction=self.prompt,
                        temperature=self.temperature,
                        max_output_tokens=self.max_output_tokens,
                        response_mime_type="application/json" if json_mode else None
                    )
                    response = client.models.generate_content(model=model, contents=contents, config=config)

                    output_text = response.text

                    if(IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : {user_input}      :       {output_text}")

                    if json_mode:
                        return json.loads(output_text)
                    return output_text

                except Exception as e:
                    if IN_DEPTH_DEBUG:
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI Unknown error on key {self.current_client_idx}: {e}")
                    keys_tried += 1
                    self._rotate_client()

            if IN_DEPTH_DEBUG:
                print("===============================================================")
                print(f"[{CURR_DIR}] : GEMINI All keys exhausted for model '{self.models[self.current_model_idx]}'. Rotating model.")

            models_tried += 1
            self._rotate_model()


        if DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : GEMINI All keys x all models exhausted.")
        return None
    




# ------------------------------------------- GEMINI ------------------------------------------- 
# cannot move proactively as gemini doesn't provide the TPM left
# check if it is giving response, if it stucks then rotate model 
class GeminiLLM(LLM):
    def __init__(self, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=500):
        if len(GEMINI_MODEL) == 0:
            raise NoModelMentioned("GEMINI : No models listed in GEMINI_MODEL.")

        self.prompt = prompt
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._lock = threading.Lock()
        self.clients = []

        # storing all client so that we dont get any issue once clients are build 
        for key_no in range(GEMINI_KEY):
            api_key = os.getenv(f"GEMINI_API_KEY{key_no}")
            if api_key and api_key.startswith("AIz"):

                # check if key is really valid or not -> pipeline doenst break inbetween 
                try:
                    client = genai.Client(api_key=api_key)
                    contents = [
                        types.Content(
                            role="user",
                            parts=[types.Part(text="Reply: ok")]
                        )
                    ]
                    response = client.models.generate_content(
                        model=GEMINI_MODEL[0],
                        contents=contents,
                        config=types.GenerateContentConfig(
                            temperature=0.1,
                            max_output_tokens=100,
                        )
                    )
                    self.clients.append(client)

                    if(IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI : Working Key {key_no} -> {api_key}")
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : Output: ",response.text)

                    # # What is the current api fails for 1/2 model and works on other -> just give a warning to user 
                    # for model in GEMINI_MODEL:
                    #     try:
                    #         response = client.models.generate_content(
                    #             model=model,
                    #             contents=contents,
                    #             config=types.GenerateContentConfig(
                    #                 temperature=0.1,
                    #                 max_output_tokens=100,
                    #             )
                    #         )

                    #         if(IN_DEPTH_DEBUG):
                    #             print("===============================================================")
                    #             print(f"\tGEMINI : Working Model {model}")
                    #             print("Output: ",response.text)

                        
                    #     except Exception as e:
                    #         print("===============================================================")
                    #         print(f"GEMINI : Model usage failed {key_no} -> {api_key} : {model}")
                    #         print("===============================================================")
                    #         # # Uncomment if you want to stop in between if model fails
                    #         # raise UnknownError(f"GEMINI : Model usage failed {key_no} -> {api_key} : {model}")
                        

                except Exception as e:
                    print("===============================================================")
                    print(f"[{CURR_DIR}] : GEMINI : API usage failed {key_no} -> {api_key} ")
                    print("===============================================================")
                    # # Uncomment if you want to fail if api key fails
                    # raise UnknownError(f"GEMINI : API Error Initialising or 1st Model in GEMINI_LLM failed : with API key {key_no} -> {api_key}")
                    # print("===============================================================")

            else:
                raise NoAPIKeysError(f"GEMINI : Key {key_no} is missing or has an invalid format.")

        if len(self.clients) == 0:
            raise NoAPIKeysError("GEMINI : No valid API keys found.")

        self.models = list(GEMINI_MODEL)  
        self.current_model_idx = 0
        self.current_client_idx = 0


    def _get_current(self):
        with self._lock:
            if DEBUG:
                print(f"Using Model : {self.models[self.current_model_idx]}")
            return (
                self.clients[self.current_client_idx],
                self.models[self.current_model_idx]
            )


    def _rotate_client(self):
        """Move to next key. Returns True if a full cycle of all keys is complete."""
        with self._lock:
            self.current_client_idx += 1
            if self.current_client_idx == len(self.clients):
                self.current_client_idx = 0


    def _rotate_model(self):
        """Move to next model. Returns True if all models are exhausted."""
        with self._lock:
            self.current_model_idx += 1
            self.current_client_idx = 0
            if self.current_model_idx == len(self.models):
                self.current_model_idx = 0


    def call(self, user_input, json_mode=False):
        """
        Rotation strategy:
          1. Try current key on current model.
          2. On failure -> rotate key.
          3. All keys exhausted on current model -> rotate model, reset keys.
          4. All models exhausted -> return None (signals InitLLM to switch client).
        """
        models_tried = 0

        while models_tried < len(self.models):
            keys_tried = 0

            while keys_tried < len(self.clients):
                client, model = self._get_current()
                try:

                    contents = [types.Content(role="user", parts=[types.Part(text=user_input)])]
                    config = types.GenerateContentConfig(
                        system_instruction=self.prompt,
                        temperature=self.temperature,
                        max_output_tokens=self.max_output_tokens,
                        response_mime_type="application/json" if json_mode else None
                    )
                    response = client.models.generate_content(model=model, contents=contents, config=config)

                    output_text = response.text

                    if(IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : {user_input}      :       {output_text}")

                    if json_mode:
                        return json.loads(output_text)
                    return output_text

                except Exception as e:
                    if IN_DEPTH_DEBUG:
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI Unknown error on key {self.current_client_idx}: {e}")
                    keys_tried += 1
                    self._rotate_client()

            if IN_DEPTH_DEBUG:
                print("===============================================================")
                print(f"[{CURR_DIR}] : GEMINI All keys exhausted for model '{self.models[self.current_model_idx]}'. Rotating model.")

            models_tried += 1
            self._rotate_model()


        if DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : GEMINI All keys x all models exhausted.")
        return None