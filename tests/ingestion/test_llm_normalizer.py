from types import SimpleNamespace

from src.contracts import (
    BlockExecutionStyle,
    ProgramExercise,
    SourceType,
    TrainingBlock,
    TrainingDay,
    TrainingProgram,
    TrainingWeek,
)
from src.ingestion.llm_normalizer import get_llm_provider, normalize_document_with_llm
from src.ingestion.models import ExtractedDocument
from src.ingestion.service import normalize_extracted_program


class FakeResponsesAPI:
    def __init__(self, program: TrainingProgram):
        self.program = program
        self.last_kwargs = None

    def parse(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(output_parsed=self.program)


class FakeChatCompletionsAPI:
    def __init__(self, program: TrainingProgram):
        self.program = program
        self.last_kwargs = None

    def parse(self, **kwargs):
        self.last_kwargs = kwargs
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(parsed=self.program))]
        )


class FakeClient:
    def __init__(self, program: TrainingProgram):
        self.responses = FakeResponsesAPI(program)
        self.beta = SimpleNamespace(chat=SimpleNamespace(completions=FakeChatCompletionsAPI(program)))


def test_normalize_document_with_llm_returns_training_program():
    parsed_program = TrainingProgram(
        program_id="temp-id",
        user_id="wrong-user",
        title="Temp Title",
        source_type=SourceType.TEXT,
        weeks=[
            TrainingWeek(
                week_number=1,
                days=[
                    TrainingDay(
                        day_id="day-1",
                        title="Lower",
                        blocks=[
                            TrainingBlock(
                                block_id="block-1",
                                title="Block 1",
                                execution_style=BlockExecutionStyle.ROUND_ROBIN,
                                exercises=[
                                    ProgramExercise(
                                        exercise_id="back_squat",
                                        display_name="Back Squat",
                                        set_count=3,
                                        rep_target="5",
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    fake_client = FakeClient(parsed_program)
    extracted = ExtractedDocument(
        text="Day 1\nBack Squat - 3x5",
        source_type=SourceType.IMAGE,
        structured_markdown="Day 1\nBack Squat - 3x5",
        structured_data={"kind": "docling"},
    )

    normalized = normalize_document_with_llm(
        extracted,
        user_id="user-1",
        title="Imported Program",
        program_id="program-1",
        client=fake_client,
        model="gemini-2.5-flash",
    )

    assert normalized.user_id == "user-1"
    assert normalized.program_id == "program-1"
    assert normalized.title == "Imported Program"
    assert normalized.source_type == SourceType.IMAGE
    assert normalized.weeks[0].days[0].blocks[0].title == "Block 1"
    assert normalized.weeks[0].days[0].exercises[0].exercise_id == "back_squat"
    assert fake_client.beta.chat.completions.last_kwargs["model"] == "gemini-2.5-flash"
    assert "Parsed structured JSON" not in fake_client.beta.chat.completions.last_kwargs["messages"][1]["content"]


def test_normalize_extracted_program_uses_llm_when_available(monkeypatch):
    extracted = ExtractedDocument(
        text="Day 1\nBack Squat - 3x5",
        source_type=SourceType.TEXT,
    )
    expected = TrainingProgram(
        program_id="program-1",
        user_id="user-1",
        title="Imported Program",
        source_type=SourceType.TEXT,
        weeks=[],
    )

    monkeypatch.setattr("src.ingestion.service.llm_normalization_available", lambda: True)
    monkeypatch.setattr("src.ingestion.service.normalize_document_with_llm", lambda *args, **kwargs: expected)

    program, mode = normalize_extracted_program(
        extracted,
        user_id="user-1",
        program_id="program-1",
        title="Imported Program",
    )

    assert mode == "gemini"
    assert program == expected


def test_get_llm_provider_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("LLM_NORMALIZER_PROVIDER", raising=False)
    assert get_llm_provider() == "gemini"


def test_get_llm_provider_accepts_groq(monkeypatch):
    monkeypatch.setenv("LLM_NORMALIZER_PROVIDER", "groq")
    assert get_llm_provider() == "groq"
