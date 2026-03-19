from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers used as judges."""

    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a response from the LLM.

        Args:
            system_prompt: The system-level instruction for the judge.
            user_prompt: The user-level prompt containing the content to evaluate.

        Returns:
            The raw text response from the LLM.
        """
        ...
