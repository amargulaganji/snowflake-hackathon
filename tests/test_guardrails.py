"""Test guardrails — insufficient evidence and contradiction detection."""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

INSUFFICIENT_CASES = [
    {"member_id": "M999", "question": "What medications is this member taking?", "label": "Nonexistent member"},
    {"member_id": "M001", "question": "What was the member's blood glucose reading from their visit on 2020-01-01?", "label": "Data not in system"},
    {"member_id": "M001", "question": "What genetic test results does this member have?", "label": "Data type not in model"},
]

CONTRADICTION_CASES = [
    {"member_id": "M010", "question": "Is there any contradiction between the structured medication records and clinical notes for member M010 regarding Digoxin?", "label": "Digoxin contradiction (M010)"},
]


async def test_insufficient(client: httpx.AsyncClient, case: dict) -> dict:
    try:
        resp = await client.post(f"{BASE_URL}/ask", json={
            "member_id": case["member_id"],
            "question": case["question"],
            "history": [],
        }, timeout=120.0)
        data = resp.json()
        answer_lower = data.get("answer", "").lower()
        has_flag = data.get("insufficient_evidence", False)
        has_phrases = any(p in answer_lower for p in ["insufficient", "no data", "cannot determine", "not available", "no records", "not found"])
        return {"label": case["label"], "passed": has_flag or has_phrases, "insufficient_evidence_field": has_flag, "phrases_found": has_phrases}
    except Exception as e:
        return {"label": case["label"], "passed": False, "error": str(e)}


async def test_contradiction(client: httpx.AsyncClient, case: dict) -> dict:
    try:
        resp = await client.post(f"{BASE_URL}/ask", json={
            "member_id": case["member_id"],
            "question": case["question"],
            "history": [],
        }, timeout=120.0)
        data = resp.json()
        detected = data.get("contradiction_detected", False)
        answer_lower = data.get("answer", "").lower()
        has_phrases = any(p in answer_lower for p in ["contradiction", "discrepancy", "inconsistent", "conflicts"])
        return {"label": case["label"], "passed": detected or has_phrases, "contradiction_detected_field": detected, "phrases_found": has_phrases}
    except Exception as e:
        return {"label": case["label"], "passed": False, "error": str(e)}


async def main():
    async with httpx.AsyncClient() as client:
        print("=== Insufficient Evidence Tests ===")
        insuff_results = []
        for c in INSUFFICIENT_CASES:
            print(f"Testing: {c['label']}...")
            r = await test_insufficient(client, c)
            insuff_results.append(r)
            print(f"  {'PASS' if r['passed'] else 'FAIL'}")

        print("\n=== Contradiction Detection Tests ===")
        contra_results = []
        for c in CONTRADICTION_CASES:
            print(f"Testing: {c['label']}...")
            r = await test_contradiction(client, c)
            contra_results.append(r)
            print(f"  {'PASS' if r['passed'] else 'FAIL'}")

    all_results = insuff_results + contra_results
    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)
    print(f"\nGuardrails: {passed}/{total} ({100*passed//total}%)")
    print(json.dumps(all_results, indent=2))
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
