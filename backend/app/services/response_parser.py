from __future__ import annotations

import json
import re
from typing import Any

from app.models.schemas import AskResponse, EvidenceItem

TOOL_DISPLAY_NAMES: dict[str, tuple[str, str]] = {
    "clinical_analyst": ("Structured Data Query", "structured"),
    "clinical_notes_search": ("Clinical Notes", "document"),
    "policy_docs_search": ("Policy Documents", "policy"),
    "drug_interaction_search": ("Drug Interaction Guidelines", "guideline"),
    "score_polypharmacy_risk": ("Polypharmacy Risk Score", "udf"),
    "check_policy_compliance": ("Policy Compliance Check", "udf"),
}


def _extract_text(message: dict) -> str:
    content = message.get("content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(parts)
    return str(content)


def _extract_tool_results(message: dict) -> list[dict]:
    content = message.get("content", [])
    if not isinstance(content, list):
        return []
    results: list[dict] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") in ("tool_results", "tool_result"):
            results.append(block)
    return results


def _parse_tool_content(tool_result: dict) -> dict[str, Any]:
    content = tool_result.get("content", "")
    if isinstance(content, str):
        try:
            return json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return {"raw": content}
    if isinstance(content, dict):
        return content
    return {"raw": str(content)}


def _summarize_tool_content(parsed: dict, source_type: str) -> str:
    """Extract a meaningful preview from tool result JSON."""
    if source_type == "udf":
        level = parsed.get("risk_level", "")
        reasoning = parsed.get("reasoning", "")
        if level and reasoning:
            return f"Risk: {level} — {reasoning[:200]}"
        status = parsed.get("compliance_status", "")
        if status:
            gaps = parsed.get("gaps", [])
            return f"Status: {status}" + (f" — Gaps: {', '.join(gaps[:3])}" if gaps else "")
    if "raw" in parsed and parsed["raw"]:
        raw = str(parsed["raw"])
        return raw[:300] if len(raw) > 300 else raw
    # For structured data, show key fields
    preview_parts = []
    for key in ("results", "data", "answer", "text", "content"):
        if key in parsed:
            val = str(parsed[key])
            preview_parts.append(val[:200])
            break
    if not preview_parts:
        return json.dumps(parsed, default=str)[:300]
    return preview_parts[0]


def _build_evidence(tool_results: list[dict]) -> list[EvidenceItem]:
    items: list[EvidenceItem] = []
    for tr in tool_results:
        tool_name = tr.get("tool_name", tr.get("name", "unknown"))
        parsed = _parse_tool_content(tr)

        display_name, source_type = TOOL_DISPLAY_NAMES.get(
            tool_name, (tool_name, "structured")
        )

        # Skip empty results
        content_str = _summarize_tool_content(parsed, source_type)
        if content_str in ('{"raw": ""}', '{"raw": "None"}', ""):
            continue

        items.append(
            EvidenceItem(
                source_type=source_type,
                source_name=display_name,
                content=content_str,
                relevance=None,
            )
        )
    return items


def _detect_risk(tool_results: list[dict]) -> str | None:
    for tr in tool_results:
        parsed = _parse_tool_content(tr)
        if "risk_level" in parsed:
            return str(parsed["risk_level"])
    return None


def _extract_sentences(text: str, around: int) -> str:
    """Extract full sentence(s) around a character position."""
    # Find sentence boundaries (., !, ?) before and after the position
    start = around
    while start > 0 and text[start - 1] not in ".!?\n":
        start -= 1
    end = around
    while end < len(text) and text[end] not in ".!?\n":
        end += 1
    # Include the period
    if end < len(text):
        end += 1
    sentence = text[start:end].strip()
    if not sentence:
        return text[max(0, around - 100):around + 200].strip()
    return sentence


def _detect_contradiction(text: str, tool_results: list[dict]) -> tuple[bool, str | None]:
    lower = text.lower()
    phrases = [
        "contradiction",
        "contradicts",
        "inconsistent",
        "discrepancy",
        "conflicts with",
        "does not match",
    ]
    # Skip false positives like "No contradictions detected"
    negation_phrases = [
        "no contradiction",
        "no contradictions",
        "without contradiction",
    ]
    for neg in negation_phrases:
        if neg in lower:
            return False, None

    for phrase in phrases:
        idx = lower.find(phrase)
        if idx >= 0:
            detail = _extract_sentences(text, idx)
            return True, detail
    return False, None


def _detect_insufficient(text: str) -> bool:
    lower = text.lower()
    patterns = [
        "insufficient evidence",
        "not enough information",
        "cannot determine",
        "unable to confirm",
        "i don't have enough",
        "no data available",
    ]
    return any(p in lower for p in patterns)


def parse_agent_response(raw: dict) -> AskResponse:
    messages = raw.get("messages", [])
    if not messages:
        message = raw.get("message", raw)
        messages = [message] if message else []

    full_text = ""
    all_tool_results: list[dict] = []

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        full_text += _extract_text(msg) + "\n"
        all_tool_results.extend(_extract_tool_results(msg))

    full_text = full_text.strip()
    if not full_text:
        full_text = json.dumps(raw, default=str)[:2000]

    evidence = _build_evidence(all_tool_results)
    risk_level = _detect_risk(all_tool_results)
    contradiction_detected, contradiction_details = _detect_contradiction(
        full_text, all_tool_results
    )
    insufficient = _detect_insufficient(full_text)

    return AskResponse(
        answer=full_text,
        evidence_chain=evidence,
        risk_level=risk_level,
        contradiction_detected=contradiction_detected,
        contradiction_details=contradiction_details,
        insufficient_evidence=insufficient,
    )
