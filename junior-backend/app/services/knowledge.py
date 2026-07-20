from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

_model = SentenceTransformer('all-MiniLM-L6-v2')

def generate_embedding(text: str):
    return _model.encode(text).tolist()

def search_knowledge(db: Session, query: str, limit: int = 5):
    return []   # dummy for SQLite