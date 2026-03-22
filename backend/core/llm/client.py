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
    Anthropic Claude client with retry logic and error handling.
    Reads ANTHROPIC_API_KEY, ANTHROPIC_DEFAULT_MODEL, ANTHROPIC_FAST_MODEL
    from Django settings.
    """

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.default_model = settings.ANTHROPIC_DEFAULT_MODEL
        self.fast_model = settings.ANTHROPIC_FAST_MODEL
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise LLMError("anthropic package is not installed. Run: pip install anthropic")
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
            messages: List of message dicts with 'role' and 'content'.
                      A message with role='system' is extracted as the system prompt.
            model: Model identifier. Defaults to ANTHROPIC_DEFAULT_MODEL
            temperature: Sampling temperature (0-1 for Claude)
            max_tokens: Maximum tokens in response
            response_format: If {'type': 'json_object'}, instructs Claude to
                             return only valid JSON.

        Returns:
            dict with keys: content (str), model (str), usage (dict), finish_reason (str)
        """
        client = self._get_client()
        model = model or self.default_model

        # Anthropic takes system as a top-level param, not a message role
        system_parts = [m['content'] for m in messages if m['role'] == 'system']
        user_messages = [m for m in messages if m['role'] != 'system']

        system_prompt = '\n\n'.join(system_parts) if system_parts else None

        # When structured JSON output is requested, append an explicit instruction
        if response_format and response_format.get('type') == 'json_object':
            json_instruction = 'Respond with valid JSON only. Do not include markdown, code fences, or any text outside the JSON object.'
            system_prompt = f"{system_prompt}\n\n{json_instruction}" if system_prompt else json_instruction

        kwargs = {
            'model': model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': user_messages,
        }
        if system_prompt:
            kwargs['system'] = system_prompt

        logger.debug(
            "LLM request: model=%s, messages=%d, temp=%s, max_tokens=%d",
            model, len(user_messages), temperature, max_tokens
        )

        start_time = time.time()
        response = client.messages.create(**kwargs)
        elapsed = time.time() - start_time

        content = response.content[0].text
        finish_reason = response.stop_reason  # 'end_turn', 'max_tokens', 'stop_sequence'

        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.output_tokens if response.usage else 0

        logger.debug(
            "LLM response: model=%s, stop_reason=%s, elapsed=%.2fs, "
            "input_tokens=%d, output_tokens=%d",
            response.model,
            finish_reason,
            elapsed,
            input_tokens,
            output_tokens,
        )

        return {
            'content': content,
            'model': response.model,
            'finish_reason': finish_reason,
            'usage': {
                'prompt_tokens': input_tokens,
                'completion_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens,
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
        """
        import anthropic as _anthropic

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

                is_rate_limit = isinstance(exc, _anthropic.RateLimitError) or (
                    'rate_limit' in str(exc).lower()
                    or 'rate limit' in str(exc).lower()
                    or '429' in str(exc)
                )
                is_timeout = isinstance(exc, _anthropic.APITimeoutError) or (
                    'timeout' in str(exc).lower()
                    or 'timed out' in str(exc).lower()
                )

                if attempt < max_retries:
                    delay = retry_delay * (2 ** attempt)
                    if is_rate_limit:
                        delay = max(delay, 60)
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
