"""Tests for the realistic document dataset in data/documents.

(Moved from the repo-root ``test_dataset_integration.py`` and converted to
idiomatic pytest: a shared ``docs`` fixture replaces the hand-threaded
function arguments and ``main()`` runner.)
"""

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from parse_documents import load_all_documents  # noqa: E402


@pytest.fixture(scope="module")
def docs():
    return load_all_documents(str(REPO_ROOT / "data" / "documents"))


def test_loads_all_documents_with_required_fields(docs):
    assert len(docs) == 50
    for doc in docs:
        for field in ("doc_id", "title", "content", "department", "classification"):
            assert field in doc, f"Missing {field} in {doc.get('doc_id', doc)}"


def test_department_distribution(docs):
    counts = {}
    for doc in docs:
        counts[doc["department"]] = counts.get(doc["department"], 0) + 1
    assert counts == {
        "engineering": 15,
        "sales": 10,
        "hr": 10,
        "finance": 10,
        "public": 5,
    }


def test_public_documents_classified_public(docs):
    public = [d for d in docs if d["department"] == "public"]
    assert len(public) == 5
    assert all(d["classification"] == "public" for d in public)


@pytest.mark.parametrize(
    "doc_id",
    ["engineering-architecture-001", "sales-guide-005", "hr-policy-001"],
)
def test_cross_department_documents_exist(docs, doc_id):
    assert any(d["doc_id"] == doc_id for d in docs)


@pytest.mark.parametrize(
    "doc_id",
    ["sales-proposal-001", "hr-policy-002", "engineering-guide-006"],
)
def test_individual_exception_documents_exist(docs, doc_id):
    assert any(d["doc_id"] == doc_id for d in docs)


def test_doc_id_naming_convention(docs):
    pattern = re.compile(r"^[a-z]+-[a-z]+-\d{3}$")
    for doc in docs:
        assert pattern.match(doc["doc_id"]), f"Invalid doc_id: {doc['doc_id']}"
