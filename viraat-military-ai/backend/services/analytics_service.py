from typing import Optional
from sqlalchemy.orm import Session
from database.models import Analytics
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy import func


class AnalyticsService:
    """Service for tracking and analyzing usage."""
    
    @staticmethod
    def log_query(db: Session, user_id: Optional[int], query: str, 
                 response_time: float, model_used: str, 
                 tokens_used: Optional[int] = None,
                 rag_sources_used: Optional[int] = None) -> Analytics:
        """Log a query for analytics."""
        analytics = Analytics(
            user_id=user_id,
            query=query,
            response_time=response_time,
            model_used=model_used,
            tokens_used=tokens_used,
            rag_sources_used=rag_sources_used
        )
        
        db.add(analytics)
        db.commit()
        db.refresh(analytics)
        
        return analytics
    
    @staticmethod
    def get_total_queries(db: Session, user_id: Optional[int] = None) -> int:
        """Get total number of queries."""
        query = db.query(func.count(Analytics.id))
        
        if user_id:
            query = query.filter(Analytics.user_id == user_id)
        
        return query.scalar()
    
    @staticmethod
    def get_average_response_time(db: Session, user_id: Optional[int] = None) -> float:
        """Get average response time."""
        query = db.query(func.avg(Analytics.response_time))
        
        if user_id:
            query = query.filter(Analytics.user_id == user_id)
        
        result = query.scalar()
        return round(result, 2) if result else 0.0
    
    @staticmethod
    def get_popular_queries(db: Session, limit: int = 10, user_id: Optional[int] = None):
        """Get most common queries."""
        query = db.query(
            Analytics.query,
            func.count(Analytics.id).label('count')
        ).group_by(Analytics.query).order_by(func.count(Analytics.id).desc())
        
        if user_id:
            query = query.filter(Analytics.user_id == user_id)
        
        return query.limit(limit).all()
    
    @staticmethod
    def get_queries_by_timeframe(db: Session, days: int = 7, user_id: Optional[int] = None):
        """Get queries grouped by date for a timeframe."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = db.query(
            func.date(Analytics.created_at).label('date'),
            func.count(Analytics.id).label('count')
        ).filter(Analytics.created_at >= start_date).group_by(
            func.date(Analytics.created_at)
        ).order_by(func.date(Analytics.created_at))
        
        if user_id:
            query = query.filter(Analytics.user_id == user_id)
        
        return query.all()
    
    @staticmethod
    def get_rag_usage_stats(db: Session, user_id: Optional[int] = None):
        """Get statistics on RAG usage."""
        query = db.query(Analytics).filter(Analytics.rag_sources_used > 0)
        
        if user_id:
            query = query.filter(Analytics.user_id == user_id)
        
        total_with_rag = query.count()
        avg_sources = db.query(func.avg(Analytics.rag_sources_used)).filter(
            Analytics.rag_sources_used > 0
        )
        
        if user_id:
            avg_sources = avg_sources.filter(Analytics.user_id == user_id)
        
        avg = avg_sources.scalar()
        
        return {
            'queries_with_rag': total_with_rag,
            'average_sources': round(avg, 2) if avg else 0.0
        }
    
    @staticmethod
    def get_dashboard_stats(db: Session, user_id: Optional[int] = None):
        """Get comprehensive dashboard statistics."""
        return {
            'total_queries': AnalyticsService.get_total_queries(db, user_id),
            'average_response_time': AnalyticsService.get_average_response_time(db, user_id),
            'popular_queries': AnalyticsService.get_popular_queries(db, 5, user_id),
            'queries_last_7_days': AnalyticsService.get_queries_by_timeframe(db, 7, user_id),
            'rag_stats': AnalyticsService.get_rag_usage_stats(db, user_id)
        }


# Global analytics service instance
analytics_service = AnalyticsService()
