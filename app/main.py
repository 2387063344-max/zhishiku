from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List
import uuid

app = FastAPI(title="zhishiku-api")

class ArticleIn(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)
    tags: List[str] = []

class KeywordReq(BaseModel):
    query: str
    top_k: int = 10

class SemanticReq(BaseModel):
    query: str
    top_k: int = 8

class WriteReq(BaseModel):
    topic: str
    use_web: bool = False

ARTICLES = []

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/articles")
def create_article(a: ArticleIn):
    item = {"id": str(uuid.uuid4()), **a.model_dump()}
    ARTICLES.append(item)
    return item

@app.post("/api/search/keyword")
def search_keyword(req: KeywordReq):
    q = req.query.lower()
    hits = []
    for a in ARTICLES:
        text = (a["title"] + " " + a["content"]).lower()
        score = text.count(q)
        if score > 0:
            hits.append({"article_id": a["id"], "title": a["title"], "score": score, "snippet": a["content"][:120]})
    hits.sort(key=lambda x: x["score"], reverse=True)
    return {"mode": "keyword", "hits": hits[:req.top_k]}

@app.post("/api/search/semantic")
def search_semantic(req: SemanticReq):
    # MVP 简化：先用包含关系近似语义
    q = req.query
    chunks = []
    for a in ARTICLES:
        score = 1.0 if any(k in a["content"] for k in q[:4]) else 0.2
        chunks.append({"article_id": a["id"], "title": a["title"], "chunk": a["content"][:180], "score": score})
    chunks.sort(key=lambda x: x["score"], reverse=True)
    return {"mode": "semantic", "chunks": chunks[:req.top_k]}

@app.post("/api/write/topic")
def write_topic(req: WriteReq):
    related = [a for a in ARTICLES if req.topic[:2] in (a["title"] + a["content"])]
    kb_points = "\n".join([f"- {a['title']}: {a['content'][:80]}..." for a in related[:3]]) or "- 暂无足够知识库内容"
    article = f"""# {req.topic}

## 引言
本文基于知识库进行总结。

## 相关证据
{kb_points}

## 结论
AI 更可能改变分工，而不是简单取代人类。"""
    sources = [{"source_type": "kb", "source_id": a["id"], "quote": a["content"][:120]} for a in related[:3]]
    return {"topic": req.topic, "article": article, "sources": sources}
