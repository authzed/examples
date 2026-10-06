"""Initialize Elasticsearch and SpiceDB with sample data."""

import sys
import os
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_mistralai import MistralAIEmbeddings
from elasticsearch import Elasticsearch, helpers
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


def setup_elasticsearch():
    """Setup Elasticsearch with sample documents using Mistral semantic embeddings."""
    print("\nSetting up Elasticsearch...")

    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    es_api_key = os.getenv("ELASTICSEARCH_API_KEY", "")
    mistral_api_key = os.getenv("MISTRAL_API_KEY", "")

    if es_api_key:
        client = Elasticsearch(es_url, api_key=es_api_key)
    else:
        client = Elasticsearch(es_url)
    embeddings = MistralAIEmbeddings(model="mistral-embed", api_key=mistral_api_key)

    if client.indices.exists(index="documents"):
        client.indices.delete(index="documents")
        print("  ✅ Dropped existing documents index")

    mappings = {
        "properties": {
            "doc_id": {"type": "keyword"},
            "title": {"type": "text"},
            "content": {"type": "text"},
            "department": {"type": "keyword"},
            "classification": {"type": "keyword"},
            "embedding": {
                "type": "dense_vector",
                "dims": 1024,
                "index": True,
                "similarity": "cosine",
            },
        }
    }

    client.indices.create(index="documents", mappings=mappings)
    print("  ✅ documents index created")

    documents = load_all_documents()
    print(f"  ✅ Loaded {len(documents)} documents from data/documents/")

    # Embed all documents in a single batched call. embed_documents() chunks the
    # inputs internally, so this issues far fewer Mistral API requests than
    # embedding one document at a time (and is much less likely to hit rate limits).
    doc_embeddings = embeddings.embed_documents([doc["content"] for doc in documents])
    print(f"  ✅ Embedded {len(doc_embeddings)} documents")

    actions = [
        {
            "_index": "documents",
            "_id": doc["doc_id"],
            "_source": {
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "content": doc["content"],
                "department": doc["department"],
                "classification": doc["classification"],
                "embedding": embedding,
            },
        }
        for doc, embedding in zip(documents, doc_embeddings)
    ]

    helpers.bulk(client, actions)
    client.indices.refresh(index="documents")
    print(f"  ✅ Inserted {len(actions)} documents with embeddings")

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
    setup_elasticsearch()

    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nYou can now run: python examples/basic_example.py")


if __name__ == "__main__":
    main()
