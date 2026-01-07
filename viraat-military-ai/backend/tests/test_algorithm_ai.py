import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from models.rag_engine import rag_engine
from models.llm_handler import llm_handler

async def test_ai_flow():
    print("🚀 Starting Algorithm-based AI Verification...")
    
    # 1. Initialize RAG
    print("\n--- 1. Testing RAG Initialization ---")
    initialized = await rag_engine.initialize()
    print(f"RAG Initialized: {initialized}")
    stats = rag_engine.get_stats()
    print(f"Stats: {stats}")
    
    # 2. Test Search
    print("\n--- 2. Testing Search (Military Communications) ---")
    query = "What are military communications?"
    results = rag_engine.search(query)
    print(f"Found {len(results)} results")
    if results:
        print(f"Top Result Content Sample: {results[0]['content'][:100]}...")
        print(f"Similarity: {results[0]['similarity']:.4f}")
    
    # 3. Test Response Generation
    print("\n--- 3. Testing Response Generation ---")
    await llm_handler.initialize()
    context = rag_engine.get_context_for_query(query)
    response = await llm_handler.generate_response(query, context)
    print("Response Generated:")
    print("-" * 30)
    print(response)
    print("-" * 30)
    
    # 4. Test Streaming
    print("\n--- 4. Testing Streaming ---")
    print("Stream: ", end="", flush=True)
    async for chunk in llm_handler.generate_stream(query, context):
        print(chunk, end="", flush=True)
    print("\n")
    
    print("✅ Verification Complete!")

if __name__ == "__main__":
    asyncio.run(test_ai_flow())
