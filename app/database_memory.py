"""
In-memory database for MVP testing.
Replaces Supabase with a simple Python dictionary-based storage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import json
import logging

logger = logging.getLogger(__name__)


class InMemoryDB:
    """
    In-memory database using Python dictionaries.
    Simulates Supabase table operations.
    """
    
    def __init__(self):
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.claim_events: Dict[str, List[Dict[str, Any]]] = {}
        self.documents: Dict[str, List[Dict[str, Any]]] = {}
        self.users: Dict[str, Dict[str, Any]] = {}  # For auth simulation
        logger.info("In-memory database initialized")
    
    def reset(self):
        """Reset all data (useful for testing)."""
        self.incidents.clear()
        self.claim_events.clear()
        self.documents.clear()
        self.users.clear()
        logger.info("In-memory database reset")
    
    def create_user(self, user_id: str, email: str = None):
        """Create a test user."""
        self.users[user_id] = {
            "id": user_id,
            "email": email or f"{user_id}@test.com",
            "created_at": datetime.utcnow().isoformat()
        }
        return self.users[user_id]


class InMemoryTable:
    """
    Simulates a Supabase table with in-memory operations.
    """
    
    def __init__(self, db: InMemoryDB, table_name: str):
        self.db = db
        self.table_name = table_name
    
    def insert(self, data: Dict[str, Any]) -> 'InMemoryQueryBuilder':
        """Insert data into table."""
        if isinstance(data, dict):
            data = [data]
        
        results = []
        for item in data:
            # Generate ID if not provided
            if "id" not in item:
                item["id"] = str(uuid.uuid4())
            
            # Set timestamps
            if "created_at" not in item:
                item["created_at"] = datetime.utcnow().isoformat()
            if "updated_at" not in item:
                item["updated_at"] = datetime.utcnow().isoformat()
            
            # Store based on table name
            if self.table_name == "incidents":
                self.db.incidents[item["id"]] = item.copy()
                results.append(item)
            elif self.table_name == "claim_events":
                incident_id = item.get("incident_id")
                if incident_id not in self.db.claim_events:
                    self.db.claim_events[incident_id] = []
                self.db.claim_events[incident_id].append(item)
                results.append(item)
            elif self.table_name == "documents":
                incident_id = item.get("incident_id")
                if incident_id not in self.db.documents:
                    self.db.documents[incident_id] = []
                self.db.documents[incident_id].append(item)
                results.append(item)
        
        # Return mock result object
        mock_result = type('Result', (), {
            'data': results,
            'execute': lambda self: self
        })()
        return InMemoryQueryBuilder(self.db, self.table_name, results)
    
    def select(self, columns: str = "*") -> 'InMemoryQueryBuilder':
        """Select from table."""
        return InMemoryQueryBuilder(self.db, self.table_name)
    
    def update(self, data: Dict[str, Any]) -> 'InMemoryQueryBuilder':
        """Update table records."""
        return InMemoryQueryBuilder(self.db, self.table_name, update_data=data)


class InMemoryQueryBuilder:
    """
    Query builder for in-memory database operations.
    Simulates Supabase query chaining.
    """
    
    def __init__(self, db: InMemoryDB, table_name: str, initial_data: List = None, update_data: Dict = None):
        self.db = db
        self.table_name = table_name
        self.filters = []
        self.order_by_field = None
        self.order_desc = False
        self.update_data = update_data
        self.initial_data = initial_data or []
    
    def eq(self, column: str, value: Any) -> 'InMemoryQueryBuilder':
        """Add equality filter."""
        self.filters.append(("eq", column, value))
        return self
    
    def order(self, column: str) -> 'InMemoryQueryBuilder':
        """Order by column."""
        self.order_by_field = column
        return self
    
    def execute(self) -> 'InMemoryResult':
        """Execute query and return results."""
        # Get data based on table
        if self.table_name == "incidents":
            data = list(self.db.incidents.values())
        elif self.table_name == "claim_events":
            # Flatten all events
            data = []
            for events_list in self.db.claim_events.values():
                data.extend(events_list)
        elif self.table_name == "documents":
            # Flatten all documents
            data = []
            for docs_list in self.db.documents.values():
                data.extend(docs_list)
        else:
            data = []
        
        # Apply filters
        for filter_type, column, value in self.filters:
            if filter_type == "eq":
                data = [item for item in data if item.get(column) == value]
        
        # Apply ordering
        if self.order_by_field:
            data.sort(key=lambda x: x.get(self.order_by_field, ""), reverse=self.order_desc)
        
        # Handle updates
        if self.update_data:
            for item in data:
                item.update(self.update_data)
                if "updated_at" not in self.update_data:
                    item["updated_at"] = datetime.utcnow().isoformat()
                # Update stored data
                if self.table_name == "incidents" and "id" in item:
                    self.db.incidents[item["id"]] = item
        
        return InMemoryResult(data)


class InMemoryResult:
    """Mock result object similar to Supabase response."""
    
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data


# Global in-memory database instance
_memory_db: Optional[InMemoryDB] = None


def get_memory_db() -> InMemoryDB:
    """Get or create in-memory database instance."""
    global _memory_db
    if _memory_db is None:
        _memory_db = InMemoryDB()
    return _memory_db


def get_memory_client():
    """Get in-memory client that mimics Supabase client."""
    db = get_memory_db()
    
    class MemoryClient:
        def table(self, table_name: str):
            return InMemoryTable(db, table_name)
    
    return MemoryClient()
