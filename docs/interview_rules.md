# Smart AI Interviewer - Logic & Rules

This document outlines the master flow of how the AI Interviewer conducts and evaluates a candidate, designed to mimic a real senior technical interviewer.

---

## 1. The Interview Flow

The interview follows a natural, adaptive flow with four distinct phases:

### Phase 1: Introduction (Warm-up)
*   **Goal**: Build rapport, set tone, evaluate confidence.
*   **Behavior**:
    *   Greet the candidate by name.
    *   Reference a specific item from their CV to show familiarity.
    *   Ask for a brief (60-90s) self-introduction.
*   **Assessment**: Clarity, confidence, ability to summarize.

### Phase 2: Technical Evaluation (Core)
*   **Goal**: Probe depth of knowledge, not just memorization.
*   **Behavior**:
    *   **Select Topic**: Based on JD requirements and CV projects.
    *   **Anchor Question**: Start with a broad, open-ended question (e.g., "Walk me through...").
    *   **Probing Loop**:
        *   If answer is **shallow**: Probe deeper (Why? How? What if?).
        *   If answer is **strong**: Increase difficulty (Scaling, Edge cases, Trade-offs).
*   **Coding Tasks**:
    *   If code is required, the `CoordinatorAgent` hands off to the `CodingAgent`.
    *   The `CodingAgent` can execute code using the Piston API (Python, C++, Java, C).
    *   Focus on correctness, efficiency, and readability.

### Phase 3: Behavioral & Communication
*   **Goal**: Assess team fit, ownership, and soft skills.
*   **Behavior**:
    *   Use STAR method prompts (Situation, Task, Action, Result).
    *   Focus on conflict resolution, leadership, and learning from failure.

### Phase 4: Closing
*   **Goal**: Wrap up professionally.
*   **Behavior**:
    *   Thank the candidate.
    *   Provide a summary of the session.
    *   End the session.

---

## 2. System Architecture & Agents

### Coordinator Agent
*   **Role**: The main orchestrator. Manages the conversation flow, state, and high-level logic.
*   **Model**: `gemini-2.5-flash` (fast, efficient) for most turns.
*   **Responsibilities**:
    *   Maintains interview state (Intro -> Technical -> Behavioral -> Closing).
    *   Decides when to switch stages based on time and question count.
    *   Generates questions and feedback.
    *   Detects coding intent and delegates to `CodingAgent`.

### Coding Agent
*   **Role**: Specialized agent for code generation and execution.
*   **Model**: `gemini-2.5-pro` (reasoning-heavy).
*   **Responsibilities**:
    *   Writes, debugs, and explains code.
    *   Executes code using the `execute_code` tool.
    *   Verifies candidate solutions.

### Session Management
*   **Time-Aware**: Strictly adheres to the interview duration (default 30 mins).
*   **Stateful**: Uses `InterviewMemory` to track:
    *   Current Stage
    *   Question Count
    *   Topics Covered
    *   Last Answer Depth
*   **Resilient**: Handles backend errors (503, 429) with retries and graceful degradation.

---

## 3. Scoring & Evaluation

The AI evaluates candidates on 5 key metrics (0.0 - 1.0):

1.  **Technical Foundations**: Understanding of core concepts.
2.  **Depth of Knowledge**: Ability to explain "why" and handle complexity.
3.  **Problem-Solving**: Structured approach, requirement clarification.
4.  **Communication**: Clarity, conciseness.
5.  **Behavioral Fit**: Ownership, collaboration.

**Decision Logic**:
*   **Strong Hire**: > 0.75 aggregate score.
*   **Hire**: 0.55 - 0.75.
*   **Reject**: < 0.55.

---

## 4. Technical Implementation Details

### System Instruction (JSON Format)

```json
{
  "interviewer_role": "senior_technical",
  "stages": ["intro", "technical", "behavioral", "closing"],
  "stage_instructions": {
    "intro": {
      "task": "Greet, reference CV, ask for intro.",
      "output_format": "QUESTION: <text>\\nFEEDBACK: <optional text>"
    },
    "technical": {
      "task": "Anchor question -> Probe loop (clarify -> approach -> tradeoffs -> edge cases).",
      "probing_rules": {
        "if_depth_lt_0.5": "Probe deeper",
        "if_depth_gt_0.7": "Escalate difficulty"
      }
    },
    "behavioral": {
      "task": "STAR-style questions.",
      "output_format": "QUESTION: <text>\\nFEEDBACK: <optional text>"
    }
  },
  "response_rules": {
    "question_length": "1-3 sentences",
    "feedback_length": "1 sentence",
    "always_reference_last_answer": true
  }
}
```

### Architecture Diagram

```mermaid
flowchart TB
  A[User Start] --> B[CoordinatorAgent]
  B --> C{Stage?}
  C -- Intro/Behavioral --> D[Generate Question (Flash)]
  C -- Technical --> E{Coding Needed?}
  E -- No --> D
  E -- Yes --> F[CodingAgent (Pro)]
  F --> G[Execute Code Tool]
  G --> F
  F --> H[Response]
  D --> H
  H --> I[Frontend UI]
```
