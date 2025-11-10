# 🧠 Member Question Answering API

A simple **FastAPI** service that answers natural-language questions about member data fetched from the public `/messages` API.

---

## 🚀 Overview

This project implements a small REST API that can interpret natural-language questions and respond with answers extracted or inferred from the `/messages` dataset.

Example questions:
- “When is Layla planning her trip to London?”
- “How many cars does Vikram Desai have?”
- “What are Amira’s favorite restaurants?”

The endpoint `/ask` accepts a free-text question and returns a JSON response:
```json
{ "answer": "..." }
