import pytest

from backend.app.engine.judges import build_judge_prompts
from backend.app.models.schemas import DatasetEntry, JudgeConfig


class TestBuildJudgePrompts:
    def test_basic_prompts(self):
        judge = JudgeConfig(
            name="acc", dimension="accuracy", rubric="Score 1-5", scoring_scale=5
        )
        entry = DatasetEntry(input="What is 2+2?", output="4")

        system, user = build_judge_prompts(judge, entry)

        assert "accuracy" in system
        assert "Score 1-5" in system
        assert "1 to 5" in system
        assert "What is 2+2?" in user
        assert "4" in user
        assert "Expected" not in user  # no expected_output

    def test_with_expected_output(self):
        judge = JudgeConfig(name="j", dimension="d", rubric="r")
        entry = DatasetEntry(
            input="q", output="a", expected_output="reference answer"
        )

        system, user = build_judge_prompts(judge, entry)

        assert "Expected/Reference Output" in user
        assert "reference answer" in user

    def test_json_format_instruction(self):
        judge = JudgeConfig(name="j", dimension="d", rubric="r")
        entry = DatasetEntry(input="q", output="a")

        system, _ = build_judge_prompts(judge, entry)

        assert '"score"' in system
        assert '"reasoning"' in system
        assert "JSON" in system
