# ResearchMind

> Multi-agent research assistant, drop in a query, get back a full research report.

Think Perplexity, but you own every layer: the orchestration, the search, the synthesis, the write-up.

---

## What it does

ResearchMind takes a single natural-language query and runs it through a pipeline of autonomous agents that plan what to look for, search the web, retrieve from a vector store, extract the signal from the noise, and write a structured long-form report — all without you touching it again.

###  How it Works
![ResearchMind architecture](assets/SystemDesign.png)

---

## Architecture

![ResearchMind architecture](assets/System-Design.png)

---

## Stack

| Layer | Tech |
|---|---|
| API gateway | FastAPI |
| Orchestration | LangGraph |
| LLM | Claude (Anthropic SDK) |
| Web search | Tavily |
| State / checkpointing | Redis |
| Vector store | pgvector (Postgres) |
| Observability | LangSmith |

---

## Getting started

```bash
git clone https://github.com/your-username/researchmind
cd researchmind
cp .env.example .env   # fill in API keys
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then hit it:

```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest advances in solid-state batteries?"}'
```

---

## Environment variables


---

## Status

 Work in progress
 

## Written By:
Darlene Wendy