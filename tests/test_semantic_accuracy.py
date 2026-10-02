"""Test semantic accuracy — 10+ NL questions against the Cortex Agent."""
import asyncio
import httpx
import json
import sys

BASE_URL = "http://localhost:8000"

TESTS = [
    {"q": "How many active medications does member M001 have?", "expect_contains": ["6", "active"]},
    {"q": "What is Eleanor Vance's plan type?", "expect_contains": ["Medicare"]},
    {"q": "List the diagnoses for member M010", "expect_contains": ["CKD", "diabetes", "hypertension"]},
    {"q": "What is the latest INR result for member M001?", "expect_contains": ["INR", "2.5"]},
    {"q": "Does member M001 have any abnormal lab results?", "expect_contains": ["abnormal", "creatinine"]},
    {"q": "What drugs is member M010 currently taking?", "expect_contains": ["Warfarin", "Metformin"]},
    {"q": "Has member M001 had any ER visits?", "expect_contains": ["ER", "fall"]},
    {"q": "What is Frank Delgado's age?", "expect_contains": ["87"]},
    {"q": "Check drug interactions for member M001", "expect_contains": ["interaction", "Warfarin"]},
    {"q": "What policy compliance issues exist for member M001?", "expect_contains": ["compliance", "policy"]},
    {"q": "Summarize the clinical profile of member M010", "expect_contains": ["M010", "medication"]},
]


async def run_test(client: httpx.AsyncClient, test: dict, idx: int) -> dict:
    try:
        resp = await client.post(f"{BASE_URL}/ask", json={
            "member_id": test["q"].split("member ")[-1][:4] if "member " in test["q"] else "M001",
            "question": test["q"],
            "history": [],
        }, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()
        answer = data.get("answer", "").lower()
        passed = all(kw.lower() in answer for kw in test["expect_contains"])
        return {"idx": idx + 1, "question": test["q"], "passed": passed, "missing": [k for k in test["expect_contains"] if k.lower() not in answer]}
    except Exception as e:
        return {"idx": idx + 1, "question": test["q"], "passed": False, "missing": [str(e)]}


async def main():
    async with httpx.AsyncClient() as client:
        results = []
        for i, t in enumerate(TESTS):
            print(f"Running test {i+1}/{len(TESTS)}: {t['q'][:60]}...")
            r = await run_test(client, t, i)
            results.append(r)
            print(f"  {'PASS' if r['passed'] else 'FAIL'}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Semantic Accuracy: {passed}/{total} ({100*passed//total}%)")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    asyncio.run(main())
