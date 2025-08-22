#!/usr/bin/env python3
"""
Non-interactive terminal test for multiple GET endpoints via the chatbot.

ID-based tests are optional and controlled by environment variables:
- TEST_USER_ID_OR_EMAIL
- TEST_EXECUTION_ID
- TEST_WORKFLOW_ID
- TEST_TAG_ID
- TEST_CREDENTIAL_TYPE_NAME

Run:
  python test_get_endpoints.py

Optionally set env vars, e.g. PowerShell:
  $env:TEST_WORKFLOW_ID="123"; $env:TEST_TAG_ID="456"; python test_get_endpoints.py
"""

import os
from typing import List, Tuple
from n8n_chatbot import answer_user


def run_queries(queries: List[Tuple[str, str]]) -> None:
    for label, q in queries:
        print("\n" + "=" * 80)
        print(f"TEST: {label}")
        print("-" * 80)
        print(f"Query: {q}")
        print("-" * 80)
        try:
            result = answer_user(q)
            print("Result:\n" + (result if isinstance(result, str) else str(result)))
        except Exception as e:
            print(f"ERROR: {e}")
    print("\n" + "=" * 80)
    print("All tests completed.")
    print("=" * 80)


def main() -> None:
    user_id_or_email = os.getenv("TEST_USER_ID_OR_EMAIL")
    execution_id = os.getenv("TEST_EXECUTION_ID")
    workflow_id = os.getenv("TEST_WORKFLOW_ID")
    tag_id = os.getenv("TEST_TAG_ID")
    credential_type_name = os.getenv("TEST_CREDENTIAL_TYPE_NAME")

    tests: List[Tuple[str, str]] = [
        ("Users list", "List users limit 5"),
        ("Executions list", "List executions status success limit 5"),
        ("Workflows active true", "List workflows active true limit 5"),
        ("Workflows list", "List workflows limit 5"),
        ("Tags list", "List tags limit 5"),
        ("Variables list", "List variables limit 5"),
        ("Projects list", "List projects limit 5"),
    ]

    if user_id_or_email:
        tests.append((
            "User detail",
            f"Get user {user_id_or_email} include role true",
        ))
    if execution_id:
        tests.append((
            "Execution detail",
            f"Get execution {execution_id} include data false",
        ))
    if workflow_id:
        tests.append((
            "Workflow detail",
            f"Get workflow {workflow_id}",
        ))
        tests.append((
            "Workflow tags",
            f"Get tags for workflow {workflow_id}",
        ))
    if tag_id:
        tests.append((
            "Tag detail",
            f"Get tag {tag_id}",
        ))
    if credential_type_name:
        tests.append((
            "Credential schema",
            f"Get credentials schema for {credential_type_name}",
        ))

    run_queries(tests)


if __name__ == "__main__":
    main()
