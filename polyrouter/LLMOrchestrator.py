# File respnsible for handling LLMClients and handle dynamic model and client routing


from .LLMClients import LLM, GroqLLM, GeminiLLM, CereBrasLLM
from .Exceptions import AllClientsExhaustedError, AllModelsFailedError
import threading

CURR_DIR = "LLMOrchestrator"

class LLMOrchestrator:
    """
    - Holds all LLM Client Object.
    - Stays on current client until it returns None (fully exhausted).
    - Moves to next client and stays there until it too is exhausted.
    - Raises AllModelsFailedError only when every client is exhausted.
    """
 
    def __init__(self, groq=None, gemini=None, cerebras=None, debug = 0, verbose = 0, prompt="You are a helpful assistant", temperature=0.5, max_output_tokens=1000,test_mode=0):
        self.clients: list[LLM] = []
        if(groq and groq.get("groq_models") and groq.get("groq_keys")):
            if(debug):
                print("GROQ_KEYS: ",groq["groq_keys"])
            self.clients.append(
                GroqLLM(groq["groq_models"], groq["groq_keys"], prompt=prompt, temperature=temperature,max_output_tokens=max_output_tokens,DEBUG=debug,IN_DEPTH_DEBUG=verbose,test_mode=test_mode),
            )

        if(gemini and gemini.get("gemini_models") and gemini.get("gemini_keys")):
            if(debug):
                print("GEMINI_KEYS: ",gemini["gemini_keys"])
            self.clients.append(
                GeminiLLM(gemini["gemini_models"], gemini["gemini_keys"], prompt=prompt, temperature=temperature,max_output_tokens=max_output_tokens,DEBUG=debug,IN_DEPTH_DEBUG=verbose,test_mode=test_mode),
            )

        if(cerebras and cerebras.get("cerebras_models") and cerebras.get("cerebras_keys")):
            if(debug):
                print("CEREBRAS_KEYS: ",cerebras["cerebras_keys"])
            self.clients.append(
                CereBrasLLM(cerebras["cerebras_models"], cerebras["cerebras_keys"], prompt=prompt, temperature=temperature,max_output_tokens=max_output_tokens,DEBUG=debug,IN_DEPTH_DEBUG=verbose,test_mode=test_mode),
            )
 
        if len(self.clients) == 0:
            raise AllClientsExhaustedError("InitLLM : No LLM clients configured. Either models or keys are empty")
 
        self.current_idx = 0
        self.DEBUG = debug
        self.IN_DEPTH_DEBUG = verbose
        self._lock = threading.Lock()
 
    def _rotate_client(self) -> bool:
        """Move to next available client. Returns False if all are exhausted."""
        with self._lock:
            self.current_idx += 1
            return self.current_idx < len(self.clients)
 
    def call(self, user_input, json_mode=False):
        """
        Try current client. If it returns None (exhausted),
        move to next and stay there. Repeat until all exhausted.
        """
        while True:
            with self._lock:
                current_client = self.clients[self.current_idx]
 
            result = current_client.call(user_input, json_mode=json_mode)
 
            if result is not None:
                return result
 
            # Current client fully exhausted — move to next
            if self.DEBUG:
                print(f"[{CURR_DIR}] Client {self.current_idx} ({type(current_client).__name__}) exhausted. Switching.")
 
            has_next = self._rotate_client()
 
            if not has_next:
                break
 
        # instead of this we can put a while loop which breaks and raise error after 5 or 10 repetative failures
        # cause every failure tells a story -> maybe that failure is no more a failure
        # are bhaiya recover ho gaya hoga so (TPM resets after 1 min in groq sooo) (not in gemini)
        raise AllModelsFailedError(
            f"[{CURR_DIR}] All clients and models failed -> {CURR_DIR}"
        )