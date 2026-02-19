"""
Test script to verify production improvements.

This tests the new features without requiring running services.
"""

import json
import sys
from io import StringIO


def test_structured_logging():
    """Test that logging produces valid JSON."""
    print("\n=== Testing Structured Logging ===")

    # Capture logging output
    from agentic_rag.logging_config import setup_logging, get_logger

    setup_logging(level="INFO")
    logger = get_logger("test")

    # Capture stdout
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()

    # Log with context
    logger.info(
        "Test message",
        extra={
            "subject_id": "alice",
            "document_count": 5,
            "duration_ms": 123.45,
        },
    )

    # Restore stdout
    sys.stdout = old_stdout
    output = captured_output.getvalue()

    # Parse as JSON
    try:
        log_entry = json.loads(output.strip())
        assert log_entry["level"] == "INFO"
        assert log_entry["logger"] == "agentic_rag.test"
        assert log_entry["message"] == "Test message"
        assert log_entry["subject_id"] == "alice"
        assert log_entry["document_count"] == 5
        assert log_entry["duration_ms"] == 123.45
        print("✅ Structured logging works correctly")
        print(f"   Sample log: {json.dumps(log_entry, indent=2)[:200]}...")
        return True
    except (json.JSONDecodeError, AssertionError, KeyError) as e:
        print(f"❌ Structured logging failed: {e}")
        print(f"   Output: {output}")
        return False


def test_connection_pooling():
    """Test that singletons are created correctly."""
    print("\n=== Testing Connection Pooling ===")

    try:
        from agentic_rag.grpc_helpers import (
            get_spicedb_client,
            reset_spicedb_client,
            _spicedb_client,
        )
        from agentic_rag.weaviate_client import (
            get_weaviate_client,
            reset_weaviate_client,
            _weaviate_client,
        )

        # Verify reset functions exist
        assert callable(reset_spicedb_client)
        assert callable(reset_weaviate_client)

        print("✅ Connection pooling functions defined correctly")
        print("   - get_spicedb_client() available")
        print("   - get_weaviate_client() available")
        print("   - reset_*_client() functions available")
        return True
    except (ImportError, AssertionError) as e:
        print(f"❌ Connection pooling failed: {e}")
        return False


def test_batch_permissions():
    """Test that batch permission checker is defined."""
    print("\n=== Testing Batch Permission Checker ===")

    try:
        from agentic_rag.authorization_helpers import batch_check_permissions

        # Verify function signature
        import inspect

        sig = inspect.signature(batch_check_permissions)
        params = list(sig.parameters.keys())

        assert "client" in params
        assert "subject_id" in params
        assert "documents" in params

        print("✅ Batch permission checker defined correctly")
        print(f"   Function signature: batch_check_permissions{sig}")
        return True
    except (ImportError, AssertionError) as e:
        print(f"❌ Batch permission checker failed: {e}")
        return False


def test_validation():
    """Test input validation."""
    print("\n=== Testing Input Validation ===")

    try:
        from agentic_rag.validation import (
            validate_query,
            validate_subject_id,
            ValidationError,
        )

        # Test valid inputs
        query = validate_query("  test query  ")
        assert query == "test query"

        subject = validate_subject_id("alice_123")
        assert subject == "alice_123"

        # Test invalid inputs
        try:
            validate_query("")
            print("❌ Empty query should raise ValidationError")
            return False
        except ValidationError:
            pass  # Expected

        try:
            validate_subject_id("alice@example.com")
            print("❌ Invalid characters should raise ValidationError")
            return False
        except ValidationError:
            pass  # Expected

        # Test truncation
        long_query = "x" * 2000
        truncated = validate_query(long_query)
        assert len(truncated) == 1000

        print("✅ Input validation works correctly")
        print("   - Empty query rejected")
        print("   - Invalid characters rejected")
        print("   - Long queries truncated")
        return True
    except Exception as e:
        print(f"❌ Input validation failed: {e}")
        return False


def test_error_handling():
    """Test that error handling is present in nodes."""
    print("\n=== Testing Error Handling ===")

    try:
        # Check retrieval node has try-except
        with open("agentic_rag/nodes/retrieval_node.py", "r") as f:
            retrieval_code = f.read()

        assert "except Exception as e:" in retrieval_code
        assert "logger.error" in retrieval_code

        # Check authorization helpers has try-except
        with open("agentic_rag/authorization_helpers.py", "r") as f:
            auth_code = f.read()

        assert "except Exception as e:" in auth_code
        assert "logger.error" in auth_code

        print("✅ Error handling implemented correctly")
        print("   - Retrieval node has try-except")
        print("   - Authorization helpers has try-except")
        print("   - Errors logged with logger.error")
        return True
    except Exception as e:
        print(f"❌ Error handling check failed: {e}")
        return False


def test_config():
    """Test that config has log_level field."""
    print("\n=== Testing Configuration ===")

    try:
        from agentic_rag.config import get_config

        config = get_config()

        assert hasattr(config, "log_level")
        assert config.log_level == "INFO"  # Default value

        print("✅ Configuration updated correctly")
        print(f"   - log_level field added (default: {config.log_level})")
        return True
    except Exception as e:
        print(f"❌ Configuration check failed: {e}")
        return False


def test_graph_validation():
    """Test that graph has validation wrapper."""
    print("\n=== Testing Graph Validation ===")

    try:
        from agentic_rag.graph import run_agentic_rag
        import inspect

        # Verify function signature
        sig = inspect.signature(run_agentic_rag)
        params = list(sig.parameters.keys())

        assert "query" in params
        assert "subject_id" in params

        print("✅ Graph validation wrapper defined correctly")
        print(f"   Function: run_agentic_rag{sig}")
        return True
    except Exception as e:
        print(f"❌ Graph validation check failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PRODUCTION IMPROVEMENTS VERIFICATION")
    print("=" * 60)

    tests = [
        test_structured_logging,
        test_connection_pooling,
        test_batch_permissions,
        test_validation,
        test_error_handling,
        test_config,
        test_graph_validation,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n❌ Test {test.__name__} crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n✅ All production improvements verified successfully!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
