"""Parse .txt document files and extract metadata."""

import os
import re


def parse_document_file(filepath):
    """Parse a .txt document file and extract metadata."""
    filename = os.path.basename(filepath)

    # Parse filename: {dept}-{category}-{num}.txt
    match = re.match(r'([a-z]+)-([a-z]+)-(\d+)\.txt', filename)
    if not match:
        raise ValueError(f"Invalid filename format: {filename}")

    dept, category, num = match.groups()
    doc_id = f"{dept}-{category}-{num}"

    # Read content
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract title from first line
    lines = content.split('\n')
    title = lines[0].replace('Title: ', '').strip() if lines else f"Document {doc_id}"

    # Extract classification
    classification = "internal"  # default
    for line in lines:
        if line.startswith('Classification:'):
            classification = line.replace('Classification:', '').strip()
            break

    return {
        "doc_id": doc_id,
        "title": title,
        "content": content,
        "department": dept,
        "classification": classification,
        "category": category,
    }


def load_all_documents(docs_dir="data/documents"):
    """Load all documents from data/documents/."""
    documents = []

    if not os.path.exists(docs_dir):
        raise ValueError(f"Documents directory not found: {docs_dir}")

    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(docs_dir, filename)
            doc = parse_document_file(filepath)
            documents.append(doc)

    return documents


if __name__ == "__main__":
    # Test the parser
    docs = load_all_documents()
    print(f"Loaded {len(docs)} documents")
    print(f"\nFirst 5 documents:")
    for doc in docs[:5]:
        print(f"  {doc['doc_id']}: {doc['title']} ({doc['classification']})")
