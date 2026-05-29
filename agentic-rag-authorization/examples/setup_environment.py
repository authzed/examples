"""Initialize Milvus and SpiceDB with sample data."""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openai
from pymilvus import MilvusClient, DataType
from authzed.api.v1 import (
    WriteSchemaRequest,
    WriteRelationshipsRequest,
    Relationship,
    RelationshipUpdate,
    ObjectReference,
    SubjectReference,
)
from agentic_rag.grpc_helpers import create_insecure_spicedb_client

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
from parse_documents import load_all_documents


def setup_spicedb():
    """Setup SpiceDB schema and relationships."""
    print("Setting up SpiceDB...")

    client = create_insecure_spicedb_client("localhost:50051", "devtoken")

    schema_path = os.path.join(os.path.dirname(__file__), "..", "data", "schema.zed")
    with open(schema_path) as f:
        schema = f.read()

    client.WriteSchema(WriteSchemaRequest(schema=schema))
    print("  ✅ Schema loaded")

    documents = load_all_documents()

    updates = [
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="engineering"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="alice")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="sales"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="bob")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="hr"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="hr_manager")
                ),
            ),
        ),
        RelationshipUpdate(
            operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
            relationship=Relationship(
                resource=ObjectReference(object_type="department", object_id="finance"),
                relation="member",
                subject=SubjectReference(
                    object=ObjectReference(object_type="user", object_id="finance_manager")
                ),
            ),
        ),
    ]

    for doc in documents:
        doc_id = doc['doc_id']
        dept = doc['department']

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
            updates.append(
                RelationshipUpdate(
                    operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                    relationship=Relationship(
                        resource=ObjectReference(object_type="document", object_id=doc_id),
                        relation="viewer",
                        subject=SubjectReference(
                            object=ObjectReference(object_type="department", object_id=dept),
                            optional_relation="member",
                        ),
                    ),
                )
            )

    cross_dept_docs = [
        ("engineering-architecture-001", "sales"),
        ("sales-guide-005", "engineering"),
        ("hr-policy-001", "finance"),
    ]

    for doc_id, additional_dept in cross_dept_docs:
        updates.append(
            RelationshipUpdate(
                operation=RelationshipUpdate.Operation.OPERATION_TOUCH,
                relationship=Relationship(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    relation="viewer",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="department", object_id=additional_dept),
                        optional_relation="member",
                    ),
                ),
            )
        )

    individual_exceptions = [
        ("alice", "sales-proposal-001"),
        ("finance_manager", "hr-policy-002"),
        ("bob", "engineering-guide-006"),
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


def setup_milvus():
    """Setup Milvus with sample documents using OpenAI semantic embeddings."""
    print("\nSetting up Milvus...")

    milvus_uri = os.getenv("MILVUS_URI", "http://localhost:19530")
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

    client = MilvusClient(uri=milvus_uri)
    oai_client = openai.OpenAI(api_key=openai_api_key)

    if client.has_collection("Documents"):
        client.drop_collection("Documents")
        print("  ✅ Dropped existing Documents collection")

    schema = client.create_schema(auto_id=False, enable_dynamic_field=False)
    schema.add_field("doc_id", DataType.VARCHAR, max_length=256, is_primary=True)
    schema.add_field("title", DataType.VARCHAR, max_length=512)
    schema.add_field("content", DataType.VARCHAR, max_length=65535)
    schema.add_field("department", DataType.VARCHAR, max_length=128)
    schema.add_field("classification", DataType.VARCHAR, max_length=128)
    schema.add_field("embedding", DataType.FLOAT_VECTOR, dim=1536)

    index_params = client.prepare_index_params()
    index_params.add_index(
        field_name="embedding",
        metric_type="COSINE",
        index_type="IVF_FLAT",
        params={"nlist": 128},
    )

    client.create_collection("Documents", schema=schema, index_params=index_params)
    print("  ✅ Documents collection created")

    documents = load_all_documents()
    print(f"  ✅ Loaded {len(documents)} documents from data/documents/")

    rows = []
    for i, doc in enumerate(documents):
        response = oai_client.embeddings.create(
            model="text-embedding-3-small",
            input=doc["content"],
        )
        rows.append({
            "doc_id": doc["doc_id"],
            "title": doc["title"],
            "content": doc["content"],
            "department": doc["department"],
            "classification": doc["classification"],
            "embedding": response.data[0].embedding,
        })
        if (i + 1) % 10 == 0:
            print(f"  Embedded {i + 1}/{len(documents)} documents...")

    client.insert("Documents", rows)
    print(f"  ✅ Inserted {len(rows)} documents with embeddings")

    dept_counts = {}
    for doc in documents:
        dept = doc['department']
        dept_counts[dept] = dept_counts.get(dept, 0) + 1

    print("  Document Distribution:")
    for dept, count in sorted(dept_counts.items()):
        print(f"    - {dept}: {count} documents")


def main():
    """Run setup."""
    print("=" * 60)
    print("Agentic RAG with Authorization - Environment Setup")
    print("=" * 60)

    setup_spicedb()
    setup_milvus()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nYou can now run: python examples/basic_example.py")


if __name__ == "__main__":
    main()
