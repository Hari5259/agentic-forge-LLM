"""
Memory Manager Module
Handles persistent storage of conversations, agent states, and actions using SQLite.
Provides long-term memory capabilities for agents.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager


# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "memory.db")


@dataclass
class Conversation:
    """Represents a conversation entry."""
    id: Optional[int]
    agent_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    metadata: Dict


@dataclass 
class AgentState:
    """Represents an agent's persistent state."""
    agent_id: str
    agent_name: str
    agent_type: str
    config: Dict
    created_at: str
    last_active: str
    is_active: bool


@dataclass
class ActionLog:
    """Represents an action performed by an agent."""
    id: Optional[int]
    agent_id: str
    action_type: str
    action_data: Dict
    result: str
    timestamp: str


class MemoryManager:
    """
    Manages persistent memory for agents using SQLite.
    Stores conversations, agent states, and action logs.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the memory manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or DB_PATH
        self._ensure_db_exists()
        self._init_database()
    
    def _ensure_db_exists(self):
        """Ensure the database directory exists."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Agents table - stores agent configurations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT NOT NULL,
                    agent_type TEXT NOT NULL,
                    config TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1
                )
            """)
            
            # Conversations table - stores chat history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            """)
            
            # Action logs table - stores agent actions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    action_data TEXT DEFAULT '{}',
                    result TEXT,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            """)
            
            # Knowledge sources table - tracks uploaded documents
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    file_path TEXT,
                    chunk_count INTEGER DEFAULT 0,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents (agent_id)
                )
            """)
            
            # Usage patterns table - for proactive suggestions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS usage_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_type TEXT NOT NULL,
                    pattern_data TEXT NOT NULL,
                    frequency INTEGER DEFAULT 1,
                    last_seen TEXT NOT NULL
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_conv_agent ON conversations(agent_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_actions_agent ON action_logs(agent_id)")
    
    # ==================== Agent Management ====================
    
    def save_agent(self, agent: AgentState) -> str:
        """
        Save or update an agent's state.
        
        Args:
            agent: AgentState object to save
            
        Returns:
            The agent_id
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agents 
                (agent_id, agent_name, agent_type, config, created_at, last_active, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                agent.agent_id,
                agent.agent_name,
                agent.agent_type,
                json.dumps(agent.config),
                agent.created_at,
                agent.last_active,
                1 if agent.is_active else 0
            ))
        return agent.agent_id
    
    def get_agent(self, agent_id: str) -> Optional[AgentState]:
        """Retrieve an agent by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                return AgentState(
                    agent_id=row["agent_id"],
                    agent_name=row["agent_name"],
                    agent_type=row["agent_type"],
                    config=json.loads(row["config"]),
                    created_at=row["created_at"],
                    last_active=row["last_active"],
                    is_active=bool(row["is_active"])
                )
        return None
    
    def list_agents(self, active_only: bool = True) -> List[AgentState]:
        """List all agents."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM agents"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY last_active DESC"
            cursor.execute(query)
            
            agents = []
            for row in cursor.fetchall():
                agents.append(AgentState(
                    agent_id=row["agent_id"],
                    agent_name=row["agent_name"],
                    agent_type=row["agent_type"],
                    config=json.loads(row["config"]),
                    created_at=row["created_at"],
                    last_active=row["last_active"],
                    is_active=bool(row["is_active"])
                ))
            return agents
    
    def delete_agent(self, agent_id: str):
        """Mark an agent as inactive (soft delete)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE agents SET is_active = 0 WHERE agent_id = ?",
                (agent_id,)
            )
    
    def update_agent_activity(self, agent_id: str):
        """Update the last_active timestamp for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE agents SET last_active = ? WHERE agent_id = ?",
                (datetime.now().isoformat(), agent_id)
            )
    
    # ==================== Conversation Management ====================
    
    def save_message(self, agent_id: str, role: str, content: str, 
                     metadata: Dict = None) -> int:
        """
        Save a conversation message.
        
        Args:
            agent_id: The agent's ID
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata dict
            
        Returns:
            The message ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (agent_id, role, content, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (
                agent_id,
                role,
                content,
                datetime.now().isoformat(),
                json.dumps(metadata or {})
            ))
            return cursor.lastrowid
    
    def get_conversation_history(self, agent_id: str, limit: int = 50) -> List[Conversation]:
        """Get recent conversation history for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM conversations 
                WHERE agent_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (agent_id, limit))
            
            messages = []
            for row in cursor.fetchall():
                messages.append(Conversation(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    role=row["role"],
                    content=row["content"],
                    timestamp=row["timestamp"],
                    metadata=json.loads(row["metadata"])
                ))
            return list(reversed(messages))  # Return in chronological order
    
    def get_conversation_context(self, agent_id: str, num_messages: int = 10) -> str:
        """Get formatted conversation context for LLM prompts."""
        history = self.get_conversation_history(agent_id, num_messages)
        context = []
        for msg in history:
            role = "Human" if msg.role == "user" else "Assistant"
            context.append(f"{role}: {msg.content}")
        return "\n".join(context)
    
    def clear_conversation(self, agent_id: str):
        """Clear all conversations for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM conversations WHERE agent_id = ?", (agent_id,))
    
    # ==================== Action Logging ====================
    
    def log_action(self, agent_id: str, action_type: str, 
                   action_data: Dict, result: str) -> int:
        """Log an action performed by an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO action_logs (agent_id, action_type, action_data, result, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                agent_id,
                action_type,
                json.dumps(action_data),
                result,
                datetime.now().isoformat()
            ))
            return cursor.lastrowid
    
    def get_action_history(self, agent_id: str, limit: int = 20) -> List[ActionLog]:
        """Get recent actions for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM action_logs 
                WHERE agent_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (agent_id, limit))
            
            actions = []
            for row in cursor.fetchall():
                actions.append(ActionLog(
                    id=row["id"],
                    agent_id=row["agent_id"],
                    action_type=row["action_type"],
                    action_data=json.loads(row["action_data"]),
                    result=row["result"],
                    timestamp=row["timestamp"]
                ))
            return actions
    
    # ==================== Knowledge Sources ====================
    
    def save_knowledge_source(self, agent_id: str, source_name: str, 
                              source_type: str, file_path: str, chunk_count: int):
        """Record a knowledge source added to an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_sources 
                (agent_id, source_name, source_type, file_path, chunk_count, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                agent_id,
                source_name,
                source_type,
                file_path,
                chunk_count,
                datetime.now().isoformat()
            ))
    
    def get_knowledge_sources(self, agent_id: str) -> List[Dict]:
        """Get all knowledge sources for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM knowledge_sources WHERE agent_id = ?",
                (agent_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Usage Patterns ====================
    
    def record_pattern(self, pattern_type: str, pattern_data: str):
        """Record a usage pattern for proactive suggestions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute("""
                SELECT id, frequency FROM usage_patterns 
                WHERE pattern_type = ? AND pattern_data = ?
            """, (pattern_type, pattern_data))
            
            row = cursor.fetchone()
            if row:
                # Update frequency
                cursor.execute("""
                    UPDATE usage_patterns 
                    SET frequency = ?, last_seen = ?
                    WHERE id = ?
                """, (row["frequency"] + 1, datetime.now().isoformat(), row["id"]))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO usage_patterns (pattern_type, pattern_data, frequency, last_seen)
                    VALUES (?, ?, 1, ?)
                """, (pattern_type, pattern_data, datetime.now().isoformat()))
    
    def get_frequent_patterns(self, min_frequency: int = 3) -> List[Dict]:
        """Get frequently occurring patterns for suggestions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM usage_patterns 
                WHERE frequency >= ?
                ORDER BY frequency DESC
                LIMIT 10
            """, (min_frequency,))
            return [dict(row) for row in cursor.fetchall()]
    
    # ==================== Statistics ====================
    
    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get statistics for an agent."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Count conversations
            cursor.execute(
                "SELECT COUNT(*) as count FROM conversations WHERE agent_id = ?",
                (agent_id,)
            )
            conv_count = cursor.fetchone()["count"]
            
            # Count actions
            cursor.execute(
                "SELECT COUNT(*) as count FROM action_logs WHERE agent_id = ?",
                (agent_id,)
            )
            action_count = cursor.fetchone()["count"]
            
            # Count knowledge sources
            cursor.execute(
                "SELECT COUNT(*) as count FROM knowledge_sources WHERE agent_id = ?",
                (agent_id,)
            )
            knowledge_count = cursor.fetchone()["count"]
            
            return {
                "conversations": conv_count,
                "actions": action_count,
                "knowledge_sources": knowledge_count
            }
