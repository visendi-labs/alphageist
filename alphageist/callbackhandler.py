from collections.abc import Callable    
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import LLMResult

class CustomStreamHandler(StreamingStdOutCallbackHandler):
    
    def __init__(self, on_llm_new_token:Callable[[str],None], on_llm_end:Callable[[LLMResult],None]):
        super().__init__()
        self._on_llm_new_token = on_llm_new_token
        self._on_llm_end = on_llm_end

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        self._on_llm_new_token(token, **kwargs)

    def on_llm_end(self, response:LLMResult, **kwargs) -> None:
        """Run when LLM ends running."""
        self._on_llm_end(response, **kwargs)

