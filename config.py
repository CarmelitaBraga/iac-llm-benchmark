"""Model configurations for deterministic IaC defect classification."""

from dataclasses import dataclass
from typing import Optional
import os


@dataclass
class ModelConfig:
    """Configuration for a specific LLM model."""
    name: str
    provider: str  # e.g., 'openai', 'gemini', 'qwen'
    temperature: float = 0
    top_p: float = 1
    top_k: int = 1
    max_tokens: int = 2048

    # Retry and delay settings
    max_retries: int = 3
    initial_delay: float = 1.0  # Initial delay in seconds for exponential backoff
    max_delay: float = 30.0  # Maximum delay in seconds

    # API-specific
    api_key_env_var: Optional[str] = None
    api_base_url: Optional[str] = None
    default_headers: Optional[dict] = None


# Model configurations for scientific reproducibility
# All temperatures set to 0 for maximum determinism
MODELS = {
    'deepseek-v3': ModelConfig(
        name='deepseek-v3',
        provider='deepseek',
        temperature=0,
        max_tokens=2048,
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        api_key_env_var='DEEPSEEK_API_KEY',
        api_base_url='DEEPSEEK_API_URL',
    ),
    'gpt-5.2': ModelConfig(
        name='gpt-5.2',
        provider='openai',
        temperature=0,
        max_tokens=2048,
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        api_key_env_var='OPENAI_API_KEY',
        api_base_url='OPENAI_API_URL',
    ),
    'qwen3-coder-480b-a35b-i': ModelConfig(
        name='qwen3-coder-480b-a35b-i',
        provider='qwen',
        temperature=0,
        max_tokens=2048,
        max_retries=3,
        initial_delay=1.0,
        max_delay=30.0,
        api_key_env_var='QWEN_API_KEY',
        api_base_url='QWEN_API_URL',
    ),
}

# Defect categories
CATEGORIES = {
    'CONFIGURATION_DATA',
    'DEPENDENCY',
    'DOCUMENTATION',
    'CONDITIONAL',
    'SERVICE',
    'IDEMPOTENCY',
    'SECURITY',
    'SYNTAX',
    'NO_DEFECT',
}

# Processing settings
BATCH_SIZE = 10  # Commits per API request
CHECKPOINT_FREQUENCY = 10  # Save checkpoint every N batches
DEFAULT_DELAY_BETWEEN_REQUESTS = 5  # Delay between requests in seconds
