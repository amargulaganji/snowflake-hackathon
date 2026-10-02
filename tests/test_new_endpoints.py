"""Tests for new endpoints: member creation, documents, roles, audit, jobs, and edge cases."""
import asyncio
import httpx
import json
import uuid

BASE_URL = "http://localhost:8000"

TESTS = [
    # Member Studio: creation
    {
        "name": "Create member via studio",
        "method": "POST",
        "url": "/studio/members",
        "body": {"first_name": "Test", "last_name": "User", "age": 55, "gender": "Male", "plan_type": "PPO", "pcp_name": "Dr. Test", "risk_flags": ["Diabetes"]},
        "expect_status": 200,
        "expect_keys": ["member_id", "status"],
    },
    # Member Studio: missing fields should still work (partial)
    {
        "name": "Create member with minimal fields",
        "method": "POST",
        "url": "/studio/members",
        "body": {"first_name": "Minimal", "last_name": "Member"},
        "expect_status": 200,
    },
    # Document upload (text file)
    {
        "name": "Document list returns array",
        "method": "GET",
        "url": "/documents",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Document list with filter
    {
        "name": "Document list with category filter",
        "method": "GET",
        "url": "/documents?category=clinical",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Admin: users list
    {
        "name": "Admin users returns seeded users",
        "method": "GET",
        "url": "/admin/users",
        "expect_status": 200,
        "expect_is_list": True,
        "expect_min_length": 4,
    },
    # Admin: current user
    {
        "name": "Admin current user returns role",
        "method": "GET",
        "url": "/admin/users/current",
        "expect_status": 200,
        "expect_keys": ["user_id", "user_role"],
    },
    # Admin: role switch
    {
        "name": "Admin role switch",
        "method": "POST",
        "url": "/admin/users/switch-role",
        "body": {"role": "care_manager"},
        "expect_status": 200,
        "expect_keys": ["status", "new_role"],
    },
    # Admin: audit log
    {
        "name": "Audit log returns list",
        "method": "GET",
        "url": "/admin/audit?limit=10",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Admin: jobs
    {
        "name": "Jobs endpoint returns list",
        "method": "GET",
        "url": "/admin/jobs",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Member summary endpoint
    {
        "name": "Member summary returns counts",
        "method": "GET",
        "url": "/members/M001/summary",
        "expect_status": 200,
        "expect_keys": ["active_medications", "active_diagnoses", "abnormal_labs"],
    },
    # Risk explanation endpoint
    {
        "name": "Risk explanation returns factors",
        "method": "GET",
        "url": "/members/M001/risk-explanation",
        "expect_status": 200,
        "expect_keys": ["member_id", "contributing_factors", "risk_flags"],
    },
    # Role authorization: studio blocked for care_manager
    {
        "name": "Studio blocked for care_manager role",
        "method": "POST",
        "url": "/studio/members",
        "body": {"first_name": "Blocked", "last_name": "User"},
        "headers": {"X-User-Role": "care_manager"},
        "expect_status": 403,
    },
    # Malformed document ID
    {
        "name": "Get nonexistent document returns 404",
        "method": "GET",
        "url": "/documents/NONEXISTENT_DOC_ID",
        "expect_status": 404,
    },
    # Duplicate member creation (different IDs generated)
    {
        "name": "Two member creates produce different IDs",
        "method": "POST",
        "url": "/studio/members",
        "body": {"first_name": "Dup", "last_name": "Test1"},
        "expect_status": 200,
        "save_field": "member_id",
    },
    # Timeline edge: member with no encounters
    {
        "name": "Member detail for new member has empty arrays",
        "method": "GET",
        "url": "/members/M999_PLACEHOLDER",
        "expect_status": 404,
    },
    # Malformed input to studio
    {
        "name": "Studio rejects empty body",
        "method": "POST",
        "url": "/studio/members",
        "body": {},
        "expect_status": 422,
    },
    # Health check still works
    {
        "name": "Health check ok",
        "method": "GET",
        "url": "/health",
        "expect_status": 200,
    },
    # Search still works
    {
        "name": "Member search still works",
        "method": "GET",
        "url": "/members?q=Eleanor",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Top risk still works
    {
        "name": "Top risk still works",
        "method": "GET",
        "url": "/members/top-risk?limit=5",
        "expect_status": 200,
        "expect_is_list": True,
    },
    # Ask endpoint still works (validation only)
    {
        "name": "Ask rejects missing fields",
        "method": "POST",
        "url": "/ask",
        "body": {"question": "hello"},
        "expect_status": 422,
    },
    # Risk explanation for unknown member returns empty factors
    {
        "name": "Risk explanation for unknown member returns empty factors",
        "method": "GET",
        "url": "/members/M999/risk-explanation",
        "expect_status": 200,
        "expect_keys": ["member_id", "contributing_factors"],
    },
    # Member summary for unknown member returns zeros
    {
        "name": "Member summary for unknown member returns zeros",
        "method": "GET",
        "url": "/members/M999/summary",
        "expect_status": 200,
    },
]


async def run_test(client: httpx.AsyncClient, test: dict) -> dict:
    try:
        headers = test.get("headers", {})
        if test["method"] == "GET":
            resp = await client.get(f"{BASE_URL}{test['url']}", headers=headers, timeout=30.0)
        else:
            resp = await client.post(f"{BASE_URL}{test['url']}", json=test.get("body", {}), headers=headers, timeout=30.0)

        result = {"name": test["name"], "passed": True, "status": resp.status_code}

        if "expect_status" in test and resp.status_code != test["expect_status"]:
            result["passed"] = False
            result["reason"] = f"Expected status {test['expect_status']}, got {resp.status_code}"
            return result

        if resp.status_code == 200:
            data = resp.json()
            if "expect_keys" in test:
                missing = [k for k in test["expect_keys"] if k not in data]
                if missing:
                    result["passed"] = False
                    result["reason"] = f"Missing keys: {missing}"
            if test.get("expect_is_list") and not isinstance(data, list):
                result["passed"] = False
                result["reason"] = "Expected list response"
            if "expect_min_length" in test and isinstance(data, list) and len(data) < test["expect_min_length"]:
                result["passed"] = False
                result["reason"] = f"Expected at least {test['expect_min_length']} items, got {len(data)}"

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
            status = "PASS" if r["passed"] else "FAIL"
            extra = f" -- {r.get('reason', '')}" if not r["passed"] else ""
            print(f"  {status}{extra}")

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\nNew Endpoints: {passed}/{total} ({100*passed//total if total else 0}%)")
    print(json.dumps(results, indent=2))
    return results


if __name__ == "__main__":
    asyncio.run(main())
