import hashlib


def cache_key(query: str, top_k: int, vector_weight: float, keyword_weight: float) -> str:
    material = f"{query.strip().lower()}|{top_k}|{vector_weight}|{keyword_weight}"
    return "rag:query:" + hashlib.sha256(material.encode()).hexdigest()
