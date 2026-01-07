import os
import glob
from typing import List, Dict, Optional
from loguru import logger
from config import settings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class RAGEngine:
    """Retrieval Augmented Generation engine using TF-IDF (No models/No API keys)."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            ngram_range=(1, 2),
            max_df=0.8,
            min_df=1,
            sublinear_tf=True  # Apply sublinear tf scaling, i.e. replace tf with 1 + log(tf).
        )
        self.documents = []
        self.metadatas = []
        self.tfidf_matrix = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the TF-IDF engine by indexing local military knowledge base."""
        try:
            logger.info("Initializing Algorithm-based RAG engine (TF-IDF)...")
            
            # Load documents from knowledge-base sources
            kb_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "knowledge-base", "sources")
            if not os.path.exists(kb_path):
                logger.warning(f"Knowledge-base sources not found at {kb_path}")
                # Create a minimal document if missing to avoid failure
                self.add_document("VIRAAT Military AI: Advanced query resolution system for military decision-making.", {"source": "system"})
            else:
                md_files = glob.glob(os.path.join(kb_path, "*.md"))
                for file_path in md_files:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Simple chunking by paragraph or section
                        chunks = [c.strip() for c in content.split("\n\n") if len(c.strip()) > 50]
                        for chunk in chunks:
                            self.add_document(chunk, {"source": os.path.basename(file_path)})
            
            if self.documents:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
                self.is_initialized = True
                logger.info(f"✓ RAG engine initialized. Indexed {len(self.documents)} document chunks.")
            else:
                logger.warning("No documents found to index.")
                
            return True
            
        except Exception as e:
            logger.error(f"Error initializing RAG engine: {str(e)}")
            return False
    
    def add_document(self, document: str, metadata: Optional[Dict] = None):
        """Add a document chunk to the internal store."""
        self.documents.append(document)
        self.metadatas.append(metadata or {})
    
    def _expand_synonyms(self, query: str) -> str:
        """Expand query terms with military/general synonyms to improve recall."""
        synonym_map = {
            "gun": "gun weapon rifle firearm pistol arm",
            "guns": "guns weapons rifles firearms pistols arms",
            "soldier": "soldier personnel infantry troop",
            "communications": "communications comms signals radio",
            "tank": "tank armor vehicle mb",
            "plane": "plane aircraft jet fighter",
            "assemble": "assemble build construct setup maintenance",
            "how": "how procedure steps guide protocol"
        }
        
        words = query.lower().split()
        expanded_words = []
        for word in words:
            expanded_words.append(word)
            if word in synonym_map:
                expanded_words.append(synonym_map[word])
        
        return " ".join(expanded_words)
    
    def search(self, query: str, top_k: Optional[int] = None) -> List[Dict]:
        """Search for relevant documents using Cosine Similarity on TF-IDF vectors (Synchronous)."""
        try:
            if not self.is_initialized or not self.documents:
                logger.warning("RAG engine not initialized or empty during search")
                return []
            
            k = top_k or settings.rag_top_k
            
            # Expand query with synonyms
            expanded_query = self._expand_synonyms(query)
            logger.info(f"Original Query: '{query}' -> Expanded: '{expanded_query}'")

            # Generate query vector
            query_vec = self.vectorizer.transform([expanded_query])
            
            # Compute cosine similarity
            cosine_sim = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
            
            # Get top k indices
            top_indices = cosine_sim.argsort()[-k:][::-1]
            
            # Format results
            formatted_results = []
            if top_indices.size > 0:
                logger.info(f"Query: '{query}' - Max Sim: {cosine_sim[top_indices[0]]:.4f}")
            
            for idx in top_indices:
                similarity = float(cosine_sim[idx])
                
                # Log potential candidates for debugging
                if similarity > 0.01:
                    doc_preview = self.documents[idx][:50].replace('\n', ' ')
                    logger.debug(f"Candidate: {doc_preview}... (Score: {similarity:.4f})")

                # Filter by minimum similarity (Use settings)
                if similarity >= settings.rag_min_similarity: 
                    formatted_results.append({
                        'content': self.documents[idx], 
                        'metadata': self.metadatas[idx],
                        'similarity': similarity
                    })
            
            logger.info(f"Found {len(formatted_results)} relevant chunks for query using TF-IDF")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str, top_k: Optional[int] = None) -> str:
        """Get formatted context string for the decision engine."""
        # Search for relevant documents (Synchronous)
        results = self.search(query, top_k)
        
        if not results:
            return ""
        
        # Format context
        context_parts = []
        for i, result in enumerate(results, 1):
            content = result['content']
            similarity = result['similarity']
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'Unknown')
            
            context_parts.append(
                f"[Ref {i}: {source}, Relevance: {similarity:.2f}]\n{content}"
            )
        
        context = "\n\n".join(context_parts)
        return context
    
    def get_stats(self) -> Dict:
        """Get engine statistics."""
        return {
            "engine_type": "TF-IDF (No-Model)",
            "document_count": len(self.documents),
            "is_initialized": self.is_initialized
        }


# Global RAG engine instance
rag_engine = RAGEngine()
