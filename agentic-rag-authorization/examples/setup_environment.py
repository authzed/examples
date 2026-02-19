"""Initialize Weaviate and SpiceDB with sample data."""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path so we can import from agentic_rag
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import weaviate
from authzed.api.v1 import (
    WriteSchemaRequest,
    WriteRelationshipsRequest,
    Relationship,
    RelationshipUpdate,
    ObjectReference,
    SubjectReference,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client
import json

# Add scripts directory to path for document parser
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from parse_documents import load_all_documents


def setup_spicedb():
    """Setup SpiceDB schema and relationships."""
    print("Setting up SpiceDB...")

    client = create_insecure_spicedb_client("localhost:50051", "devtoken")

    # Load schema
    schema_path = os.path.join(os.path.dirname(__file__), "..", "data", "schema.zed")
    with open(schema_path) as f:
        schema = f.read()

    client.WriteSchema(WriteSchemaRequest(schema=schema))
    print("  ✅ Schema loaded")

    # Load documents to get all doc_ids
    documents = load_all_documents()

    # Create user-department relationships
    updates = [
        # Alice is in engineering department
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(
                    object_type="department", object_id="engineering"
                ),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="alice")
                ),
            ),
        ),
        # Bob is in sales department
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(
                    object_type="department", object_id="sales"
                ),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="bob")
                ),
            ),
        ),
        # HR manager is in HR department
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(
                    object_type="department", object_id="hr"
                ),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="hr_manager")
                ),
            ),
        ),
        # Finance manager is in finance department
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(
                    object_type="department", object_id="finance"
                ),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="finance_manager")
                ),
            ),
        ),
    ]

    # Create department-based document permissions
    for doc in documents:
        doc_id = doc['doc_id']
        dept = doc['department']

        # Public documents: accessible to all users
        if dept == "public":
            for user in ["alice", "bob", "hr_manager", "finance_manager"]:
                updates.append(
                    RelationshipUpdate(
                        operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                        relationship=Relationship(
                            resource=ObjectReference(object_type="document", object_id=doc_id),
                            relation="viewer",
                            subject=SubjectReference(
                                object=ObjectReference(object_type="user", object_id=user)
                            ),
                        ),
                    )
                )
        else:
            # Department documents: accessible to department members
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="document", object_id=doc_id),
                        relation="viewer",
                        subject=SubjectReference(
                            object=ObjectReference(
                                object_type="department",
                                object_id=dept,
                            ),
                            optional_relation="member",
                        ),
                    ),
                )
            )

    # Cross-department documents
    cross_dept_docs = [
        ("engineering-architecture-001", "sales"),  # Tech sales need architecture docs
        ("sales-guide-005", "engineering"),  # Engineering needs to understand product positioning
        ("hr-policy-001", "finance"),  # Finance needs HR policies for budget planning
    ]

    for doc_id, additional_dept in cross_dept_docs:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(
                            object_type="department",
                            object_id=additional_dept,
                        ),
                        optional_relation="member",
                    ),
                ),
            )
        )

    # Individual user exceptions
    individual_exceptions = [
        ("alice", "sales-proposal-001"),  # Alice needs to see a technical sales proposal
        ("finance_manager", "hr-policy-002"),  # Finance manager needs HR compensation policy
        ("bob", "engineering-guide-006"),  # Bob needs technical documentation for sales
    ]

    for user, doc_id in individual_exceptions:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="user", object_id=user)
                    ),
                ),
            )
        )

    client.WriteRelationships(WriteRelationshipsRequest(updates=updates))
    print(f"  ✅ {len(updates)} relationships configured")
    print("  Users and Departments:")
    print("    - alice: engineering department")
    print("    - bob: sales department")
    print("    - hr_manager: hr department")
    print("    - finance_manager: finance department")
    print("  Permission Patterns:")
    print(f"    - Department-based: All dept members access their dept docs")
    print(f"    - Cross-department: 3 collaboration documents")
    print(f"    - Individual exceptions: 3 special access grants")
    print(f"    - Public access: 5 documents accessible to all users")


def setup_weaviate():
    """Setup Weaviate with sample documents."""
    print("\nSetting up Weaviate...")

    # Connect to Weaviate v3 (REST API)
    client = weaviate.Client("http://127.0.0.1:8080")

    try:
        # Check if class exists and delete it
        try:
            client.schema.delete_class("Documents")
            print("  ✅ Deleted existing Documents class")
        except:
            pass

        # Create schema using v3 API (no vectorizer since we're using BM25 keyword search)
        schema = {
            "class": "Documents",
            "vectorizer": "none",  # Disable vectorization for BM25 keyword search
            "properties": [
                {"name": "doc_id", "dataType": ["text"]},
                {"name": "title", "dataType": ["text"]},
                {"name": "content", "dataType": ["text"]},
                {"name": "department", "dataType": ["text"]},
                {"name": "classification", "dataType": ["text"]},
            ],
        }
        client.schema.create_class(schema)
        print("  ✅ Documents class created")

        # Load documents from .txt files
        documents = load_all_documents()
        print(f"  ✅ Loaded {len(documents)} documents from data/documents/")

        # Insert documents using v3 API
        with client.batch as batch:
            for doc in documents:
                batch.add_data_object(
                    data_object=doc,
                    class_name="Documents",
                )

        print(f"  ✅ Inserted {len(documents)} documents")
        print("  Document Distribution:")

        # Count by department
        dept_counts = {}
        for doc in documents:
            dept = doc['department']
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        for dept, count in sorted(dept_counts.items()):
            print(f"    - {dept}: {count} documents")

    finally:
        pass  # v3 client doesn't need explicit close


def main():
    """Run setup."""
    print("=" * 60)
    print("Agentic RAG with Authorization - Environment Setup")
    print("=" * 60)

    setup_spicedb()
    setup_weaviate()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nYou can now run: python examples/basic_example.py")


if __name__ == "__main__":
    main()
