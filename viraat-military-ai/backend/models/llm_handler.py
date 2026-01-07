from typing import Dict, List, Optional, AsyncIterator
import asyncio
from loguru import logger
from config import settings
from controllers.visual_controller import visual_controller
import random
import re
import json


class LLMHandler:
    """
    Algorithm-based 'Decision Engine' that mimics an LLM.
    Uses TF-IDF retrieval + Rule-based Response Generation.
    """
    
    def __init__(self):
        self.initialized = False
        
    async def initialize(self):
        """Initialize the Algorithm handler."""
        logger.info("🛠️  Algorithm-based AI handler initialized")
        self.initialized = True
        return True
    
    def _create_military_prompt(self, query: str, context: Optional[str] = None, 
                                conversation_history: Optional[List[Dict]] = None) -> str:
        """This is now a legacy method but kept for interface compatibility if needed."""
        return f"Query: {query}\nContext: {context}"
    
    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None,
        stream: bool = False
    ) -> str:
        """Generate response using the Decision Engine algorithm."""
        await asyncio.sleep(0.5) # Slight delay to feel like 'AI processing'
        
        if not context or len(context.strip()) < 10:
            return self._generate_fallback_response(query)
            
        return self._structure_context_response(query, context, conversation_history)
    
    def _structure_context_response(self, query: str, context: str, history: Optional[List[Dict]]) -> str:
        """Algorithmic response structuring with Persona and Visuals."""
        
        # 1. Analyze for Visual Intent
        visual_directive = visual_controller.analyze(query)
        visual_block = ""
        if visual_directive:
            # We encode the directive as a hidden JSON-like block or special marker for the frontend
            # Format: [VISUAL_DIRECTIVE: {"model_id": "..."}]
            visual_block = f"\n\n[VISUAL_DIRECTIVE: {json.dumps(visual_directive)}]\n"

        # Extract snippets from context (Refs)
        logger.info(f"LLMHandler Received Context ({len(context)} chars). Preview: {context[:100]}...")
        
        # Robust parsing: Split by "[Ref "
        refs = []
        if "[Ref " in context:
            parts = context.split("\n\n[Ref ")
            # Handle first part (which might be just "[Ref " if it starts with it)
            if context.startswith("[Ref "):
                parts[0] = parts[0][5:] # Remove initial "[Ref "
            
            for p in parts:
                # Format: "1: source, Relevance: 0.xx]\nContent"
                try:
                    meta_part, content_part = p.split("]\n", 1)
                    if "Relevance:" in meta_part:
                         # Extract source (everything before ", Relevance")
                         # Meta: "1: filename.md, Relevance: 0.50"
                         source_str = meta_part.split(", Relevance:")[0]
                         source = source_str.split(": ", 1)[1] if ": " in source_str else source_str
                         
                         rel_str = meta_part.split("Relevance: ")[1]
                         rel = float(rel_str)
                         
                         refs.append((source, rel, content_part))
                except Exception:
                    continue
        else:
            # Fallback for legacy format or single chunk
             refs = []

        # 2. Persona Engine: Generate Intro
        intro = self._generate_persona_intro(query, bool(refs))
        
        response = f"{intro}\n\n"
        
        if refs:
            response += "#### Key Intelligence Points:\n"
            
            # Helper to find best sentence
            def get_best_sentence(text, query):
                sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
                if not sentences: return text[:100] + "..."
                
                query_terms = set(re.findall(r'\w+', query.lower())) - {'what', 'are', 'is', 'the', 'a', 'an', 'in', 'on', 'of', 'to'}
                best_sent = sentences[0]
                max_score = 0
                
                for sent in sentences:
                    sent_lower = sent.lower()
                    score = sum(1 for term in query_terms if term in sent_lower)
                    if score > max_score:
                        max_score = score
                        best_sent = sent
                        
                return best_sent.strip()

            for source, rel, content in refs[:3]: # Top 3 points
                # Smart summary: Find sentence with most query terms
                best_sentence = get_best_sentence(content, query)
                response += f"- **{source}**: {best_sentence}\n"
            
            # Determine top score for dynamic filtering
            top_score = float(refs[0][1]) if refs else 0.0
            
            response += "\n#### Detailed Analysis:\n"
            
            seen_content = set()
            for source, rel, content in refs:
                current_score = float(rel)
                
                # Dynamic Filter: Ignore if score is less than 50% of best match
                # Dynamic Filter: Ignore if score is less than 80% of best match
                # Increased to 0.8 to Strictly remove "Report suspicious activity" when user asks for "Status report"
                if current_score < (top_score * 0.8):
                    continue
                    
                clean_content = content.strip()
                
                # Deduplication logic (check start of content)
                if clean_content[:50] not in seen_content:
                    response += f"**From {source}**:\n"
                    # Preserve formatting by just printing content
                    response += f"{clean_content}\n\n"
                    seen_content.add(clean_content[:50])
        else:
             response += self._generate_persona_fallback()
             
        # 3. Add Visual Directive (invisible to user, parsed by frontend)
        if visual_block:
            response += visual_block
            response += f"\n\n> *Commencing 3D Visualization for {visual_directive['model_name']}...*"

        return response

    def _generate_persona_intro(self, query: str, has_data: bool) -> str:
        """Generate a role-playing intro based on context."""
        if not has_data:
            return "Commander, my strategic assessment yielded no specific matches in the current database."
            
        intros = [
            f"Commander, I have analyzed the intelligence database regarding **'{query}'** and found the following:",
            f"Strategic Report: Analysis of **'{query}'** complete. Accessing classified directives:",
            f"VIRAAT System Active. Retrieving technical specifications for **'{query}'**:",
        ]
        return random.choice(intros)

    def _generate_persona_fallback(self) -> str:
        return "\n\nMy archives do not contain specific tactical data on this subject. Recommendation: Verify the terminology or request a broader strategic overview."

    def _generate_fallback_response(self, query: str) -> str:
        """Fallback response when no context is found."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["hello", "hi", "greet"]):
            return "Greetings. I am VIRAAT, your tactical AI assistant. How can I assist with military intelligence or protocols today?"
            
        if any(word in query_lower for word in ["who", "what are you"]):
            return "I am VIRAAT (Virtual Intelligence Reporting & Analysis Autonomous Tool). I operate using advanced retrieval algorithms to provide accurate military data without relying on external APIs or heavy models."

        return "VIRAAT Analysis: I could not find specific matches in the current knowledge base for your query. Please ensure your query contains relevant military terminology or check the knowledge base sources."

    async def generate_stream(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict]] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response using the Decision Engine."""
        full_response = await self.generate_response(query, context, conversation_history)
        
        # Simulate streaming by Yielding chunks
        words = full_response.split(" ")
        for i in range(0, len(words), 3):
            chunk = " ".join(words[i:i+3]) + " "
            yield chunk
            await asyncio.sleep(0.02)
    
    def get_model_info(self) -> Dict:
        """Get information about the 'model' (algorithm)."""
        return {
            "engine": "Decision Logic V1",
            "type": "Algorithmic/Heuristic",
            "is_loaded": self.initialized,
            "mock_mode": False
        }


# Global LLM handler instance
llm_handler = LLMHandler()
