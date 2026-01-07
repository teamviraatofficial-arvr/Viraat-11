# VIRAAT Military AI Assistant - Setup Guide

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher** - [Download](https://www.python.org/downloads/)
- **PostgreSQL 14+** - [Download](https://www.postgresql.org/download/)
- **Node.js 18+** (for desktop app) - [Download](https://nodejs.org/)
- **At least 8GB RAM** (16GB recommended for running local LLMs)
- **10GB+ free disk space** (for model files)

## Step 1: Database Setup

### Install PostgreSQL

1. Install PostgreSQL for your operating system
2. Start PostgreSQL service

### Create Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE viraat_military_ai;
CREATE USER viraat_user WITH PASSWORD 'viraat_pass';
GRANT ALL PRIVILEGES ON DATABASE viraat_military_ai TO viraat_user;

# Exit
\q
```

### Initialize Schema

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/backend"
psql -U viraat_user -d viraat_military_ai < database/schema.sql
```

## Step 2: Backend Setup

### Create Virtual Environment

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/backend"
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note**: Installing `llama-cpp-python` may take several minutes. If you have a GPU, you can install the CUDA version:

```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
```

### Download Local LLM Model

You need to download a GGUF format model. Recommended options:

#### Option 1: Mistral-7B-Instruct (Recommended)

```bash
# Create models directory
mkdir -p models/llm

# Download model (example using wget)
cd models/llm
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf
```

#### Option 2: Llama-2-7B-Chat

```bash
cd models/llm
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf
```

**Alternative**: Download models manually from [Hugging Face](https://huggingface.co/models?search=gguf) and place in `backend/models/llm/`

### Configure Environment

```bash
# Copy example environment file
cp ../.env.example .env

# Edit .env file
nano .env  # or use any text editor
```

Update the following in `.env`:

```bash
# Update model path to match your downloaded model
LLM_MODEL_PATH=./models/llm/mistral-7b-instruct-v0.2.Q4_K_M.gguf

# Update database URL if needed
DATABASE_URL=postgresql://viraat_user:viraat_pass@localhost:5432/viraat_military_ai

# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

## Step 3: Knowledge Base Setup

### Ingest Documents

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/knowledge-base"

# Make script executable
chmod +x ingest.py

# Run ingestion
python3 ingest.py
```

This will process all documents in `knowledge-base/sources/` and create embeddings.

### Add Custom Documents (Optional)

Place your own `.md` or `.txt` files in `knowledge-base/sources/` and run:

```bash
python3 ingest.py --reset  # Reset and re-ingest everything
```

## Step 4: Run Backend Server

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/backend"
source venv/bin/activate

# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### First Run Notes

- First startup will take 1-2 minutes to load the LLM model
- Check terminal output for any errors
- GPU users: Model loading will be faster

## Step 5: Run Web Application

### Option 1: Python HTTP Server (Simplest)

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/web"
python3 -m http.server 3000
```

Access at: http://localhost:3000

### Option 2: Node.js HTTP Server

```bash
cd "/Users/krishnasumathi/Documents/VIRAAT 11/viraat-military-ai/web"
npx http-server -p 3000
```

### Option 3: VS Code Live Server

If using VS Code:

1. Install "Live Server" extension
2. Right-click on `index.html`
3. Select "Open with Live Server"

## Step 6: First Login

1. Open http://localhost:3000
2. Click "Register" tab
3. Create your first account:
   - Username: `admin`
   - Email: `admin@viraat.ai`
   - Password: `your_secure_password`
   - Full Name: `Administrator`

The first user will have default "user" role. You can manually promote to admin in the database if needed.

## Testing the System

### Test API Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "llm_loaded": true,
  "rag_initialized": true
}
```

### Test Knowledge Base

```bash
cd knowledge-base
python3 ingest.py --test "What is the structure of the Indian Army?"
```

### Test Chat

1. Log into web app
2. Try example queries:
   - "What is the organizational structure of the Indian Army?"
   - "Explain the OODA loop"
   - "What are the principles of secure communications?"

## Troubleshooting

### Model Loading Issues

**Problem**: `Model not found` error

**Solution**:

- Verify model file exists in `backend/models/llm/`
- Update `LLM_MODEL_PATH` in `.env` to match exact filename
- Ensure model is in GGUF format

### Database Connection Issues

**Problem**: `Could not connect to database`

**Solution**:

- Ensure PostgreSQL is running: `pg_isready`
- Check credentials in `.env` match database
- Verify database exists: `psql -l`

### Out of Memory Issues

**Problem**: System crashes when loading model

**Solution**:

- Use a smaller quantized model (Q4_K_M or Q3_K_M)
- Reduce `LLM_CONTEXT_SIZE` in `.env` to 2048
- Close other applications

### CORS Issues

**Problem**: Web app can't connect to API

**Solution**:

- Ensure both backend and frontend are running
- Check `CORS_ORIGINS` in `.env` includes your frontend URL
- Restart backend after changing `.env`

### Slow Responses

**Problem**: Queries take too long

**Solution**:

- Use GPU acceleration if available
- Use smaller, faster model
- Reduce `LLM_MAX_TOKENS` in `.env`
- Disable RAG for faster responses (toggle in UI)

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Use strong database password
- [ ] Enable HTTPS/TLS
- [ ] Restrict `CORS_ORIGINS` to specific domains
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Implement rate limiting
- [ ] Set up monitoring and logging

### Using Docker (Optional)

```bash
# Build and run with Docker Compose
docker-compose up -d
```

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Add more documents to the knowledge base
- Customize the prompts in `backend/models/llm_handler.py`
- Set up the desktop application (see Desktop Setup Guide)

## Support

For issues or questions:

- Check logs in `backend/logs/app.log`
- Review API documentation
- Check model compatibility

## License

Proprietary - For authorized use only
