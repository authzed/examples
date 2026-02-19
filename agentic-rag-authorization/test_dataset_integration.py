"""Integration test for the realistic document dataset implementation."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from parse_documents import load_all_documents


def test_document_loading():
    """Test that documents can be loaded correctly."""
    print("Testing document loading...")

    docs = load_all_documents()

    # Test count
    assert len(docs) == 50, f"Expected 50 documents, got {len(docs)}"
    print(f"  ✅ Loaded {len(docs)} documents")

    # Test required fields
    for doc in docs:
        assert 'doc_id' in doc, f"Missing doc_id in {doc}"
        assert 'title' in doc, f"Missing title in {doc}"
        assert 'content' in doc, f"Missing content in {doc}"
        assert 'department' in doc, f"Missing department in {doc}"
        assert 'classification' in doc, f"Missing classification in {doc}"

    print("  ✅ All documents have required fields")

    return docs


def test_department_distribution(docs):
    """Test that document distribution matches expectations."""
    print("\nTesting department distribution...")

    dept_counts = {}
    for doc in docs:
        dept = doc['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    expected = {
        'engineering': 15,
        'sales': 10,
        'hr': 10,
        'finance': 10,
        'public': 5,
    }

    for dept, expected_count in expected.items():
        actual_count = dept_counts.get(dept, 0)
        assert actual_count == expected_count, \
            f"{dept}: expected {expected_count}, got {actual_count}"
        print(f"  ✅ {dept}: {actual_count} documents")


def test_document_structure(docs):
    """Test document content structure."""
    print("\nTesting document structure...")

    # Check engineering document
    eng_docs = [d for d in docs if d['department'] == 'engineering']
    assert len(eng_docs) > 0, "No engineering documents found"

    sample_eng = eng_docs[0]
    assert 'Architecture' in sample_eng['title'] or 'Guide' in sample_eng['title'] \
        or 'Memo' in sample_eng['title'] or 'Specification' in sample_eng['title'], \
        f"Unexpected title format: {sample_eng['title']}"
    print(f"  ✅ Engineering doc sample: {sample_eng['title']}")

    # Check sales document
    sales_docs = [d for d in docs if d['department'] == 'sales']
    assert len(sales_docs) > 0, "No sales documents found"

    sample_sales = sales_docs[0]
    print(f"  ✅ Sales doc sample: {sample_sales['title']}")

    # Check public document
    public_docs = [d for d in docs if d['department'] == 'public']
    assert len(public_docs) == 5, f"Expected 5 public docs, got {len(public_docs)}"

    for pub_doc in public_docs:
        assert pub_doc['classification'] == 'public', \
            f"Public doc has wrong classification: {pub_doc['classification']}"

    print(f"  ✅ All {len(public_docs)} public documents have 'public' classification")


def test_cross_department_docs(docs):
    """Test that cross-department documents exist."""
    print("\nTesting cross-department documents...")

    # These are the cross-department docs we configured
    cross_dept_ids = [
        'engineering-architecture-001',
        'sales-guide-005',
        'hr-policy-001',
    ]

    for doc_id in cross_dept_ids:
        found = any(d['doc_id'] == doc_id for d in docs)
        assert found, f"Cross-department document not found: {doc_id}"
        print(f"  ✅ Found cross-dept doc: {doc_id}")


def test_individual_exception_docs(docs):
    """Test that individual exception documents exist."""
    print("\nTesting individual exception documents...")

    # These are the individual exception docs we configured
    exception_ids = [
        'sales-proposal-001',
        'hr-policy-002',
        'engineering-guide-006',
    ]

    for doc_id in exception_ids:
        found = any(d['doc_id'] == doc_id for d in docs)
        assert found, f"Individual exception document not found: {doc_id}"
        print(f"  ✅ Found exception doc: {doc_id}")


def test_doc_id_format(docs):
    """Test that all doc_ids follow the naming convention."""
    print("\nTesting doc_id format...")

    import re
    pattern = re.compile(r'^[a-z]+-[a-z]+-\d{3}$')

    for doc in docs:
        doc_id = doc['doc_id']
        assert pattern.match(doc_id), \
            f"Invalid doc_id format: {doc_id} (expected: dept-category-###)"

    print(f"  ✅ All {len(docs)} doc_ids follow naming convention")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Dataset Integration Tests")
    print("=" * 60)

    try:
        docs = test_document_loading()
        test_department_distribution(docs)
        test_document_structure(docs)
        test_cross_department_docs(docs)
        test_individual_exception_docs(docs)
        test_doc_id_format(docs)

        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        print("=" * 60)
        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
