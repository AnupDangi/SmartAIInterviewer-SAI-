graph TB
    subgraph "Client Layer"
        USER[User Interface]
    end
    
    subgraph "Authentication"
        AUTH[Clerk Auth]
        JWT[JWT Verification]
        AUTH --> JWT
    end
    
    subgraph "Chat System"
        CHAT[Chat Handler]
        ROUTER[Model Router]
        LIGHT[Lightweight LLM]
        GEMINI[Gemini]
        MEMORY[Memory Manager]
        
        CHAT --> ROUTER
        ROUTER --> LIGHT
        ROUTER --> GEMINI
        CHAT --> MEMORY
    end
    
    subgraph "RAG System"
        UPLOAD[PDF Upload]
        PROCESS[Extract & Chunk]
        EMBED[Embeddings]
        VECTOR[(Vector DB)]
        SEARCH[Semantic Search]
        
        UPLOAD --> PROCESS
        PROCESS --> EMBED
        EMBED --> VECTOR
        SEARCH --> VECTOR
    end
    
    subgraph "Code Execution"
        CODE[Code Request]
        SANDBOX[Sandbox Worker]
        EXECUTE[Run & Test]
        
        CODE --> SANDBOX
        SANDBOX --> EXECUTE
    end
    
    subgraph "Agent System"
        COORDINATOR[Coordinator Agent]
        PLANNER[Planner Agent]
        TOOL[Tool Agent]
        
        COORDINATOR --> PLANNER
        COORDINATOR --> TOOL
    end
    
    subgraph "Media Processing"
        AUDIO[Audio Input]
        STT[Speech-to-Text]
        TTS[Text-to-Speech]
        VIDEO[Video Stream]
        
        AUDIO --> STT
        TTS --> AUDIO
    end
    
    subgraph "Realtime Collaboration"
        EDITOR[Code Editor]
        BOARD[Whiteboard]
        WS[WebSocket]
        
        EDITOR --> WS
        BOARD --> WS
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        FILES[(File Storage)]
    end
    
    USER --> AUTH
    JWT --> CHAT
    
    USER --> UPLOAD
    USER --> CODE
    USER --> AUDIO
    USER --> EDITOR
    USER --> BOARD
    
    CHAT --> COORDINATOR
    COORDINATOR --> SEARCH
    COORDINATOR --> TOOL
    TOOL --> SANDBOX
    PLANNER --> SEARCH
    
    STT --> CHAT
    CHAT --> TTS
    VIDEO --> COORDINATOR
    
    MEMORY --> DB
    EXECUTE --> DB
    PROCESS --> FILES
    WS --> COORDINATOR