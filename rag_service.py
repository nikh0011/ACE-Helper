from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

KNOWLEDGE_FILE = Path("knowledge/company_policies.txt")

embedding_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(
    path="knowledge/chroma_db"
)

collection = client.get_or_create_collection(
    name="company_policies"
)


def load_knowledge():

    text = KNOWLEDGE_FILE.read_text(
        encoding="utf-8"
    )

    sections = [
        section.strip()
        for section in text.split("\n\n")
        if section.strip()
    ]

    documents = []
    ids = []

    for index, section in enumerate(sections):
        documents.append(section)
        ids.append(f"policy_{index}")

    embeddings = embedding_model.encode(
        documents
    ).tolist()

    collection.upsert(
        documents=documents,
        embeddings=embeddings,
        ids=ids
    )


def search_knowledge(query, top_k=2):

    query_embedding = embedding_model.encode(
        [query]
    ).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k
    )

    return results["documents"][0]


load_knowledge()
