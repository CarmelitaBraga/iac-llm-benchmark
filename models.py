"""Base model abstraction and specific model implementations."""

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Optional

from config import ModelConfig


logger = logging.getLogger(__name__)


class BaseModel(ABC):
    """Abstract base class for LLM models."""

    def __init__(self, config: ModelConfig):
        self.config = config
        self.name = config.name
        self.retry_count = 0

    @abstractmethod
    def classify(self, commit_data: str) -> str:
        """
        Classify a single commit and return the response.

        Args:
            commit_data: Formatted commit information (hash, diff, message)

        Returns:
            Raw response from the model
        """
        pass

    def _get_api_key(self) -> str:
        """Get API key from environment."""
        if not self.config.api_key_env_var:
            raise ValueError(f"No API key configured for {self.name}")

        api_key = os.getenv(self.config.api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Missing {self.config.api_key_env_var} environment variable"
            )
        return api_key

    def _exponential_backoff(self, retry_count: int) -> float:
        """Calculate exponential backoff delay."""
        delay = self.config.initial_delay * (2 ** retry_count)
        return min(delay, self.config.max_delay)


class GeminiModel(BaseModel):
    """Google Gemini model implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            from google import genai
            from google.genai import types
            self.genai = genai
            self.types = types
            self.client = genai.Client(api_key=self._get_api_key())
        except ImportError:
            raise ImportError("Please install google-genai: pip install google-genai>=1.5.0")

    def classify(self, commit_data: str) -> str:
        """Call Gemini API with deterministic settings."""
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.name,
                    contents=commit_data,
                    config=self._get_generation_config(),
                )
                return response.text
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(
                        f"Gemini request failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Gemini request failed after {self.config.max_retries} attempts: {e}")
                    raise

    def _get_generation_config(self):
        """Build generation config for Gemini."""
        try:
            from google.genai import types
            return types.GenerateContentConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
                max_output_tokens=self.config.max_tokens,
            )
        except Exception:
            # Fallback for older API versions
            return {
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "top_k": self.config.top_k,
                "max_output_tokens": self.config.max_tokens,
            }


class OpenAIModel(BaseModel):
    """OpenAI GPT model implementation or OpenAI-compatible endpoints."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            api_key = self._get_api_key()

            # Build OpenAI client with optional custom base_url and headers
            client_kwargs = {'api_key': api_key}

            if config.api_base_url:
                client_kwargs['base_url'] = config.api_base_url

            if config.default_headers:
                client_kwargs['default_headers'] = config.default_headers

            self.client = OpenAI(**client_kwargs)
        except ImportError:
            raise ImportError("Please install openai: pip install openai>=1.0.0")

    def classify(self, commit_data: str) -> str:
        """Call OpenAI API with deterministic settings."""
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.name,
                    messages=[
                        {"role": "user", "content": commit_data}
                    ],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(
                        f"OpenAI request failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"OpenAI request failed after {self.config.max_retries} attempts: {e}")
                    raise


class QwenModel(BaseModel):
    """Qwen model implementation via DashScope."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            api_key = self._get_api_key()
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.api_base_url,
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai>=1.0.0")

    def classify(self, commit_data: str) -> str:
        """Call Qwen API via OpenAI-compatible endpoint."""
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.name,
                    messages=[
                        {"role": "user", "content": commit_data}
                    ],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(
                        f"Qwen request failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Qwen request failed after {self.config.max_retries} attempts: {e}")
                    raise


class DeepSeekModel(BaseModel):
    """DeepSeek model implementation via OpenAI-compatible endpoint."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)
        try:
            from openai import OpenAI
            api_key = self._get_api_key()
            self.client = OpenAI(
                api_key=api_key,
                base_url=config.api_base_url,
            )
        except ImportError:
            raise ImportError("Please install openai: pip install openai>=1.0.0")

    def classify(self, commit_data: str) -> str:
        """Call DeepSeek API via OpenAI-compatible endpoint."""
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.name,
                    messages=[
                        {"role": "user", "content": commit_data}
                    ],
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    max_tokens=self.config.max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < self.config.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(
                        f"DeepSeek request failed (attempt {attempt + 1}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"DeepSeek request failed after {self.config.max_retries} attempts: {e}")
                    raise


# Provider registry - add/remove providers here for easy configuration
PROVIDER_REGISTRY = {
    'gemini': GeminiModel,
    'openai': OpenAIModel,
    'qwen': QwenModel,
    'deepseek': DeepSeekModel,
}


def create_model(config: ModelConfig) -> BaseModel:
    """
    Factory function to create appropriate model instance.

    Providers are configured in PROVIDER_REGISTRY. To add a new provider:
    1. Create a model class inheriting from BaseModel
    2. Add an entry to PROVIDER_REGISTRY: 'provider_name': ModelClass
    """
    if config.provider not in PROVIDER_REGISTRY:
        available = ', '.join(PROVIDER_REGISTRY.keys())
        raise ValueError(f"Unknown provider '{config.provider}'. Available: {available}")

    model_class = PROVIDER_REGISTRY[config.provider]
    return model_class(config)
