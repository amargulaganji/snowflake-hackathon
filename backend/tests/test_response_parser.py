"""Tests for the Cortex Agent response parser."""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch settings before importing any app module so config.py doesn't fail
os.environ.setdefault("SNOWFLAKE_ACCOUNT_URL", "https://test.snowflakecomputing.com")
os.environ.setdefault("SNOWFLAKE_PAT", "test-token")

from app.services.response_parser import (
    _extract_text,
    _extract_tool_results,
    _parse_tool_content,
    _build_evidence,
    _detect_risk,
    _detect_contradiction,
    _detect_insufficient,
    parse_agent_response,
)
from app.models.schemas import AskResponse, EvidenceItem


def test_extract_text_string_content():
    msg = {"content": "Hello world"}
    assert _extract_text(msg) == "Hello world"


def test_extract_text_list_content():
    msg = {"content": [{"type": "text", "text": "Part 1"}, {"type": "text", "text": "Part 2"}]}
    assert _extract_text(msg) == "Part 1\nPart 2"


def test_extract_text_empty():
    assert _extract_text({}) == ""
    assert _extract_text({"content": ""}) == ""


def test_extract_tool_results():
    msg = {
        "content": [
            {"type": "text", "text": "some text"},
            {"type": "tool_result", "tool_name": "foo", "content": "bar"},
            {"type": "tool_results", "tool_name": "baz", "content": "qux"},
        ]
    }
    results = _extract_tool_results(msg)
    assert len(results) == 2


def test_extract_tool_results_non_list():
    msg = {"content": "just a string"}
    assert _extract_tool_results(msg) == []


def test_parse_tool_content_json():
    tr = {"content": '{"risk_level": "high"}'}
    parsed = _parse_tool_content(tr)
    assert parsed == {"risk_level": "high"}


def test_parse_tool_content_dict():
    tr = {"content": {"key": "val"}}
    parsed = _parse_tool_content(tr)
    assert parsed == {"key": "val"}


def test_parse_tool_content_invalid_json():
    tr = {"content": "not json"}
    parsed = _parse_tool_content(tr)
    assert parsed == {"raw": "not json"}


def test_build_evidence_search_tool():
    tool_results = [
        {"tool_name": "clinical_notes_search", "content": '{"data": "result"}'},
    ]
    evidence = _build_evidence(tool_results)
    assert len(evidence) == 1
    assert evidence[0].source_type == "document"
    assert evidence[0].source_name == "clinical_notes_search"


def test_build_evidence_policy_tool():
    tool_results = [
        {"tool_name": "check_policy_compliance", "content": '{"compliant": true}'},
    ]
    evidence = _build_evidence(tool_results)
    assert evidence[0].source_type == "policy"


def test_build_evidence_structured_tool():
    tool_results = [
        {"tool_name": "clinical_analyst", "content": '{"rows": []}'},
    ]
    evidence = _build_evidence(tool_results)
    assert evidence[0].source_type == "structured"


def test_detect_risk_present():
    tool_results = [{"content": '{"risk_level": "high"}'}]
    assert _detect_risk(tool_results) == "high"


def test_detect_risk_absent():
    tool_results = [{"content": '{"data": "no risk"}'}]
    assert _detect_risk(tool_results) is None


def test_detect_risk_empty():
    assert _detect_risk([]) is None


def test_detect_contradiction_found():
    text = "The structured data shows active, but the clinical note contradicts this."
    detected, details = _detect_contradiction(text, [])
    assert detected is True
    assert details is not None
    assert "contradict" in details.lower()


def test_detect_contradiction_not_found():
    text = "Everything looks consistent across sources."
    detected, details = _detect_contradiction(text, [])
    assert detected is False
    assert details is None


def test_detect_contradiction_discrepancy():
    text = "There is a discrepancy between the medication list and clinical notes."
    detected, _ = _detect_contradiction(text, [])
    assert detected is True


def test_detect_insufficient_true():
    assert _detect_insufficient("I don't have enough data to answer") is True
    assert _detect_insufficient("There is insufficient evidence to determine this.") is True
    assert _detect_insufficient("Cannot determine from available data.") is True


def test_detect_insufficient_false():
    assert _detect_insufficient("Here is the complete answer.") is False
    assert _detect_insufficient("The member has 5 active medications.") is False


def test_parse_agent_response_full():
    raw = {
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Member has high polypharmacy risk."},
                    {
                        "type": "tool_result",
                        "tool_name": "score_polypharmacy_risk",
                        "content": json.dumps({"risk_level": "high", "active_medication_count": 8}),
                    },
                ],
            }
        ]
    }
    resp = parse_agent_response(raw)
    assert isinstance(resp, AskResponse)
    assert "polypharmacy" in resp.answer.lower()
    assert resp.risk_level == "high"
    assert len(resp.evidence_chain) == 1
    assert resp.contradiction_detected is False
    assert resp.insufficient_evidence is False


def test_parse_agent_response_empty():
    raw = {"messages": []}
    resp = parse_agent_response(raw)
    assert isinstance(resp, AskResponse)
    assert resp.answer != ""


def test_parse_agent_response_with_contradiction():
    raw = {
        "messages": [
            {
                "role": "assistant",
                "content": "CONTRADICTION DETECTED: structured data shows active metformin but note says discontinued.",
            }
        ]
    }
    resp = parse_agent_response(raw)
    assert resp.contradiction_detected is True
    assert resp.contradiction_details is not None


def test_parse_agent_response_insufficient():
    raw = {
        "messages": [
            {"role": "assistant", "content": "Insufficient evidence to determine the answer."}
        ]
    }
    resp = parse_agent_response(raw)
    assert resp.insufficient_evidence is True


def test_parse_agent_response_fallback_message_key():
    raw = {"message": {"role": "assistant", "content": "Fallback response"}}
    resp = parse_agent_response(raw)
    assert "Fallback response" in resp.answer
