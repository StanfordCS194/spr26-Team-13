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


def test_normalize_document_with_llm_returns_training_program(monkeypatch):
    monkeypatch.setenv("LLM_NORMALIZER_PROVIDER", "gemini")
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
        structured_data={
            "texts": [
                {
                    "text": "Back Squat",
                    "prov": [
                        {
                            "page_no": 1,
                            "bbox": {"l": 10, "b": 20, "r": 90, "t": 40},
                        }
                    ],
                }
            ]
        },
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
    user_content = fake_client.beta.chat.completions.last_kwargs["messages"][1]["content"]
    assert "Positioned OCR text JSON" in user_content
    assert '"x0": 10.0' in user_content
    assert "Parsed structured JSON" not in user_content


def test_normalize_document_with_openai_attaches_source_image(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_NORMALIZER_PROVIDER", "openai")
    image_path = tmp_path / "workout.png"
    image_path.write_bytes(b"fake image bytes")
    parsed_program = TrainingProgram(
        program_id="temp-id",
        user_id="wrong-user",
        title="Temp Title",
        source_type=SourceType.IMAGE,
        weeks=[],
    )
    fake_client = FakeClient(parsed_program)
    extracted = ExtractedDocument(
        text="10 Squats\n10 Push Ups\n5 Pull Ups",
        source_type=SourceType.IMAGE,
        source_path=str(image_path),
    )

    normalized = normalize_document_with_llm(
        extracted,
        user_id="user-1",
        title="Imported Program",
        program_id="program-1",
        client=fake_client,
        model="gpt-4.1",
    )

    assert normalized.program_id == "program-1"
    content = fake_client.responses.last_kwargs["input"][0]["content"]
    assert content[0]["type"] == "input_text"
    assert content[1]["type"] == "input_image"
    assert content[1]["image_url"].startswith("data:image/png;base64,")


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
    monkeypatch.setattr("src.ingestion.service.get_llm_provider", lambda: "gemini")
    monkeypatch.setattr("src.ingestion.service.normalize_document_with_llm", lambda *args, **kwargs: expected)
    monkeypatch.setattr("src.ingestion.service.parse_program_text", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("local parser should not run")))

    program, mode = normalize_extracted_program(
        extracted,
        user_id="user-1",
        program_id="program-1",
        title="Imported Program",
    )

    assert mode == "gemini"
    assert program == expected


def test_normalize_extracted_program_preserves_successful_llm_output(monkeypatch):
    extracted = ExtractedDocument(
        text=(
            "2 days - 18 lifts - 20 sets\n"
            "WEEK 1 - DAY 1\n"
            "Day 1\n"
            "0 lifts - 0 sets\n"
            "WEEK 1 - DAY 2\n"
            "Day 2\n"
            "18 lifts - 20 sets\n"
            "Team Prep\n"
            "A BB Split Squat Overcoming Iso Duration 1 - -\n"
        ),
        source_type=SourceType.IMAGE,
    )
    parsed = TrainingProgram(
        program_id="program-1",
        user_id="user-1",
        title="Workout",
        source_type=SourceType.IMAGE,
        weeks=[
            TrainingWeek(
                week_number=1,
                days=[
                    TrainingDay(
                        day_id="week-1-day-1-day-1",
                        title="Day 1",
                    ),
                    TrainingDay(
                        day_id="week-1-day-2-day-2",
                        title="Day 2",
                        blocks=[
                            TrainingBlock(
                                block_id="team-prep",
                                title="Team Prep",
                                execution_style=BlockExecutionStyle.SEQUENTIAL,
                                exercises=[
                                    ProgramExercise(
                                        exercise_id="bb_split_squat_overcoming_iso_duration",
                                        display_name="BB Split Squat Overcoming Iso Duration",
                                        set_count=1,
                                    )
                                ],
                            )
                        ],
                    ),
                ],
            )
        ],
    )

    monkeypatch.setattr("src.ingestion.service.llm_normalization_available", lambda: True)
    monkeypatch.setattr("src.ingestion.service.get_llm_provider", lambda: "gemini")
    monkeypatch.setattr("src.ingestion.service.normalize_document_with_llm", lambda *args, **kwargs: parsed)

    program, mode = normalize_extracted_program(
        extracted,
        user_id="user-1",
        program_id="program-1",
        title="Workout",
    )

    assert mode == "gemini"
    days = program.weeks[0].days
    assert len(days) == 2
    assert days[0].title == "Day 1"
    assert days[1].title == "Day 2"
    assert days[1].blocks[0].title == "Team Prep"
    assert days[1].blocks[0].exercises[0].display_name == "BB Split Squat Overcoming Iso Duration"


def test_normalize_extracted_program_does_not_repair_llm_with_local_parse(monkeypatch):
    extracted = ExtractedDocument(
        text="Day 1\nBack Squat - 3x5 @ 185 lb\n",
        source_type=SourceType.IMAGE,
    )
    parsed = TrainingProgram(
        program_id="program-1",
        user_id="user-1",
        title="Workout",
        source_type=SourceType.IMAGE,
        weeks=[
            TrainingWeek(
                week_number=1,
                days=[
                    TrainingDay(
                        day_id="week-1-day-1-day-1",
                        title="Day 1",
                        blocks=[
                            TrainingBlock(
                                block_id="main",
                                title="Main",
                                execution_style=BlockExecutionStyle.SEQUENTIAL,
                                exercises=[
                                    ProgramExercise(
                                        exercise_id="back_squat",
                                        display_name="Back Squat",
                                        set_count=1,
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )

    monkeypatch.setattr("src.ingestion.service.llm_normalization_available", lambda: True)
    monkeypatch.setattr("src.ingestion.service.get_llm_provider", lambda: "gemini")
    monkeypatch.setattr("src.ingestion.service.normalize_document_with_llm", lambda *args, **kwargs: parsed)
    monkeypatch.setattr("src.ingestion.service.parse_program_text", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("local parser should not run")))

    program, mode = normalize_extracted_program(
        extracted,
        user_id="user-1",
        program_id="program-1",
        title="Workout",
    )

    assert mode == "gemini"
    exercises = program.weeks[0].days[0].blocks[0].exercises
    assert exercises[0].display_name == "Back Squat"
    assert exercises[0].rep_target is None
    assert exercises[0].load_target is None


def test_get_llm_provider_defaults_to_gemini(monkeypatch):
    monkeypatch.delenv("LLM_NORMALIZER_PROVIDER", raising=False)
    assert get_llm_provider() == "gemini"


def test_get_llm_provider_accepts_groq(monkeypatch):
    monkeypatch.setenv("LLM_NORMALIZER_PROVIDER", "groq")
    assert get_llm_provider() == "groq"
