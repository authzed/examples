"""Verify permission setup is correct."""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_rag.grpc_helpers import create_insecure_spicedb_client
from authzed.api.v1 import CheckPermissionRequest, ObjectReference, SubjectReference


def check_permission(client, user, doc_id):
    """Check if user can view document."""
    request = CheckPermissionRequest(
        resource=ObjectReference(object_type="document", object_id=doc_id),
        permission="view",
        subject=SubjectReference(
            object=ObjectReference(object_type="user", object_id=user)
        ),
    )
    response = client.CheckPermission(request)
    return response.permissionship == 2  # HAS_PERMISSION


def main():
    """Run permission verification tests."""
    print("=" * 60)
    print("Permission Verification Tests")
    print("=" * 60)

    client = create_insecure_spicedb_client("localhost:50051", "devtoken")

    tests = [
        # Format: (description, user, doc_id, expected_access)

        # Department access tests
        ("Alice accesses engineering doc", "alice", "engineering-architecture-001", True),
        ("Alice denied sales proposal 2", "alice", "sales-proposal-002", False),  # No exception for this one
        ("Bob accesses sales doc", "bob", "sales-proposal-001", True),
        ("Bob denied engineering guide 007", "bob", "engineering-guide-007", False),  # No exception for this one
        ("HR manager accesses HR doc", "hr_manager", "hr-policy-001", True),
        ("HR manager denied engineering doc", "hr_manager", "engineering-architecture-001", False),
        ("Finance manager accesses finance doc", "finance_manager", "finance-report-001", True),
        ("Finance manager denied sales doc", "finance_manager", "sales-proposal-001", False),

        # Public document access
        ("Alice accesses public doc", "alice", "public-handbook-001", True),
        ("Bob accesses public doc", "bob", "public-handbook-001", True),
        ("HR manager accesses public doc", "hr_manager", "public-handbook-001", True),
        ("Finance manager accesses public doc", "finance_manager", "public-handbook-001", True),

        # Cross-department access
        ("Alice accesses sales guide (cross-dept)", "alice", "sales-guide-005", True),
        ("Bob accesses engineering arch (cross-dept)", "bob", "engineering-architecture-001", True),
        ("Finance manager accesses HR policy (cross-dept)", "finance_manager", "hr-policy-001", True),

        # Individual exceptions
        ("Alice accesses sales proposal (exception)", "alice", "sales-proposal-001", True),
        ("Finance manager accesses HR policy 2 (exception)", "finance_manager", "hr-policy-002", True),
        ("Bob accesses engineering guide (exception)", "bob", "engineering-guide-006", True),
    ]

    passed = 0
    failed = 0

    for description, user, doc_id, expected in tests:
        try:
            actual = check_permission(client, user, doc_id)
            status = "✅" if actual == expected else "❌"

            if actual == expected:
                passed += 1
            else:
                failed += 1

            result = "GRANTED" if actual else "DENIED"
            expected_result = "GRANTED" if expected else "DENIED"

            print(f"{status} {description}")
            print(f"   User: {user}, Doc: {doc_id}")
            print(f"   Result: {result}, Expected: {expected_result}")

        except Exception as e:
            failed += 1
            print(f"❌ {description}")
            print(f"   Error: {str(e)}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
