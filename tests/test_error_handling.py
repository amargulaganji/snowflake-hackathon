"""Test error handling — edge cases, bad input, and boundary conditions."""
import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"


TESTS = [
    {
        "name": "Empty search query returns empty list",
        "method": "GET",
        "url": "/members?q=",
        "expect_status": 200,
        "expect_body": [],
    },
    {
        "name": "Search with no matches returns empty list",
        "method": "GET",
        "url": "/members?q=ZZZZNONEXISTENT",
        "expect_status": 200,
        "expect_body": [],
    },
    {
        "name": "Malformed member_id returns 404",
        "method": "GET",
        "url": "/members/INVALID_ID_999",
        "expect_status": 404,
    },
    {
        "name": "Valid member returns structured JSON with required keys",
        "method": "GET",
        "url": "/members/M001",
        "expect_status": 200,
        "expect_keys": ["member_id", "first_name", "last_name", "encounters", "medications", "diagnoses", "labs", "sources", "claims", "attachments"],
    },
    {
        "name": "Top-risk endpoint returns list",
        "method": "GET",
        "url": "/members/top-risk?limit=5",
        "expect_status": 200,
        "expect_is_list": True,
    },
    {
        "name": "Risk-deltas endpoint returns list",
        "method": "GET",
        "url": "/members/risk-deltas",
        "expect_status": 200,
        "expect_is_list": True,
    },
    {
        "name": "Ask endpoint rejects missing member_id",
        "method": "POST",
        "url": "/ask",
        "body": {"question": "hello"},
        "expect_status": 422,
    },
    {
        "name": "Ask endpoint rejects missing question",
        "method": "POST",
        "url": "/ask",
        "body": {"member_id": "M001"},
        "expect_status": 422,
    },
    {
        "name": "Health endpoint returns ok",
        "method": "GET",
        "url": "/health",
        "expect_status": 200,
    },
    {
        "name": "SQL injection in search is safely handled",
        "method": "GET",
        "url": "/members?q=' OR 1=1 --",
        "expect_status": 200,
        "expect_is_list": True,
    },
]


async def run_test(client: httpx.AsyncClient, test: dict) -> dict:
    try:
        if test["method"] == "GET":
            resp = await client.get(f"{BASE_URL}{test['url']}", timeout=30.0)
        else:
            resp = await client.post(f"{BASE_URL}{test['url']}", json=test.get("body", {}), timeout=30.0)

        result = {"name": test["name"], "passed": True, "status": resp.status_code}

        if "expect_status" in test and resp.status_code != test["expect_status"]:
            result["passed"] = False
            result["reason"] = f"Expected status {test['expect_status']}, got {resp.status_code}"
            return result

        if resp.status_code == 200:
            data = resp.json()
            if "expect_body" in test and data != test["expect_body"]:
                result["passed"] = False
                result["reason"] = f"Body mismatch"
            if "expect_keys" in test:
                missing = [k for k in test["expect_keys"] if k not in data]
                if missing:
                    result["passed"] = False
                    result["reason"] = f"Missing keys: {missing}"
            if test.get("expect_is_list") and not isinstance(data, list):
                result["passed"] = False
                result["reason"] = "Expected list response"

        return result
    except Exception as e:
        return {"name": test["name"], "passed": False, "reason": str(e)}


async def main():
    async with httpx.AsyncClient() as client:
        results = []
        for t in TESTS:
            print(f"Testing: {t['name']}...")
            r = await run_test(client, t)
            results.append(r)
            print(f"  {'PASS' if r['passed'] else 'FAIL'}" + (f" — {r.get('reason', '')}" if not r['passed'] else ""))

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\nError Handling: {passed}/{total} ({100*passed//total}%)")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    asyncio.run(main())
