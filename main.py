
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import re
from typing import List, Dict, Any, Optional, Tuple

app = FastAPI(
    title="Member Question Answering API",
    description="Simple API that answers natural-language questions about member data.",
    version="1.0.0",
)

MESSAGES_URL = "https://november7-730026606190.europe-west1.run.app/messages"

STOPWORDS = {
    "the", "is", "are", "a", "an", "to", "of", "for", "and", "or", "in", "on",
    "at", "with", "what", "when", "how", "many", "does", "have", "his", "her",
    "their", "favorite", "favorites", "planning", "trip"
}

def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())

def extract_member_name(question: str) -> Optional[str]:
    patterns = [
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)['’]s",
        r"When is ([A-Z][a-z]+(?: [A-Z][a-z]+)?)",
        r"How many .+ does ([A-Z][a-z]+(?: [A-Z][a-z]+)?) have",
        r"([A-Z][a-z]+(?: [A-Z][a-z]+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, question)
        if m:
            return m.group(1)
    return None

def fetch_messages() -> List[Dict[str, Any]]:
    try:
        resp = requests.get(MESSAGES_URL, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error calling /messages: {e}")

    data = resp.json()
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ["messages", "items", "data", "results"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v

    raise HTTPException(status_code=500, detail="Unexpected /messages response format.")

def filter_messages_for_member(messages: List[Dict[str, Any]], member_name: str) -> List[Dict[str, Any]]:
    member_name_lower = member_name.lower()
    filtered = []
    for msg in messages:
        text = str(msg.get("text") or msg.get("message") or "")
        member_field = msg.get("member") or msg.get("member_name") or msg.get("user") or ""
        if isinstance(member_field, dict):
            member_field_str = " ".join(str(v) for v in member_field.values())
        else:
            member_field_str = str(member_field)
        if member_name_lower in member_field_str.lower() or member_name_lower in text.lower():
            filtered.append(msg)
    return filtered or messages

def score_message_relevance(question: str, message_text: str) -> int:
    q_tokens = [t for t in tokenize(question) if t not in STOPWORDS]
    m_tokens = set(tokenize(message_text))
    return sum(1 for t in q_tokens if t in m_tokens)

def message_has_date(text: str) -> bool:
    date_patterns = [
        r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2}(?:,\s*\d{4})?",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
        r"\b(next week|next month|this weekend|tomorrow|day after tomorrow)\b",
    ]
    return any(re.search(pat, text, re.IGNORECASE) for pat in date_patterns)

def pick_best_message(question: str, messages: List[Dict[str, Any]]) -> Tuple[Optional[Dict[str, Any]], int]:
    is_when_question = question.strip().lower().startswith("when")
    best_msg, best_score = None, -1
    q_lower = question.lower()
    destination = None
    dest_match = re.search(r"\bto ([A-Z][a-z]+)\b", question)
    if dest_match:
        destination = dest_match.group(1).lower()

    for msg in messages:
        text = str(msg.get("text") or msg.get("message") or "")
        text_lower = text.lower()
        base_score = score_message_relevance(question, text)
        if destination and destination in text_lower:
            base_score += 2
        if is_when_question and destination:
            if not (destination in text_lower and message_has_date(text)):
                continue
        if base_score > best_score:
            best_score = base_score
            best_msg = msg
    return best_msg, best_score

def extract_answer(question: str, message_text: str) -> str:
    q_lower = question.strip().lower()
    text_lower = message_text.lower()
    if q_lower.startswith("when"):
        date_patterns = [
            r"\b(?:Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|Nov|November|Dec|December)\s+\d{1,2}(?:,\s*\d{4})?",
            r"\b\d{4}-\d{2}-\d{2}\b",
            r"\b\d{1,2}/\d{1,2}/\d{2,4}\b",
            r"\b(next week|next month|this weekend|tomorrow|day after tomorrow)\b",
        ]
        for pat in date_patterns:
            m = re.search(pat, message_text, re.IGNORECASE)
            if m:
                return m.group(0)
        return "I couldn't find any date or time for that trip in the messages."
    if q_lower.startswith("how many"):
        if "car" in q_lower and ("car" not in text_lower and "cars" not in text_lower):
            return "I couldn't find any number related to that question."
        m = re.search(r"\b\d+\b", message_text)
        if m:
            return m.group(0)
        return "I couldn't find any number related to that question."
    if "favorite restaurant" in q_lower or "favourite restaurant" in q_lower:
        m = re.search(r"favorite restaurants? (are|is|:)\s*(.+)", message_text, re.IGNORECASE)
        if m:
            raw = m.group(2)
            parts = re.split(r",| and ", raw)
            cleaned = [p.strip(" .!") for p in parts if p.strip()]
            if cleaned:
                return ", ".join(cleaned)
        return "I couldn't find any information about their favorite restaurants in the messages."
    snippet = message_text.strip()
    if len(snippet) > 180:
        snippet = snippet[:180].rsplit(" ", 1)[0] + "..."
    return snippet or "I couldn't infer an answer from the messages."

@app.get("/ask")
def ask(question: str = Query(..., description="Enter a natural-language question")):
    if not question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    messages = fetch_messages()
    if not messages:
        raise HTTPException(status_code=500, detail="No messages found from /messages.")
    member_name = extract_member_name(question)
    if member_name:
        messages = filter_messages_for_member(messages, member_name)
    best_msg, best_score = pick_best_message(question, messages)
    if not best_msg or best_score <= 0:
        return JSONResponse(content={"answer": "I couldn't find any relevant information."})
    message_text = str(best_msg.get("text") or best_msg.get("message") or "")
    answer = extract_answer(question, message_text)
    return JSONResponse(content={"answer": answer})
