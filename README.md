# Introduction

- This repository provides a template to create a simple On Premise Langchain Langgraph agent workflow that is capable of performing RAG search, web search, summarization, and calculation.
- This repository was created via uv and all dependancies can be found on the pyproject.toml file.

# Functional Architecture

                ┌───────────────────────────┐
                │        User Query         │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │        LLM Layer          │
                │  - Ollama / vLLM          │
                │  - Azure Chat OpenAI      │
                └─────────────┬─────────────┘
                              │
          ┌───────────────────────┼──────────────────────────────┐
          │                       │                              │
          ▼                       ▼                              ▼
          ┌───────────────────┐ ┌──────────────────┐ ┌───────────────────┐
          │ HuggingFace       │ │ Persistent Memory│ │ Tools             │
          │ Embeddings (Local)│ │ Postgres (Local) │ │ - Calculator      │
          └─────────┬─────────┘ └────────┬─────────┘ │ - Summarizer      │
                    │                    │           │ - Rag Search      │
                    ▼                    │           │ - Web Search      │
         ┌───────────────────┐           │           │   (Tavily)        │
         │ FAISS Vector DB   │           │           └───────────────────┘
         │ (Local Retrieval) │           │
         └─────────┬─────────┘           │
                   │                     │
                   └──────────┬──────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │   Response Generation     │
                └─────────────┬─────────────┘
                              │
                              ▼
                ┌───────────────────────────┐
                │ Monitoring: Arize Phoenix │
                │ (Local Setup - Postgres)  │
                └───────────────────────────┘



# Components
- LLM : Options for Ollama and vLLM are provided. For the sake of testing on a non GPU instance, the Azure Chat OpenAI LLM is included.
- Embeddings model : HuggingFace Embeddings (Downloaded and fully local; does not depend on the Internet or API calls)
- RAG : FAISS Embeddings and Vector DB(Local). An alternative can be ChromaDB for vectorDB.
- Persistent Memory : PostgreSQL (Local) -> Need pgadmin and postgres installed. 
- Tools : Calculator, Summarizer, Rag Search, Web Search (Tavily)
- Monitoring - Arize Phoenix (Local Setup)

# Steps for Ollama Setup

Download Ollama LLM
- Download qwen3:4b model; please note that gemma models seem to be running into issues with Ollama at the moment of writing this code
  `ollama pull qwen3:4b`
- Pull the model and make sure Ollama is running on port 11434

# Steps for vLLM Setup
Please refer to  https://docs.vllm.ai/en/latest/getting_started/quickstart/.

# Langchain Agent - Langgraph Workflow
This is a cyclical loop where the agent decides if/which tool should be used based on the query. It falls back to the agent if further steps are needed.
- Start at "agent" and model makes a decision.
- If tools are needed, go to "tools".
- After tool use, return to "agent" for further reasoning.
- If no further action is needed, end the workflow

<img width="600" height="400" alt="Generated Image" src="https://github.com/user-attachments/assets/9febfb2f-4f16-4c88-9bab-2f37ad57635e" />

# Python Files
There are four files used here.
- main.py : This is the main execution file
- memory.py : This handles all fucntions related to persistent memory via SQLite
- toolkit.py : This handles all tool creation.
- add_documents_faiss.py : This handles the cconversion of documents to a vector format and store it in the faiss_index.
- faiss_search.py : This handles the vector database and search functions for RAG Search.

# How to use
- Run the add_documents_faiss.py file to add documents in the folder to the FAISS index or update the FAISS index.
- Run the postgres_database_setup to create databases for chat histopry and monitoring history. Ensure pgadmin and postgreSQL is installed.
- Run the main.py file
- For Web Search, I use Tavily, you may need to set up an API access for it.
- For monitoring, please use the http://localhost:6006/projects to view token usage and costs of each prompt and response. Additional annotations can be added.
- To view the persistent memory database file .db, please use https://inloop.github.io/sqlite-viewer/.

# Next Steps:
- Expand guardrail implementation
- Cache frequently accessed embeddings or LLM responses.
- Might expand the toolkit for product/ finance/ location search, etc.
- Improve monitoring cpaability to have session search and trace alerts
- UI - Include source material from web search or knowledge base
- Expand to incorporate multimodal support where files can be ingested immediately to provide context to a prompt.
- Change to Strucutred RAG over simple RAG. (Graph RAG can be an option but preferable for SQL vector database as querying is more efficient).
- Include a frontend webapp via StreamLit or Gradio --or better React or Next. If simpler, just an html based one is also good.
- Improved prompting - I did not find this necessary as it really depends on data quality as well.










































