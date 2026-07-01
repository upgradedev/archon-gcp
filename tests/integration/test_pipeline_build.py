"""Integration: the SequentialAgent analysis pipeline constructs offline.

Constructing an ADK `SequentialAgent` (and its `LlmAgent` sub-agents with string
model names) needs no API key — only *running* against real Gemini does. So we
can assert the pipeline's shape (course concept: multi-agent SequentialAgent)
without any credentials.
"""
import pytest

pytest.importorskip("google.adk")

from archon.pipeline import build_analysis_pipeline  # noqa: E402


def test_pipeline_is_a_sequential_agent_with_three_stages():
    from google.adk.agents import SequentialAgent

    pipeline = build_analysis_pipeline()
    assert isinstance(pipeline, SequentialAgent)
    names = [a.name for a in pipeline.sub_agents]
    assert names == ["reconciler", "validator", "narrator"]


def test_pipeline_stages_hand_off_state_via_output_key():
    pipeline = build_analysis_pipeline()
    keys = [a.output_key for a in pipeline.sub_agents]
    assert keys == ["reconciliation", "validation", "summary"]


def test_pipeline_rejects_wrong_model_count():
    with pytest.raises(ValueError):
        build_analysis_pipeline(models=["only-one-model"])
