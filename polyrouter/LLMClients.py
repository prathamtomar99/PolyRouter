# File act as a interface between user defined universal call functions and llm clients specific invoke functions


# ALL the clients to which i can make calls

from abc import ABC, abstractmethod
import os
import json
import threading
from groq import Groq
from google import genai
from google.genai import types
from .Exceptions import (
    NoAPIKeysError, NoModelMentioned, UnknownError
)
from cerebras.cloud.sdk import Cerebras

CURR_DIR = "LLMClients.py"

class LLM(ABC):
    """
    Each LLM subclass manages its own keys and models.
    call() returns None when fully exhausted (all keys x all models tried).
    InitLLM uses this signal to switch to the next client.
    """
    @abstractmethod
    def call(self, user_input, json_mode=False):
        pass


# If a particulat api key model crashes it should work for and it works for other api key, then dont crash the whole system , just switch api key
# always take the first model whose TPM is available (otherwise client building fails -> assume wrong client and crash)
# or hardcode model checking in try block e.g. model=GROQ_MODEL[0] -> model="openai/gpt-oss-120b"

# ------------------------------------------- GROQ ------------------------------------------- 

class GroqLLM(LLM):
    def __init__(self, GROQ_MODEL, GROQ_KEY, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=500,DEBUG=0,IN_DEPTH_DEBUG=0, test_mode=0):
        if len(GROQ_MODEL) == 0:
            raise NoModelMentioned("GROQ : No models listed in GROQ_MODELS.")
        if len(GROQ_KEY) == 0:
            raise NoAPIKeysError("GROQ : No api key listed in GROQ_KEYS.")
        
        self.DEBUG = DEBUG
        self.IN_DEPTH_DEBUG = IN_DEPTH_DEBUG
        self.prompt = prompt
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._lock = threading.Lock()
        self.clients = []

        # storing all client so that we dont get any issue once clients are build
        print("GROQ_KEY :",GROQ_KEY)
        for api_key in GROQ_KEY:
            if api_key and api_key.startswith("gsk"):

                # check if key is really valid or not -> pipeline doenst break inbetween
                try:
                    client = Groq(api_key=api_key)
                    response = client.chat.completions.create(
                        model=GROQ_MODEL[0],
                        messages=[
                            {"role": "user", "content": "Reply: ok"}
                        ],
                        max_completion_tokens=100
                    )
                    self.clients.append(client)
                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GROQ : Working Key {api_key}")
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : Output: ",response.choices[0].message.content)

                    # # What is the current api fails for 1/2 model and works on other -> just give a warning to user
                    if(test_mode): 
                        for model in GROQ_MODEL:
                            try:
                                response = client.chat.completions.create(
                                    model=model,
                                    messages=[
                                        {"role": "user", "content": "Reply: ok"}
                                    ],
                                    max_completion_tokens=100
                                )

                                if(self.IN_DEPTH_DEBUG):
                                    print("===============================================================")
                                    print(f"\tGROQ : Working Model {model}")
                                    print("Outout: ",response.choices[0].message.content)


                            except Exception as e:
                                print("===============================================================")
                                print(f"GROQ : Model usage failed {api_key} : {model}")
                                print("===============================================================")
                                # # Uncomment if you want to stop code if 'model' fails
                                # raise UnknownError(f"GROQ : Model usage failed -> {api_key} : {model}")
                        
                except Exception as e:
                    print("===============================================================")
                    print(f"[{CURR_DIR}] : GROQ : Model usage failed {api_key}")
                    if(self.IN_DEPTH_DEBUG):
                        print(e)
                    print("===============================================================")
                    # # Uncomment if you want to fail if api key fails
                    # raise UnknownError(f"GROQ : API Error Initialising or 1st Model in GROQ_LLM failed : with API key {api_key}")
                    # print("===============================================================")

            else:
                raise NoAPIKeysError(f"GROQ : Key {api_key} is missing or has an invalid format.")

        if len(self.clients) == 0:
            raise NoAPIKeysError("GROQ : No valid API keys found.")

        self.models = list(GROQ_MODEL)  
        self.current_model_idx = 0
        self.current_client_idx = 0


    def _get_current(self):
        with self._lock:
            if self.DEBUG:
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


    # return number of tokens left with current client 
    # if number of tokens left < 500, maybe for next response they are not enough, so rotate proactively
    def _get_remaining_tokens(self, response) -> int:
        tokens_str = response.headers.get('x-ratelimit-remaining-tokens')
        if self.IN_DEPTH_DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : GROQ Tokens Remaining: {tokens_str}")
        return int(tokens_str) if tokens_str is not None else 9999


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
                    kwargs = {
                        "model": model,
                        "temperature": self.temperature,
                        "max_tokens": self.max_output_tokens,
                        "messages": [
                            {"role": "system", "content": self.prompt},
                            {"role": "user", "content": user_input}
                        ]
                    }
                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}

                    response = client.chat.completions.with_raw_response.create(**kwargs)

                    if self._get_remaining_tokens(response) < 500:
                        if self.DEBUG:
                            print("===============================================================")
                            print(f"[{CURR_DIR}] : GROQ Low tokens on key {self.current_client_idx}, rotating proactively.")
                        keys_tried += 1
                        self._rotate_client()

                    parsed = response.parse()
                    output_text = parsed.choices[0].message.content

                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : {user_input}      :       {output_text}")

                    if json_mode:
                        return json.loads(output_text)
                    return output_text

                except Exception as e:
                    if self.IN_DEPTH_DEBUG:
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GROQ Unknown error on key {self.current_client_idx}: {e}")
                    keys_tried += 1
                    self._rotate_client()

            if self.IN_DEPTH_DEBUG:
                print("===============================================================")
                print(f"[{CURR_DIR}] : GROQ All keys exhausted for model '{self.models[self.current_model_idx]}'. Rotating model.")

            models_tried += 1
            self._rotate_model()


        if self.DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : GROQ All keys x all models exhausted.")
        return None



# ------------------------------------------- GEMINI ------------------------------------------- 
# cannot move proactively as gemini doesn't provide the TPM left
# check if it is giving response, if it stucks then rotate model 
class GeminiLLM(LLM):
    def __init__(self,GEMINI_MODEL, GEMINI_KEY, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=500,DEBUG=0,IN_DEPTH_DEBUG=0,test_mode=0):
        if len(GEMINI_MODEL) == 0:
            raise NoModelMentioned("GEMINI : No models listed in GEMINI_MODEL.")
        if len(GEMINI_KEY) == 0:
            raise NoAPIKeysError("GEMINI : No api key listed in GEMINI_KEYS.")

        self.DEBUG = DEBUG
        self.IN_DEPTH_DEBUG = IN_DEPTH_DEBUG
        self.prompt = prompt
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._lock = threading.Lock()
        self.clients = []

        # storing all client so that we dont get any issue once clients are build 
        for api_key in GEMINI_KEY:
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

                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI : Working Key {api_key}")
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : Output: ",response.text)

                    # # What is the current api fails for 1/2 model and works on other -> just give a warning to user 
                    if(test_mode):
                        for model in GEMINI_MODEL:
                            try:
                                response = client.models.generate_content(
                                    model=model,
                                    contents=contents,
                                    config=types.GenerateContentConfig(
                                        temperature=0.1,
                                        max_output_tokens=100,
                                    )
                                )

                                if(self.IN_DEPTH_DEBUG):
                                    print("===============================================================")
                                    print(f"\tGEMINI : Working Model {model}")
                                    print("Output: ",response.text)

                            
                            except Exception as e:
                                print("===============================================================")
                                print(f"GEMINI : Model usage failed {api_key} : {model}")
                                print("===============================================================")
                                # # Uncomment if you want to stop in between if model fails
                                # raise UnknownError(f"GEMINI : Model usage failed {api_key} : {model}")
                        

                except Exception as e:
                    print("===============================================================")
                    print(f"[{CURR_DIR}] : GEMINI : API usage failed {api_key} ")
                    if(self.IN_DEPTH_DEBUG):
                        print(e)
                    print("===============================================================")
                    # # Uncomment if you want to fail if api key fails
                    # raise UnknownError(f"GEMINI : API Error Initialising or 1st Model in GEMINI_LLM failed : with API key {api_key}")
                    # print("===============================================================")

            else:
                raise NoAPIKeysError(f"GEMINI : Key {api_key} is missing or has an invalid format.")

        if len(self.clients) == 0:
            raise NoAPIKeysError("GEMINI : No valid API keys found.")

        self.models = list(GEMINI_MODEL)  
        self.current_model_idx = 0
        self.current_client_idx = 0


    def _get_current(self):
        with self._lock:
            if self.DEBUG:
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

                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : {user_input}      :       {output_text}")

                    if json_mode:
                        return json.loads(output_text)
                    return output_text

                except Exception as e:
                    if self.IN_DEPTH_DEBUG:
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : GEMINI Unknown error on key {self.current_client_idx}: {e}")
                    keys_tried += 1
                    self._rotate_client()

            if self.IN_DEPTH_DEBUG:
                print("===============================================================")
                print(f"[{CURR_DIR}] : GEMINI All keys exhausted for model '{self.models[self.current_model_idx]}'. Rotating model.")

            models_tried += 1
            self._rotate_model()


        if self.DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : GEMINI All keys x all models exhausted.")
        return None
    





# ------------------------------------------- CEREBRAS ------------------------------------------- 
# cannot move proactively as gemini doesn't provide the TPM left
# check if it is giving response, if it stucks then rotate model 
class CereBrasLLM(LLM):
    def __init__(self, CEREBRAS_MODEL, CEREBRAS_KEY, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=500,DEBUG=0,IN_DEPTH_DEBUG=0, test_mode=0):
        if len(CEREBRAS_MODEL) == 0:
            raise NoModelMentioned("CEREBRAS : No models listed in CEREBRAS_MODEL.")
        if len(CEREBRAS_KEY) == 0:
            raise NoAPIKeysError("CEREBRAS : No api key listed in CEREBRAS_KEYS.")

        self.DEBUG = DEBUG
        self.IN_DEPTH_DEBUG = IN_DEPTH_DEBUG
        self.prompt = prompt
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self._lock = threading.Lock()
        self.clients = []

        # storing all client so that we dont get any issue once clients are build
        for api_key in CEREBRAS_KEY:
            if api_key and api_key.startswith("csk"):

                # check if key is really valid or not -> pipeline doenst break inbetween
                try:
                    client = Cerebras(api_key=api_key)
                    response = client.chat.completions.create(
                        model=CEREBRAS_MODEL[0],
                        max_completion_tokens=200,
                        temperature=0.2,
                        top_p=1,
                        messages=[
                            {
                                "role": "system",
                                "content": "Output exactly the requested text. No extra words."
                            },
                            {
                                "role": "user",
                                "content": "Return exactly: ok"
                            }
                        ],
                    )
                    self.clients.append(client)
                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : CEREBRAS : Working Key {api_key}")
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : Output: ",response.choices[0].message.content)

                    # # What is the current api fails for 1/2 model and works on other -> just give a warning to user 
                    if(test_mode):
                        for model in CEREBRAS_MODEL:
                            try:
                                response = client.chat.completions.create(
                                    model=model,
                                    max_completion_tokens=200,
                                    temperature=0.2,
                                    top_p=1,
                                    messages=[
                                        {
                                            "role": "system",
                                            "content": "Output exactly the requested text. No extra words."
                                        },
                                        {
                                            "role": "user",
                                            "content": "Return exactly: ok"
                                        }
                                    ],
                                )

                                if(self.IN_DEPTH_DEBUG):
                                    print("===============================================================")
                                    print(f"\tCEREBRAS : Working Model {model}")
                                    print("Outout: ",response.choices[0].message.content)


                            except Exception as e:
                                print("===============================================================")
                                print(f"CEREBRAS : Model usage failed {api_key} : {model}")
                                print("===============================================================")
                                # # Uncomment if you want to stop code if 'model' fails
                                # raise UnknownError(f"CEREBRAS : Model usage failed {api_key} : {model}")
                        
                except Exception as e:
                    print("===============================================================")
                    print(f"[{CURR_DIR}] : CEREBRAS : Model usage failed {api_key}")
                    if(self.IN_DEPTH_DEBUG):
                        print(e)
                    print("===============================================================")
                    # # Uncomment if you want to fail if api key fails
                    # raise UnknownError(f"CEREBRAS : API Error Initialising or 1st Model in CEREBRAS_LLM failed : with API key {api_key}")
                    # print("===============================================================")

            else:
                raise NoAPIKeysError(f"CEREBRAS : Key {api_key} is missing or has an invalid format.")

        if len(self.clients) == 0:
            raise NoAPIKeysError("CEREBRAS : No valid API keys found.")

        self.models = list(CEREBRAS_MODEL)  
        self.current_model_idx = 0
        self.current_client_idx = 0


    def _get_current(self):
        with self._lock:
            if self.DEBUG:
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
                    kwargs = {
                        "model": model,
                        "temperature": self.temperature,
                        "max_tokens": self.max_output_tokens,
                        "messages": [
                            {"role": "system", "content": self.prompt},
                            {"role": "user", "content": user_input}
                        ]
                    }

                    if json_mode:
                        kwargs["response_format"] = {"type": "json_object"}

                    response = client.chat.completions.with_raw_response.create(**kwargs)

                    parsed_response = response.parse()
                    output_text = parsed_response.choices[0].message.content

                    if(self.IN_DEPTH_DEBUG):
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : {user_input}      :       {output_text}")

                    if json_mode:
                        return json.loads(output_text)
                    return output_text

                except Exception as e:
                    if self.IN_DEPTH_DEBUG:
                        print("===============================================================")
                        print(f"[{CURR_DIR}] : CEREBRAS Unknown error on key {self.current_client_idx}: {e}")
                    keys_tried += 1
                    self._rotate_client()

            if self.IN_DEPTH_DEBUG:
                print("===============================================================")
                print(f"[{CURR_DIR}] : CEREBRAS All keys exhausted for model '{self.models[self.current_model_idx]}'. Rotating model.")

            models_tried += 1
            self._rotate_model()


        if self.DEBUG:
            print("===============================================================")
            print(f"[{CURR_DIR}] : CEREBRAS All keys x all models exhausted.")
        return None
