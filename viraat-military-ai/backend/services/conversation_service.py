from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from database.models import Conversation, Message
from datetime import datetime
from loguru import logger


class ConversationService:
    """Service for managing conversations and messages."""
    
    @staticmethod
    def create_conversation(db: Session, user_id: int, title: Optional[str] = None) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            user_id=user_id,
            title=title or f"Conversation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        
        logger.info(f"Created conversation {conversation.id} for user {user_id}")
        return conversation
    
    @staticmethod
    def get_conversation(db: Session, conversation_id: int, user_id: int) -> Optional[Conversation]:
        """Get a conversation by ID."""
        return db.query(Conversation).filter(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        ).first()
    
    @staticmethod
    def get_user_conversations(db: Session, user_id: int, limit: int = 50) -> List[Conversation]:
        """Get all conversations for a user."""
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).limit(limit).all()
    
    @staticmethod
    def update_conversation_title(db: Session, conversation_id: int, user_id: int, 
                                 title: str) -> Optional[Conversation]:
        """Update conversation title."""
        conversation = ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return None
        
        conversation.title = title
        db.commit()
        db.refresh(conversation)
        
        return conversation
    
    @staticmethod
    def delete_conversation(db: Session, conversation_id: int, user_id: int) -> bool:
        """Delete a conversation."""
        conversation = ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        
        db.delete(conversation)
        db.commit()
        
        logger.info(f"Deleted conversation {conversation_id}")
        return True
    
    @staticmethod
    def add_message(db: Session, conversation_id: int, role: str, 
                   content: str, metadata: Optional[Dict] = None) -> Message:
        """Add a message to a conversation."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Update conversation's updated_at
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()
            db.commit()
        
        return message
    
    @staticmethod
    def get_conversation_messages(db: Session, conversation_id: int, 
                                 limit: Optional[int] = None) -> List[Message]:
        """Get all messages in a conversation."""
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    @staticmethod
    def get_conversation_history(db: Session, conversation_id: int, 
                                max_messages: int = 10) -> List[Dict]:
        """Get conversation history formatted for LLM context."""
        messages = ConversationService.get_conversation_messages(
            db, conversation_id, limit=max_messages
        )
        
        history = []
        for msg in messages:
            history.append({
                'role': msg.role,
                'content': msg.content
            })
        
        return history
    
    @staticmethod
    def clear_conversation_messages(db: Session, conversation_id: int, user_id: int) -> bool:
        """Clear all messages in a conversation."""
        conversation = ConversationService.get_conversation(db, conversation_id, user_id)
        if not conversation:
            return False
        
        db.query(Message).filter(Message.conversation_id == conversation_id).delete()
        db.commit()
        
        logger.info(f"Cleared messages in conversation {conversation_id}")
        return True


# Global conversation service instance
conversation_service = ConversationService()
