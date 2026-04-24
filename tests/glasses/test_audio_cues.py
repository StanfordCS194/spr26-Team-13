from src.contracts.common import TriggerType
from src.glasses.audio.audio_cues import (
    build_next_set_prompt,
    choose_audio_cue,
    choose_motivational_cue,
    get_audio_cues,
    normalize_exercise_name,
)


# --- normalize_exercise_name ---

def test_normalize_canonical_id():
    assert normalize_exercise_name("bench_press") == "bench_press"


def test_normalize_alias_bench():
    assert normalize_exercise_name("bench") == "bench_press"
    assert normalize_exercise_name("Bench Press") == "bench_press"
    assert normalize_exercise_name("barbell bench press") == "bench_press"


def test_normalize_alias_squat():
    assert normalize_exercise_name("squat") == "back_squat"
    assert normalize_exercise_name("Back Squat") == "back_squat"


def test_normalize_alias_ohp():
    assert normalize_exercise_name("OHP") == "overhead_press"
    assert normalize_exercise_name("ohp") == "overhead_press"


def test_normalize_unknown_returns_none():
    assert normalize_exercise_name("leg press") is None
    assert normalize_exercise_name("") is None


# --- get_audio_cues ---

def test_get_setup_cues_bench_press():
    cues = get_audio_cues("bench_press", TriggerType.EXERCISE_START)
    assert len(cues) > 0
    assert all(isinstance(c, str) for c in cues)


def test_get_setup_cues_via_alias():
    cues = get_audio_cues("bench", TriggerType.EXERCISE_START)
    assert cues == get_audio_cues("bench_press", TriggerType.EXERCISE_START)


def test_get_cues_unknown_exercise_returns_empty():
    assert get_audio_cues("leg press", TriggerType.EXERCISE_START) == []


def test_get_cues_unknown_phase_returns_empty():
    # DURING_REP is a valid TriggerType but may not be defined for all exercises;
    # more importantly, passing a phase with no entries should return [] not raise.
    assert isinstance(get_audio_cues("bench_press", TriggerType.DURING_REP), list)


def test_get_cues_returns_copy():
    # Mutating the returned list should not affect the library.
    cues = get_audio_cues("deadlift", TriggerType.EXERCISE_START)
    original_len = len(cues)
    cues.clear()
    assert len(get_audio_cues("deadlift", TriggerType.EXERCISE_START)) == original_len


# --- choose_audio_cue ---

def test_choose_audio_cue_returns_string():
    result = choose_audio_cue("back_squat", TriggerType.EXERCISE_START)
    assert isinstance(result, str)
    assert len(result) > 0


def test_choose_audio_cue_unknown_returns_none():
    assert choose_audio_cue("leg press", TriggerType.EXERCISE_START) is None


def test_choose_audio_cue_deterministic_with_seed():
    a = choose_audio_cue("deadlift", TriggerType.EXERCISE_START, seed=42)
    b = choose_audio_cue("deadlift", TriggerType.EXERCISE_START, seed=42)
    assert a == b


def test_choose_audio_cue_seed_in_valid_pool():
    cues = get_audio_cues("deadlift", TriggerType.EXERCISE_START)
    result = choose_audio_cue("deadlift", TriggerType.EXERCISE_START, seed=7)
    assert result in cues


# --- build_next_set_prompt ---

def test_next_set_prompt_includes_reps():
    prompt = build_next_set_prompt("bench_press", set_number=2, target_reps=5)
    assert "5" in prompt
    assert "2" in prompt


def test_next_set_prompt_includes_load():
    prompt = build_next_set_prompt("back_squat", set_number=1, target_reps=3, target_load=225.0)
    assert "225" in prompt
    assert "lb" in prompt


def test_next_set_prompt_custom_load_unit():
    prompt = build_next_set_prompt("deadlift", set_number=1, target_reps=5, target_load=100.0, load_unit="kg")
    assert "kg" in prompt


def test_next_set_prompt_no_load():
    prompt = build_next_set_prompt("overhead_press", set_number=3, target_reps=8)
    assert "lb" not in prompt
    assert "8" in prompt


def test_next_set_prompt_returns_string():
    result = build_next_set_prompt("barbell_row", set_number=1, target_reps=10)
    assert isinstance(result, str)
    assert len(result) > 0


# --- choose_motivational_cue ---

def test_motivational_cue_returns_nonempty_string():
    cue = choose_motivational_cue()
    assert isinstance(cue, str)
    assert len(cue) > 0


def test_motivational_cue_deterministic_with_seed():
    a = choose_motivational_cue(seed=99)
    b = choose_motivational_cue(seed=99)
    assert a == b
