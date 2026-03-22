import json
import logging
import time
from typing import Optional

from django.conf import settings

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base LLM error."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Request timed out."""
    pass


class LLMClient:
    """
    OpenAI-compatible LLM client with retry logic and error handling.
    Reads OPENAI_API_KEY and OPENAI_BASE_URL from Django settings.
    """

    def __init__(self, provider: str = 'openai'):
        self.provider = provider
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.default_model = settings.OPENAI_DEFAULT_MODEL
        self.fast_model = settings.OPENAI_FAST_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                )
            except ImportError:
                raise LLMError("openai package is not installed. Run: pip install openai")
        return self._client

    def complete(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        response_format: Optional[dict] = None,
    ) -> dict:
        """
        Send a chat completion request.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier. Defaults to OPENAI_DEFAULT_MODEL
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens in response
            response_format: Optional response format (e.g. {"type": "json_object"})

        Returns:
            dict with keys: content (str), model (str), usage (dict), finish_reason (str)
        """
        client = self._get_client()
        model = model or self.default_model

        kwargs = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }

        if response_format is not None:
            kwargs['response_format'] = response_format

        logger.debug(
            "LLM request: model=%s, messages=%d, temp=%s, max_tokens=%d",
            model, len(messages), temperature, max_tokens
        )

        start_time = time.time()
        response = client.chat.completions.create(**kwargs)
        elapsed = time.time() - start_time

        content = response.choices[0].message.content
        finish_reason = response.choices[0].finish_reason

        logger.debug(
            "LLM response: model=%s, finish_reason=%s, elapsed=%.2fs, "
            "prompt_tokens=%d, completion_tokens=%d",
            response.model,
            finish_reason,
            elapsed,
            response.usage.prompt_tokens if response.usage else 0,
            response.usage.completion_tokens if response.usage else 0,
        )

        return {
            'content': content,
            'model': response.model,
            'finish_reason': finish_reason,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                'total_tokens': response.usage.total_tokens if response.usage else 0,
            },
        }

    def complete_with_retry(
        self,
        messages: list,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4000,
        response_format: Optional[dict] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ) -> dict:
        """
        Send a chat completion request with exponential backoff retry.

        Args:
            messages: List of message dicts
            model: Model identifier
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            response_format: Optional response format
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay in seconds (exponential backoff)

        Returns:
            dict with response content and metadata
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                return self.complete(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as exc:
                last_exception = exc
                exc_type = type(exc).__name__

                # Check for rate limit errors
                is_rate_limit = (
                    'rate_limit' in str(exc).lower()
                    or 'rate limit' in str(exc).lower()
                    or '429' in str(exc)
                )
                is_timeout = (
                    'timeout' in str(exc).lower()
                    or 'timed out' in str(exc).lower()
                )

                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)
                    if is_rate_limit:
                        delay = max(delay, 60)  # At least 60s for rate limits
                        logger.warning(
                            "LLM rate limit hit (attempt %d/%d), retrying in %.0fs: %s",
                            attempt + 1, max_retries, delay, exc
                        )
                    elif is_timeout:
                        logger.warning(
                            "LLM timeout (attempt %d/%d), retrying in %.0fs: %s",
                            attempt + 1, max_retries, delay, exc
                        )
                    else:
                        logger.warning(
                            "LLM error %s (attempt %d/%d), retrying in %.0fs: %s",
                            exc_type, attempt + 1, max_retries, delay, exc
                        )
                    time.sleep(delay)
                else:
                    logger.error(
                        "LLM request failed after %d attempts: %s",
                        max_retries + 1, exc
                    )

        raise LLMError(f"LLM request failed after {max_retries + 1} attempts: {last_exception}") from last_exception

    def parse_json_response(self, response: dict) -> dict:
        """
        Parse JSON from LLM response content.
        Handles markdown code blocks and raw JSON.
        """
        content = response.get('content', '')

        # Strip markdown code blocks if present
        if '```json' in content:
            start = content.index('```json') + 7
            end = content.rindex('```')
            content = content[start:end].strip()
        elif '```' in content:
            start = content.index('```') + 3
            end = content.rindex('```')
            content = content[start:end].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM JSON response: %s\nContent: %s", e, content[:500])
            raise LLMError(f"Failed to parse JSON from LLM response: {e}") from e


# Singleton instance
_llm_client_instance = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = LLMClient()
    return _llm_client_instance
