#!/usr/bin/env python3
"""
Knowledge Base Ingestion Script
Processes documents and adds them to the ChromaDB vector store.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict
import asyncio

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from models.rag_engine import rag_engine
from loguru import logger


def load_markdown_file(file_path: str) -> List[Dict[str, str]]:
    """Load and chunk a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by headers to create chunks
    chunks = []
    current_chunk = ""
    current_heading = ""
    
    for line in content.split('\n'):
        if line.startswith('# '):
            # Main heading - start new document
            if current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'heading': current_heading,
                    'source': os.path.basename(file_path)
                })
            current_heading = line.replace('# ', '').strip()
            current_chunk = line + '\n'
        elif line.startswith('## ') or line.startswith('### '):
            # Sub-heading - create chunk
            if current_chunk and len(current_chunk) > 100:  # Minimum chunk size
                chunks.append({
                    'content': current_chunk.strip(),
                    'heading': current_heading,
                    'source': os.path.basename(file_path)
                })
            current_chunk = line + '\n'
        else:
            current_chunk += line + '\n'
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            'content': current_chunk.strip(),
            'heading': current_heading,
            'source': os.path.basename(file_path)
        })
    
    return chunks


def load_text_file(file_path: str) -> List[Dict[str, str]]:
    """Load a plain text file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Simple chunking by paragraphs
    paragraphs = content.split('\n\n')
    chunks = []
    
    for para in paragraphs:
        if para.strip() and len(para.strip()) > 50:
            chunks.append({
                'content': para.strip(),
                'heading': '',
                'source': os.path.basename(file_path)
            })
    
    return chunks


async def ingest_documents(sources_dir: str = "sources"):
    """Ingest all documents from sources directory."""
    logger.info("Starting knowledge base ingestion...")
    
    # Initialize RAG engine
    success = await rag_engine.initialize()
    if not success:
        logger.error("Failed to initialize RAG engine")
        return False
    
    # Get sources directory
    kb_dir = Path(__file__).parent
    sources_path = kb_dir / sources_dir
    
    if not sources_path.exists():
        logger.error(f"Sources directory not found: {sources_path}")
        return False
    
    # Process all files
    all_documents = []
    all_metadatas = []
    all_ids = []
    doc_count = 0
    
    for file_path in sources_path.glob("*"):
        if file_path.is_file():
            logger.info(f"Processing: {file_path.name}")
            
            try:
                if file_path.suffix == ".md":
                    chunks = load_markdown_file(str(file_path))
                elif file_path.suffix == ".txt":
                    chunks = load_text_file(str(file_path))
                else:
                    logger.warning(f"Unsupported file type: {file_path.suffix}")
                    continue
                
                # Add chunks to lists
                for chunk in chunks:
                    all_documents.append(chunk['content'])
                    all_metadatas.append({
                        'source': chunk['source'],
                        'heading': chunk['heading'],
                        'file_type': file_path.suffix
                    })
                    all_ids.append(f"{file_path.stem}_{doc_count}")
                    doc_count += 1
                
                logger.info(f"  → Extracted {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {str(e)}")
    
    # Add all documents to RAG engine
    if all_documents:
        logger.info(f"\nAdding {len(all_documents)} document chunks to knowledge base...")
        success = rag_engine.add_documents_batch(
            documents=all_documents,
            metadatas=all_metadatas,
            ids=all_ids
        )
        
        if success:
            logger.info("✓ Knowledge base ingestion complete!")
            logger.info(f"Total documents in collection: {rag_engine.collection.count()}")
            return True
        else:
            logger.error("Failed to add documents to knowledge base")
            return False
    else:
        logger.warning("No documents found to ingest")
        return False


async def test_search(query: str):
    """Test search functionality."""
    logger.info(f"\nTesting search with query: '{query}'")
    
    results = await rag_engine.search(query, top_k=3)
    
    logger.info(f"Found {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n--- Result {i} (Similarity: {result['similarity']:.3f}) ---")
        logger.info(f"Source: {result['metadata'].get('source', 'Unknown')}")
        logger.info(f"Content preview: {result['document'][:200]}...")


async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Knowledge Base Ingestion Tool")
    parser.add_argument("--reset", action="store_true", help="Reset collection before ingesting")
    parser.add_argument("--test", type=str, help="Test search with a query")
    
    args = parser.parse_args()
    
    if args.reset:
        logger.warning("Resetting knowledge base...")
        await rag_engine.initialize()
        rag_engine.reset_collection()
    
    # Ingest documents
    await ingest_documents()
    
    # Test search if requested
    if args.test:
        await test_search(args.test)


if __name__ == "__main__":
    asyncio.run(main())
