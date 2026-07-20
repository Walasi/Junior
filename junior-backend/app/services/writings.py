from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.memory import generate_embedding

def search_writings(db: Session, query: str, limit: int = 2):
    """Search personal writings in the main database."""
    #query_emb = generate_embedding(query)
    result = db.execute(
        text("""
            SELECT content, embedding <-> :emb AS distance
            FROM personal_writings
            ORDER BY distance
            LIMIT :limit
        """),
        {"emb": query_emb, "limit": limit}
    ).fetchall()
    return [row[0] for row in result]