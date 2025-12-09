# 🏹 Bowmen Unified Agent: The Self-Healing Research OS

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-High_Performance-009688?logo=fastapi\&logoColor=white)
![OpenAI](https://img.shields.io/badge/AI-GPT--4o--Mini-412991?logo=openai\&logoColor=white)
![Qdrant](https://img.shields.io/badge/VectorDB-Qdrant-b91c1c?logo=qdrant\&logoColor=white)
![Redis](https://img.shields.io/badge/Memory-Redis-dc382d?logo=redis\&logoColor=white)
![Playwright](https://img.shields.io/badge/Crawler-Playwright-2EAD33?logo=playwright\&logoColor=white)

> **A production-grade Autonomous Research Agent featuring a "Self-Healing" conversational loop, tiered memory architecture, and background forensic crawling.**

---

## 🏗️ System Architecture

The system operates on a **Dual-Pipeline Architecture**. The API Gateway routes requests to either the **Deep Research Engine** (Phase 1) or the **Conversational OS** (Phase 2).

```mermaid
graph TD
    %% Styling
    classDef ai fill:#f9f,stroke:#333,stroke-width:2px,color:black;
    classDef db fill:#e1f5fe,stroke:#0277bd,stroke-width:2px,color:black;
    classDef ext fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:black;
    classDef logic fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:black;

    User([👤 User / Client]) -->|HTTP POST| API[🚀 FastAPI Gateway
(main.py)]

    %% MEMORY LAYER
    subgraph Memory_Layer [🧠 Tiered Memory System]
        Redis[(🔴 Redis
Short-Term Context)]:::db
        Qdrant[(🔵 Qdrant
Long-Term Knowledge)]:::db
    end

    %% PHASE 1: RESEARCH
    subgraph Phase1 [Phase 1: The Builder (Deep Research Engine)]
        RP[Research Pipeline]:::logic
        Scout[🕵️ Scout Agent]:::ai
        Strat[♟️ Strategist Agent]:::ai
        Writer[✍️ Writer Agent]:::ai
        Crawler[🕷️ Deep Crawler
(Playwright + BS4)]:::ext
    end

    %% PHASE 2: CHAT
    subgraph Phase2 [Phase 2: The Brain (Conversational OS)]
        CP[Chat Pipeline]:::logic
        Orch[🚦 Orchestrator
(The Boss)]:::ai
        Decomp[🧩 Decomposer]:::ai
        Evid[⚖️ Evidencer
(The Auditor)]:::ai
        Refine[🔄 Refiner]:::ai
        Ans[🗣️ Answer Agent]:::ai
    end

    %% EXTERNAL TOOLS
    subgraph Tools [🛠️ External Tool Shed]
        Serp[🌍 SerpApi / Serper
(Web Search)]:::ext
    end

    %% CONNECTIONS
    API -->|/research| RP
    API -->|/chat| CP

    %% P1 Logic
    RP --> Scout --> Strat
    Strat --> Serp --> Writer
    Writer -->|Save Final Report| Qdrant
    RP -.->|Trigger Background Task| Crawler
    Crawler -->|Spider & Clean Pages| Qdrant

    %% P2 Logic
    CP -->|Get Chat History| Redis
    CP --> Orch
    Orch -->|Simple Chat| Ans
    Orch -->|Complex Query| Decomp

    %% THE SELF-HEALING LOOP
    Decomp -->|Sub-Queries| Tools_Agent[Tools Manager]:::logic
    Tools_Agent -->|1. Check Memory| Qdrant
    Tools_Agent -->|2. Fallback to Web| Serp
    Tools_Agent -->|3. Gathered Evidence| Evid
    
    Evid -->|❌ Data Insufficient| Refine
    Refine -->|New Search Query| Tools_Agent
    Evid -->|✅ Data Sufficient| Ans

    Ans -->|Save Chat Turn| Redis
    Ans -->|Final Response| User
```

## 🛠️ Tech Stack & Tools

We chose tools for Reliability, Speed, and Cost Efficiency.

| Component     | Tool Used           | Why we chose it?                                       |
| ------------- | ------------------- | ------------------------------------------------------ |
| LLM Engine    | GPT-4o / Mini / 4.1 | Best balance of speed & intelligence for agentic loops |
| API Framework | FastAPI             | Async, lightweight, built for concurrency              |
| Vector DB     | Qdrant              | Long-term memory + fast similarity search              |
| Cache DB      | Redis               | Short-term conversation memory                         |
| Web Search    | SerpApi / Serper    | Real-time financial/news data                          |
| Deep Crawler  | Playwright          | Handles dynamic JS-heavy websites                      |
| Cleaner       | BeautifulSoup       | Removes noise for high-quality RAG chunks              |

---

## 🧠 Agent Logic Breakdown

### **Phase 1: Deep Research ("The Builder")**

Triggered via `/research`. Goal: Build the Knowledge Base.

* **🕵️ Scout Agent** — Understands the domain, company, and context
* **♟️ Strategist Agent** — Creates a forensic research plan
* **🌍 Tools Agent** — Executes 10–15 deep search queries
* **✍️ Writer Agent** — Produces a professional investment memo
* **🕷️ Crawler** — Indexes 50+ pages of the website into Qdrant

### **Phase 2: Conversational OS ("The Brain")**

Triggered via `/ask_stream`. Goal: Answer user questions with reasoning.

* **🚦 Orchestrator** — Routes the question to chat, recall, or research
* **🧩 Decomposer** — Breaks queries into atomic tasks
* **⚖️ Evidencer** — Validates whether retrieved data answers the question
* **🔄 Refiner** — Rewrites bad queries, re-searches, self-heals
* **🗣️ Answer Agent** — Produces the final verified answer

---

## 🚀 Installation & Setup

### 1. Prerequisites

Docker for Redis & Qdrant.

### 2. Infrastructure Setup

```
docker run -d -p 6379:6379 redis
docker run -d -p 6333:6333 -v $(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant
```

### 3. Application Setup

```
git clone <repo-url>
cd bowmen_unified
pip install -r requirements.txt
playwright install chromium
```

### 4. Configuration

Rename `.env.example` to `.env`:

```
OPENAI_API_KEY=sk-proj-...
SERPAPI_API_KEY=7716ac...
REDIS_HOST=localhost
REDIS_PORT=6379
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 5. Run the Server

```
python main.py
```

---

## ⚡ Usage Examples

### **1. Phase 1 Research**

```
curl -X POST "http://localhost:8000/research" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.databricks.com"}'
```

### **2. Phase 2 Chat**

```
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.databricks.com", "message": "What are their risks vs Snowflake?"}'
```

---

## 📂 Project Structure

```
bowmen_unified/
├── main.py                    
├── config/
│   ├── prompts.yaml           
│   └── config.yaml            
├── src/
│   ├── conversation/          
│   │   ├── pipeline.py        
│   │   └── orchestrator.py    
│   ├── agents/                
│   │   ├── research/          
│   │   ├── conversation/      
│   │   └── common/            
│   └── memory/                
```
