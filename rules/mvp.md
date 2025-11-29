# AI-Powered Interviewer — Architecture & Build Plan (Clerk Auth + Postgres Edition)

> Goal: Build a production-ready, deployable AI Interviewer that accepts CV (PDF) and Job Description (PDF/text), ingests them with RAG, conducts a realistic interview (audio↔audio, coding IDE, architecture diagram drawing, video prompts), runs code execution in a sandbox, gives structured feedback, and escalates heavy reasoning to Gemini (via Google ADK). The system uses **Clerk for authentication**, **Postgres** for persistent data (Supabase-compatible), and a multi-agent architecture.

---

## 1 — High-level system architecture

### **Frontend (Next.js on Vercel)**

* Clerk authentication UI (sign-in, sign-up, OAuth, session tokens)
* Secure file upload for CV & JD
* Chat interface with audio↔audio interactions
* Monaco coding IDE (real-time editor)
* Architecture whiteboard (Excalidraw / custom canvas)
* WebRTC-powered video prompts and optional camera usage
* WebSocket client for real-time updates (editor diffs, logs)
* Clerk-protected API requests (JWT attached automatically)

---

### **Backend API Gateway (FastAPI or Node.js on Render / Cloud Run)**

Handles all authenticated requests. Responsibilities:

* Clerk JWT verification
* Session and interview lifecycle management
* CV/JD ingestion endpoints
* RAG query endpoints
* Audio STT/TTS management (proxy to STT/TTS providers)
* Model routing (light model vs Gemini)
* Observability & metrics

Backend uses **Postgres** as the primary DB.

---

### **Database Layer (Postgres)**

Stores structured data for:

* Users (Clerk-managed identity references only)
* Sessions (interviews)
* CV/JD metadata and extracted text
* RAG embeddings (via pgvector)
* History, logs, memory snapshots
* Code submissions, run/test results

Postgres schema integrates:

* `pgvector` for embeddings
* `jsonb` for agent memories and feedback

---

### **RAG Pipeline**

Processing flow:

1. Upload CV/JD → store raw PDF in storage bucket
2. Extract text (PyMuPDF or similar)
3. Chunk text into semantic segments
4. Embed using small embedding model
5. Store in Postgres `pgvector`
6. Query relevant chunks during interview

This powers contextual follow-up questions, CV gap detection, and relevance scoring.

---

### **Multi-Agent Orchestrator (Google ADK + custom agents)**

Agents include:

#### **Coordinator Agent**

* Controls flow of interview
* Selects question difficulty
* Routes tasks to planner/code-review/diagram agents
* Decides when to escalate to Gemini

#### **Planner Agent**

* Designs interview structure based on JD, CV, and past answers
* Chooses coding, system design, behavioral questions

#### **Tool Agent**

* Code execution
* Web search (if added)
* Diagram interpretation tasks (vision models)

#### **Memory Agent**

* Manages InSessionMemory (short-term)
* Persists key points to Postgres for long-term memory
* Provides conversation continuity

---

### **Judge / Sandbox Worker (Docker-based)**

Executes candidate code safely:

* Python, JS, Java, C++ runners
* Resource limits (CPU/mem/time)
* Network disabled
* Each run isolated in a container

Returns structured JSON:

* Pass/fail
* Failing tests & reasons
* Stack traces
* Performance metrics

Only minimal structured data goes to LLM for cost-efficient feedback.

---

### **Audio/Video Pipeline**

* WebRTC (LiveKit recommended) for video prompts and optional webcam
* Audio input converted to text using STT (Whisper/Groq/STT provider)
* Audio output generated via TTS (ElevenLabs or TTS provider)
* Audio↔audio loop for realistic interviewer experience

---

### **Model & Routing Policy**

Use lightweight LLMs for bulk logic:

* Conversation
* Follow-up questioning
* Soft feedback
* Routing hints

Use **Gemini (through ADK)** only for heavy tasks:

* Code feedback
* Architecture diagram critique
* Deep reasoning
* Complex debugging
* Final candidate scoring

This ensures low cost + maximum evaluation points.

---

## 2 — End-to-end flow (sequence)

1. User authenticates via **Clerk**.
2. User uploads CV (PDF) + Job Description.
3. Backend extracts text → chunks → embeddings → store in Postgres.
4. User clicks **Start Interview** → backend creates session + InSessionMemory.
5. Coordinator agent fetches CV/JD context using RAG and generates opening question.
6. UI plays audio + text question.
7. Candidate answers via:

   * Text
   * Audio (STT → text)
   * Code in IDE
   * Diagram on whiteboard
8. For code questions:

   * Editor diffs stream through WS
   * User presses Run → judge runs tests locally (no LLM)
   * User presses Submit → judge + Gemini feedback (minimal diffs only)
9. System stores all memories and logs in Postgres.
10. Interview concludes with a Gemini-powered evaluation & improvement roadmap.

---

## 3 — Key API Endpoints

**Auth handled by Clerk; backend verifies JWT.**

* `POST /upload` → Upload CV/JD
* `POST /session/create`
* `POST /session/{id}/start`
* `WS /ws/{session_id}` → real-time diffs/events
* `POST /run` → sandbox code execution
* `POST /submit` → judge + Gemini feedback
* `POST /rag/query`
* `GET /session/{id}/memory`
* `GET /metrics`

---

## 4 — Postgres Schema (Simplified)

**users**

* user_id (Clerk ID)
* email
* created_at

**files**

* file_id
* user_id
* type (cv/jd)
* storage_url
* text

**embeddings**

* emb_id
* file_id
* chunk_text
* embedding (vector)

**sessions**

* session_id
* user_id
* status (ongoing/completed)
* created_at

**messages**

* id
* session_id
* role (user/agent)
* content
* ts

**code_runs**

* run_id
* session_id
* results json
* ts

**memories**

* id
* session_id
* payload json
* ts

---

## 5 — Observability

Store structured data in Postgres + logs:

* Test run timings
* LLM usage metrics
* Model routing decisions
* Agent traces

Expose Prometheus-style metrics via `/metrics`.

---

## 6 — Deployment Model

* Frontend → **Vercel** (Next.js)
* Backend → **Render** or **Cloud Run**
* Judge worker → separate Render service or Cloud Run job
* Postgres → Managed Postgres (Supabase, Neon, Railway)
* Clerk → Authentication provider
* File storage → Supabase Storage / GCS / S3

---

## 7 — MVP Roadmap

**Phase 1 (MVP)**

* Clerk auth integrated
* Upload + RAG ingestion pipeline
* Basic chat agent using light model
* Basic coding IDE + run tests
* Session memory
* Minimal feedback

**Phase 2 (Advanced)**

* Gemini reasoning
* Audio↔audio pipeline
* Diagram drawing + critique
* System design questions
* Full observability dashboard
* Interview replay UI

---

If you want, the next step can be generating the **GitHub project scaffold** (frontend + backend + DB migrations + agent router) based on this architecture.
