"""
RAG System Module
Handles document processing, embedding generation, and retrieval using ChromaDB.
Supports PDF, DOCX, TXT, and CSV files.
"""

import os
import hashlib
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

# Document loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document


# ChromaDB storage path
CHROMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "chroma_db")


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    content: str
    source: str
    page: int
    chunk_id: str


@dataclass
class RetrievalResult:
    """Result from a retrieval query."""
    content: str
    source: str
    score: float
    metadata: Dict


class RAGSystem:
    """
    Retrieval-Augmented Generation system using ChromaDB.
    Handles document ingestion, embedding, and retrieval.
    """
    
    def __init__(self, embeddings, collection_name: str = "default"):
        """
        Initialize the RAG system.
        
        Args:
            embeddings: LangChain embeddings instance (from Ollama)
            collection_name: Name for the ChromaDB collection
        """
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.chroma_path = CHROMA_PATH
        
        # Ensure storage directory exists
        os.makedirs(self.chroma_path, exist_ok=True)
        
        # Initialize or load the vector store
        self.vectorstore = self._init_vectorstore()
        
        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def _init_vectorstore(self) -> Chroma:
        """Initialize or load the ChromaDB vector store."""
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.chroma_path
        )
    
    def _get_file_hash(self, file_path: str) -> str:
        """Generate a hash for a file to detect duplicates."""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    
    def _load_document(self, file_path: str) -> List[Document]:
        """
        Load a document based on its file type.
        
        Args:
            file_path: Path to the document
            
        Returns:
            List of Document objects
        """
        ext = os.path.splitext(file_path)[1].lower()
        
        loaders = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.txt': TextLoader,
            '.csv': CSVLoader
        }
        
        if ext not in loaders:
            raise ValueError(f"Unsupported file type: {ext}")
        
        loader = loaders[ext](file_path)
        return loader.load()
    
    def add_document(self, file_path: str, agent_id: str = None) -> Dict:
        """
        Add a document to the knowledge base.
        
        Args:
            file_path: Path to the document
            agent_id: Optional agent ID to associate with the document
            
        Returns:
            Dict with processing results
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load the document
        documents = self._load_document(file_path)
        
        # Add metadata
        file_hash = self._get_file_hash(file_path)
        file_name = os.path.basename(file_path)
        
        for doc in documents:
            doc.metadata.update({
                "source": file_name,
                "file_path": file_path,
                "file_hash": file_hash,
                "agent_id": agent_id or "global"
            })
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vectorstore.add_documents(chunks)
        
        return {
            "file_name": file_name,
            "chunks_created": len(chunks),
            "file_hash": file_hash
        }
    
    def add_text(self, text: str, source: str = "user_input", 
                 agent_id: str = None) -> Dict:
        """
        Add raw text to the knowledge base.
        
        Args:
            text: Text content to add
            source: Source identifier
            agent_id: Optional agent ID
            
        Returns:
            Dict with processing results
        """
        # Create a document from text
        doc = Document(
            page_content=text,
            metadata={
                "source": source,
                "agent_id": agent_id or "global"
            }
        )
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        
        # Add to vector store
        self.vectorstore.add_documents(chunks)
        
        return {
            "source": source,
            "chunks_created": len(chunks)
        }
    
    def query(self, query: str, k: int = 5, 
              agent_id: str = None) -> List[RetrievalResult]:
        """
        Query the knowledge base for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            agent_id: Filter by agent ID if provided
            
        Returns:
            List of RetrievalResult objects
        """
        # Build filter if agent_id specified
        filter_dict = None
        if agent_id:
            filter_dict = {"agent_id": {"$in": [agent_id, "global"]}}
        
        # Perform similarity search with scores
        results = self.vectorstore.similarity_search_with_score(
            query, 
            k=k,
            filter=filter_dict
        )
        
        retrieval_results = []
        for doc, score in results:
            retrieval_results.append(RetrievalResult(
                content=doc.page_content,
                source=doc.metadata.get("source", "unknown"),
                score=float(score),
                metadata=doc.metadata
            ))
        
        return retrieval_results
    
    def get_context(self, query: str, k: int = 3, 
                    agent_id: str = None) -> str:
        """
        Get formatted context for LLM prompts.
        
        Args:
            query: Search query
            k: Number of documents to include
            agent_id: Filter by agent ID
            
        Returns:
            Formatted context string
        """
        results = self.query(query, k=k, agent_id=agent_id)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {result.source}]\n{result.content}"
            )
        
        return "\n\n---\n\n".join(context_parts)
    
    def delete_document(self, file_hash: str):
        """
        Delete a document by its hash.
        
        Args:
            file_hash: The hash of the file to delete
        """
        # Get all documents with this hash
        # Note: ChromaDB doesn't support direct deletion by metadata,
        # so we need to recreate the collection without these docs
        # This is a simplified implementation
        pass  # TODO: Implement proper deletion
    
    def list_documents(self, agent_id: str = None) -> List[Dict]:
        """
        List all documents in the knowledge base.
        
        Args:
            agent_id: Filter by agent ID
            
        Returns:
            List of document metadata
        """
        # Get collection
        collection = self.vectorstore._collection
        
        # Get all documents
        results = collection.get()
        
        # Extract unique sources
        sources = {}
        for i, metadata in enumerate(results.get("metadatas", [])):
            source = metadata.get("source", "unknown")
            if agent_id and metadata.get("agent_id") not in [agent_id, "global"]:
                continue
            if source not in sources:
                sources[source] = {
                    "source": source,
                    "agent_id": metadata.get("agent_id"),
                    "chunk_count": 1
                }
            else:
                sources[source]["chunk_count"] += 1
        
        return list(sources.values())
    
    def clear_collection(self, agent_id: str = None):
        """
        Clear all documents from the collection.
        
        Args:
            agent_id: If provided, only clear documents for this agent
        """
        if agent_id:
            # Would need to filter and delete specific documents
            pass
        else:
            # Clear entire collection
            self.vectorstore.delete_collection()
            self.vectorstore = self._init_vectorstore()


class RAGRetriever:
    """
    LangChain-compatible retriever wrapper for the RAG system.
    """
    
    def __init__(self, rag_system: RAGSystem, agent_id: str = None, k: int = 3):
        """
        Initialize the retriever.
        
        Args:
            rag_system: The RAG system instance
            agent_id: Optional agent ID filter
            k: Number of documents to retrieve
        """
        self.rag_system = rag_system
        self.agent_id = agent_id
        self.k = k
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The search query
            
        Returns:
            List of Document objects
        """
        results = self.rag_system.query(query, k=self.k, agent_id=self.agent_id)
        
        documents = []
        for result in results:
            documents.append(Document(
                page_content=result.content,
                metadata={"source": result.source, "score": result.score}
            ))
        
        return documents
    
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        """Async version of get_relevant_documents."""
        return self.get_relevant_documents(query)
