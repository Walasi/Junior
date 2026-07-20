from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.memory import generate_embedding

def search_qa(db: Session, query: str, limit: int = 1):
    """Search the Q&A database (read-only) for the best answer."""
    #query_emb = generate_embedding(query)
    result = db.execute(
        text("""
            SELECT answer, embedding <-> :emb AS distance
            FROM knowledge_base
            ORDER BY distance
            LIMIT :limit
        """),
        {"emb": query_emb, "limit": limit}
    ).fetchall()
    if result:
        return result[0][0]
    return None