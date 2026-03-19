import logging

from backend.app.models.schemas import DatasetEntry, JudgeConfig, JudgeScore
from backend.app.providers.gemini import GeminiProvider

logger = logging.getLogger(__name__)

JUDGE_SYSTEM_PROMPT_TEMPLATE = """You are an expert LLM output evaluator. Your task is to evaluate a response on the dimension of "{dimension}".

## Rubric
{rubric}

## Instructions
- Score the response on a scale of 1 to {scale}.
- Provide a brief reasoning for your score.
- Respond ONLY with valid JSON in this exact format:
{{"score": <number>, "reasoning": "<your reasoning>"}}
"""

JUDGE_USER_PROMPT_TEMPLATE = """## Input (the question/prompt given to the LLM)
{input}

## Response to Evaluate
{output}
{expected_section}
Evaluate the response according to the rubric and provide your score and reasoning as JSON."""


def build_judge_prompts(
    judge: JudgeConfig, entry: DatasetEntry
) -> tuple[str, str]:
    """Build system and user prompts for a judge evaluation."""
    system_prompt = JUDGE_SYSTEM_PROMPT_TEMPLATE.format(
        dimension=judge.dimension,
        rubric=judge.rubric,
        scale=judge.scoring_scale,
    )

    expected_section = ""
    if entry.expected_output:
        expected_section = f"\n## Expected/Reference Output\n{entry.expected_output}\n"

    user_prompt = JUDGE_USER_PROMPT_TEMPLATE.format(
        input=entry.input,
        output=entry.output,
        expected_section=expected_section,
    )

    return system_prompt, user_prompt


async def run_judge(
    provider: GeminiProvider,
    judge: JudgeConfig,
    entry: DatasetEntry,
) -> JudgeScore:
    """Run a single judge on a single dataset entry.

    Returns:
        JudgeScore with the judge's score and reasoning.
    """
    system_prompt, user_prompt = build_judge_prompts(judge, entry)

    try:
        result = await provider.generate_judge_score(system_prompt, user_prompt)
        score = max(1, min(result["score"], judge.scoring_scale))

        return JudgeScore(
            judge_name=judge.name,
            dimension=judge.dimension,
            score=score,
            reasoning=result["reasoning"],
        )
    except Exception as e:
        logger.error("Judge %s failed on entry: %s", judge.name, e)
        return JudgeScore(
            judge_name=judge.name,
            dimension=judge.dimension,
            score=0.0,
            reasoning=f"Judge evaluation failed: {e}",
        )
