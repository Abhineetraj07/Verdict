import asyncio
import json
import logging

import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.config import settings
from backend.app.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider with rate limiting and retry logic."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self._api_key = api_key or settings.gemini_api_key
        self._model_name = model_name or settings.gemini_model
        genai.configure(api_key=self._api_key)
        self._model = genai.GenerativeModel(self._model_name)
        self._semaphore = asyncio.Semaphore(settings.rate_limit_rpm)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=60),
    )
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        async with self._semaphore:
            response = await self._model.generate_content_async(
                contents=[
                    {"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}
                ],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            return response.text

    async def generate_judge_score(
        self, system_prompt: str, user_prompt: str
    ) -> dict:
        """Generate a judge score, parsing the JSON response.

        Returns:
            Dict with 'score' (float) and 'reasoning' (str) keys.
        """
        raw = await self.generate(system_prompt, user_prompt)
        try:
            parsed = json.loads(raw)
            return {
                "score": float(parsed["score"]),
                "reasoning": str(parsed.get("reasoning", "")),
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning("Failed to parse judge response: %s | raw: %s", e, raw[:200])
            raise ValueError(f"Invalid judge response format: {e}") from e
