from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import timedelta
import time
from loguru import logger

from config import settings
from database.models import get_db, init_db, User
from models.llm_handler import llm_handler
from models.rag_engine import rag_engine
from services.auth_service import auth_service
from services.conversation_service import conversation_service
from services.analytics_service import analytics_service

# Initialize FastAPI app
app = FastAPI(
    title="VIRAAT Military AI Assistant",
    description="Advanced AI-powered query resolution system for military decision-making",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# ==================== Pydantic Models ====================

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[int] = None
    use_rag: bool = True
    stream: bool = False

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: str

# ==================== Helper Functions ====================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), 
                          db: Session = Depends(get_db)) -> User:
    """Get current authenticated user."""
    token = credentials.credentials
    
    # Support mock guest token for development
    is_dev = settings.environment.lower() == "development"
    logger.debug(f"Auth check: token='{token}', is_dev={is_dev}")
    
    if token == "guest_token_mock" and is_dev:
        guest_user = auth_service.get_user(db, "guest_warrior")
        if not guest_user:
            logger.info("Creating mock guest user")
            guest_user = auth_service.create_user(
                db, 
                username="guest_warrior", 
                email="guest@viraat.ai", 
                password="guest_password_secure_123",
                full_name="Guest Personnel",
                role="guest"
            )
        return guest_user

    payload = auth_service.decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = auth_service.get_user(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# ==================== Routes ====================

@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_initialized": llm_handler.mock_mode or llm_handler.llm is not None,
        "rag_initialized": True
    }

@app.post("/api/v1/auth/register", response_model=Token)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """User registration endpoint."""
    if auth_service.get_user(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if auth_service.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = auth_service.create_user(
        db, 
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name
    )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name, "role": user.role}
    }

@app.post("/api/v1/auth/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint."""
    user = auth_service.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Incorrect username or password"
        )
    
    access_token = auth_service.create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name, "role": user.role}
    }

@app.get("/api/v1/conversations")
async def get_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all conversations for the current user."""
    return conversation_service.get_user_conversations(db, current_user.id)

@app.post("/api/v1/conversations")
async def create_conversation(conv_data: ConversationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Create a new conversation."""
    return conversation_service.create_conversation(db, current_user.id, conv_data.title)

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Delete a conversation."""
    success = conversation_service.delete_conversation(db, conversation_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success"}

@app.patch("/api/v1/conversations/{conversation_id}")
async def update_conversation(conversation_id: int, conv_data: ConversationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update conversation title."""
    conversation = conversation_service.update_conversation_title(db, conversation_id, current_user.id, conv_data.title)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation

@app.get("/api/v1/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all messages in a conversation."""
    return conversation_service.get_conversation_messages(db, conversation_id)

@app.post("/api/v1/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Chat endpoint for AI response."""
    start_time = time.time()
    
    # Get conversation context
    history = []
    if request.conversation_id:
        history = conversation_service.get_conversation_history(db, request.conversation_id)
    
    # RAG lookup if requested
    context = ""
    sources_count = 0
    if request.use_rag:
        # rag_results = rag_engine.search(request.query) # Deprecated direct call
        context = rag_engine.get_context_for_query(request.query)
        # sources_count is roughly number of refs, but we can't easily get it from string. 
        # For analytics, we can do a quick count or just search again if needed, 
        # but better to just count the refs in string.
        sources_count = context.count("[Ref ")
    
    # Get LLM response
    response_text = await llm_handler.generate_response(request.query, context, history)
    
    # Extract visual directive (backend now produces structured JSON)
    visual_directive = None
    
    # Check if response contains visual marker (legacy support)
    if "[VISUAL_DIRECTIVE:" in response_text:
        marker_idx = response_text.index("[VISUAL_DIRECTIVE:")
        end_idx = response_text.rfind("]")
        if end_idx > marker_idx:
            try:
                import json as json_module
                json_str = response_text[marker_idx+17:end_idx]
                visual_directive = json_module.loads(json_str)
                response_text = response_text[:marker_idx].strip()
            except Exception:
                pass
    
    # Alternatively, analyze query for visual intent
    if not visual_directive:
        visual_intent = visual_controller.analyze(request.query)
        if visual_intent:
            visual_directive = visual_intent
    
    # Log user message
    if request.conversation_id:
        conversation_service.add_message(db, request.conversation_id, "user", request.query)
        conversation_service.add_message(db, request.conversation_id, "assistant", response_text)
    
    # Log analytics
    response_time = time.time() - start_time
    analytics_service.log_query(
        db, 
        current_user.id, 
        request.query, 
        response_time, 
        settings.llm_model_path,
        rag_sources_used=sources_count
    )
    
    return {
        "response": response_text,
        "sources_count": sources_count,
        "visual_directive": visual_directive
    }

@app.get("/api/v1/analytics/dashboard")
async def get_analytics(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get analytics dashboard stats."""
    # Allow all users to see their own stats, or admin to see everything
    user_id = None if current_user.role == "admin" else current_user.id
    return analytics_service.get_dashboard_stats(db, user_id)

@app.on_event("startup")
async def startup_event():
    init_db()
    await llm_handler.initialize()
    await rag_engine.initialize()
    logger.info("Application started, database initialized, and LLM model loaded")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
