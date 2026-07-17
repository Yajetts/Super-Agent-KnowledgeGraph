"""Centralized access to OpenAI-backed language model calls."""

from __future__ import annotations

from functools import lru_cache

from langchain_openai import ChatOpenAI

from config.settings import get_settings


class LLMService:
    """Reusable wrapper around the configured OpenAI chat model."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openai_api_key
        self._model = settings.openai_model
        self._base_url = settings.openai_base_url
        
        print("API key loaded:", bool(self._api_key))
        print("Model:", self._model)
        print("Base URL:", repr(self._base_url))

        self._client = None

    def _get_client(self) -> ChatOpenAI:
            if self._client is not None:
                return self._client

            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured.")

            #client_kwargs: dict[str, str] = {
            #       "api_key": self._api_key,
            #       "model": self._model,
            #   }
            client_kwargs = {
                "api_key": self._api_key,   
                "model": self._model,
                "base_url": "https://api.openai.com/v1"     
            }

            if self._base_url:
                client_kwargs["base_url"] = self._base_url

            self._client = ChatOpenAI(
                api_key=self._api_key,
                model=self._model,
                base_url="https://api.openai.com/v1"
            )
            
            #print("CLIENT CREATED:", self._client)
            return self._client
    
        

    def generate(self, prompt: str) -> str:
        """Generate a completion for the supplied prompt."""
        try:
            #response = self._get_client().invoke(prompt)
            client = self._get_client()

            #print("CLIENT TYPE:", type(client))
            #print("CLIENT OBJECT:", client)
            response = client.invoke(prompt)

        except Exception as exc:
            print(f"\n\nOPENAI ERROR: {repr(exc)}\n\n")
            raise RuntimeError(f"OpenAI request failed: {exc}") from exc

        content = getattr(response, "content", "")
        return str(content).strip()


@lru_cache(maxsize=1)
def get_llm_service() -> LLMService:
    """Return a cached language model service instance."""
    return LLMService()