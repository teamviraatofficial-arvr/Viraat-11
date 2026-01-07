# VIRAAT Military AI Assistant

An advanced AI-powered query resolution system designed for military, army, and security decision-making. Built with local LLM capabilities for privacy and security.

## Features

- 🤖 **Local LLM Integration** - Runs entirely on your machine for maximum security
- 📚 **RAG System** - Retrieval Augmented Generation with military knowledge base
- 💬 **Multi-turn Conversations** - Contextual dialogue with memory
- 🎤 **Voice Support** - Voice input and text-to-speech output
- 🔒 **Authentication** - JWT-based secure authentication
- 📊 **Analytics** - Query tracking and performance metrics
- 🌐 **Multi-platform** - Web, API, and Desktop applications
- 💻 **Code Display** - Syntax-highlighted code responses

## Architecture

```
viraat-military-ai/
├── backend/              # FastAPI backend with ML models
├── web/                  # Web application
├── desktop/              # Electron desktop app
├── knowledge-base/       # Military domain documents & embeddings
└── docs/                 # Documentation
```

## Tech Stack

- **Backend**: FastAPI, Python 3.10+
- **ML/AI**: llama-cpp-python, ChromaDB, LangChain
- **Database**: PostgreSQL (conversations), ChromaDB (vector store)
- **Frontend**: Vanilla JS, Modern CSS
- **Desktop**: Electron
- **Authentication**: JWT tokens

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- At least 8GB RAM (16GB recommended for local LLMs)

### Installation

1. **Clone and navigate to project**

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai"
```

2. **Set up backend**

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Download local LLM model**

```bash
# Download a quantized Mistral or Llama model (GGUF format)
# Place in backend/models/llm/
```

4. **Configure environment**

```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run backend**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

6. **Run web application**

```bash
cd ../web
python3 -m http.server 3000
# Or use any static file server
```

7. **Access the application**

- Web: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Development Phases

- ✅ **Phase 1**: Core Backend + Web App (Current)
- ⏳ **Phase 2**: Enhanced Features (Voice, Analytics)
- ⏳ **Phase 3**: Desktop Application
- ⏳ **Phase 4**: Mobile Application
- ⏳ **Phase 5**: AR/VR Integration

## Security Notice

⚠️ This system is designed for educational and prototype purposes. For production military use:

- Implement additional security layers
- Use classified data sources with proper authorization
- Add audit logging and compliance features
- Deploy in secure, isolated environments

## License

Proprietary - For authorized use only

## Contact

Project VIRAAT 11
