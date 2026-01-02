# 🚀 X Post Generator Backend (API)

A **production-grade AI backend** for generating X (Twitter) posts using **FastAPI + LangGraph**, with **human-in-the-loop feedback**, **thread-based workflow state**, and **robust error handling** for real-world API failures (rate limits, invalid users, etc.).

This backend is designed to work seamlessly with a frontend that supports **generate → feedback → resume** flows.

🔗 **Live App**: https://x-post-frontend-iota.vercel.app  (Deployed on Vercel)
---

## ✨ Key Features

- 🧠 **LangGraph-based AI workflow**
- 🔁 **Human feedback loop** (interrupt & resume)
- ⚡ **FastAPI REST API**
- 🧵 **Thread-based state management**
- 🛑 Graceful handling of:
  - Rate limits
  - Invalid / missing users
  - LLM failures (GROQ API)
- 🔍 Clean API schemas
- 🧪 Easy to extend & debug

---

## 🧱 Tech Stack

| Layer | Technology |
|------|-----------|
| Backend | FastAPI |
| AI Orchestration | LangGraph |
| LLM | Groq / OpenAI-compatible |
| Server | Uvicorn |
| Language | Python 3.10+ |
| State | Graph thread snapshots |

---

## 📂 Project Structure (Actual)

X_Post_Generator(API)/
├── api/
│   ├── router/
│   │   ├── generate.py          # POST /generate
│   │   ├── resume.py            # POST /resume/{thread_id}
│   │   └── __init__.py
│   │
│   ├── schemas.py               # Request / response models
│   ├── server.py                # API router aggregation
│   └── __init__.py
│
├── graph/
│   ├── nodes.py                 # LangGraph nodes
│   ├── workflow.py              # Graph definition
│   └── __init__.py
│
├── twitter_mcp_server/
│   ├── client.py                # Twitter/X client logic
│   ├── twitter_mcp_server4.py   # MCP integration
│   └── __init__.py
│
├── llm.py                      
├── utils.py                     # Shared helpers
├── config.py                   
├── main.py              ]
│
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── .env
├── .gitignore
├── LICENSE
├── TERMS_OF_SERVICE.md
└── README.md



---

## 🧠 Advanced Roadmap (Planned Enhancements)

This project is designed with **enterprise extensibility** in mind. Below are planned upgrades that align with **paid API–grade AI platforms**.

---

### 📚 Retrieval-Augmented Generation (RAG)

Add **document-aware tweet generation**, enabling the system to create posts grounded in trusted sources instead of raw prompts.

**Planned Capabilities:**
- Generate X posts based on:
  - PDFs
  - Research papers
  - Notes / documents
  - Knowledge bases
- Vector database integration:
  - FAISS / Chroma / Pinecone
- Semantic document retrieval
- Context-aware post generation
- Source-grounded outputs (reduced hallucinations)

**Use Cases:**
- Research-driven thought leadership
- Brand-aligned content
- Technical or academic threads
- Long-form tweet series from documents

---

### 💼 Paid API–Grade Features (Planned)

These features align with **commercial AI platforms** and SaaS offerings:

- 🔐 API authentication & key-based access
- 📊 Post performance analytics
- 🧵 Threaded / long-form tweet generation
- 🧠 Tone, persona & brand presets
- 🗓️ Scheduled post generation
- 🔄 Multi-platform support (X, LinkedIn, Threads)
- 💳 Usage limits & billing hooks
- 🐳 Dockerized, scalable deployment
- 📈 Monitoring & logging

---

## 📜 License & Usage Restrictions

### ⚠️ PROPRIETARY LICENSE — ALL RIGHTS RESERVED

This repository is **NOT open-source**.

**You may NOT:**
- Copy or redistribute this code
- Use it for commercial purposes
- Modify, sublicense, or resell it
- Deploy it as a public or private service
- Use it to train or fine-tune models

**You MAY:**
- View the code for learning and evaluation only
- Run the project locally for personal understanding

Unauthorized use, distribution, or commercial exploitation is **strictly prohibited** and may result in legal action.

See the [`LICENSE`](./LICENSE) file for full legal terms.

---

## 👤 Author

**Puneet Ranjan**  
AI/ML Engineer 

**Focus Areas:**
- Production-grade AI backends
- LangGraph-based orchestration
- Human-in-the-loop AI systems
- Scalable LLM architectures

---

> 🚨 This repository represents **original architectural work** and is intentionally restrictive.


