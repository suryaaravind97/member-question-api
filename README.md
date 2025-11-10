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


-----------------------------------------------------------------------------------------------

Bonus 1
While designing the question-answering system, several approaches were considered. The chosen solution uses a rule-based heuristic parser that relies on simple keyword matching, regular expressions, and scoring logic to extract meaningful answers from the /messages API. This design is fast, explainable, and well-suited for small datasets with inconsistent structure. A second approach explored involved machine learning–based QA models (like fine-tuned BERT or DistilBERT) that could interpret questions contextually, but these require large labeled datasets and more compute resources. Another idea was semantic search using embeddings (e.g., Sentence-BERT) to find message similarities in vector space, which would handle paraphrasing better but require vector databases and more complex infrastructure. In the end, the rule-based design was selected for its transparency, light footprint, and reliable performance on small-scale text data.

-----------------------------------------------------------------------------------------
Bonus -2
During dataset analysis, several inconsistencies were observed in the member data retrieved from the /messages API. Many records were incomplete or ambiguous—some messages referenced members such as Layla, Vikram, or Amira without any associated details about their trips, possessions, or preferences. The text data was unstructured, mixing topics like travel, restaurants, and events in free-form sentences rather than organized fields. Several date references (e.g., November 10, 15, 20, 25) appeared without clear context linking them to specific members or actions. There were also format variations and possible duplicates in capitalization or phrasing, suggesting noise in data entry. Overall, the dataset represents real-world conversational data that lacks consistent schema—highlighting the importance of robust preprocessing, entity extraction, and validation in building reliable natural-language systems.
