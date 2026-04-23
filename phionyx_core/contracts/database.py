"""
Database Access Contracts
==========================
Protocols/interfaces for database access in phionyx_core.

Core modules should depend on these protocols, not on concrete database implementations.
Implementations should be provided by phionyx_bridge.
"""

from typing import Protocol, Optional, List, Dict, Any
from abc import ABC, abstractmethod


class MemoryRepositoryProtocol(Protocol):
    """Protocol for memory storage operations."""

    def insert_memory(self, memory_data: Dict[str, Any]) -> Optional[str]:
        """Insert a memory record. Returns memory ID if successful."""
        ...

    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        ...

    def search_memories(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search memories by query criteria."""
        ...

    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory record. Returns True if successful."""
        ...

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record. Returns True if successful."""
        ...


class GraphRepositoryProtocol(Protocol):
    """Protocol for graph/concept storage operations."""

    def get_concepts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all concepts for a user."""
        ...

    def get_associations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all associations for a user."""
        ...

    def insert_concept(self, concept_data: Dict[str, Any]) -> Optional[str]:
        """Insert a concept. Returns concept ID if successful."""
        ...

    def insert_association(self, association_data: Dict[str, Any]) -> Optional[str]:
        """Insert an association. Returns association ID if successful."""
        ...

    def insert_chronicle_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Insert a chronicle event. Returns event ID if successful."""
        ...

    def get_chronicle_events(self, character_id: str) -> List[Dict[str, Any]]:
        """Get chronicle events for a character."""
        ...


class UserProfileRepositoryProtocol(Protocol):
    """Protocol for user profile storage operations."""

    def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get a character by ID."""
        ...

    def get_user_characters(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all characters for a user."""
        ...

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user profile."""
        ...

    def get_game_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get game sessions for a user."""
        ...

    def insert_game_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Insert a game session. Returns session ID if successful."""
        ...

    def insert_game_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Insert a game log. Returns log ID if successful."""
        ...

    def get_echoes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get echoes for a user."""
        ...


class AuditRepositoryProtocol(Protocol):
    """Protocol for audit log storage operations."""

    def log_pedagogy_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a pedagogy audit event. Returns True if successful."""
        ...

    def log_safety_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a safety audit event. Returns True if successful."""
        ...


# Abstract base classes for type checking and documentation

class MemoryRepository(ABC):
    """Abstract base class for memory repository implementations."""

    @abstractmethod
    def insert_memory(self, memory_data: Dict[str, Any]) -> Optional[str]:
        """Insert a memory record. Returns memory ID if successful."""
        pass

    @abstractmethod
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a memory by ID."""
        pass

    @abstractmethod
    def search_memories(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search memories by query criteria."""
        pass

    @abstractmethod
    def update_memory(self, memory_id: str, updates: Dict[str, Any]) -> bool:
        """Update a memory record. Returns True if successful."""
        pass

    @abstractmethod
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory record. Returns True if successful."""
        pass


class GraphRepository(ABC):
    """Abstract base class for graph repository implementations."""

    @abstractmethod
    def get_concepts(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all concepts for a user."""
        pass

    @abstractmethod
    def get_associations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all associations for a user."""
        pass

    @abstractmethod
    def insert_concept(self, concept_data: Dict[str, Any]) -> Optional[str]:
        """Insert a concept. Returns concept ID if successful."""
        pass

    @abstractmethod
    def insert_association(self, association_data: Dict[str, Any]) -> Optional[str]:
        """Insert an association. Returns association ID if successful."""
        pass

    @abstractmethod
    def insert_chronicle_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """Insert a chronicle event. Returns event ID if successful."""
        pass

    @abstractmethod
    def get_chronicle_events(self, character_id: str) -> List[Dict[str, Any]]:
        """Get chronicle events for a character."""
        pass


class UserProfileRepository(ABC):
    """Abstract base class for user profile repository implementations."""

    @abstractmethod
    def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Get a character by ID."""
        pass

    @abstractmethod
    def get_user_characters(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all characters for a user."""
        pass

    @abstractmethod
    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get a user profile."""
        pass

    @abstractmethod
    def get_game_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get game sessions for a user."""
        pass

    @abstractmethod
    def insert_game_session(self, session_data: Dict[str, Any]) -> Optional[str]:
        """Insert a game session. Returns session ID if successful."""
        pass

    @abstractmethod
    def insert_game_log(self, log_data: Dict[str, Any]) -> Optional[str]:
        """Insert a game log. Returns log ID if successful."""
        pass

    @abstractmethod
    def get_echoes(self, user_id: str) -> List[Dict[str, Any]]:
        """Get echoes for a user."""
        pass


class AuditRepository(ABC):
    """Abstract base class for audit repository implementations."""

    @abstractmethod
    def log_pedagogy_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a pedagogy audit event. Returns True if successful."""
        pass

    @abstractmethod
    def log_safety_event(self, event_data: Dict[str, Any]) -> bool:
        """Log a safety audit event. Returns True if successful."""
        pass

