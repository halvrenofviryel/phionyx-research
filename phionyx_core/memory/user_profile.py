"""
User Profile Manager - Supabase Integration
Handles user profiles, characters, game sessions, and game logs.
"""

import logging
from typing import Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    create_client = None
    Client = None
import os

if TYPE_CHECKING:
    from phionyx_core.contracts.database import UserProfileRepositoryProtocol

logger = logging.getLogger(__name__)

class UserProfile:
    """
    Manages user profiles, characters, game sessions, and game logs in Supabase.
    """

    def __init__(self, user_profile_repository: Optional['UserProfileRepositoryProtocol'] = None):
        """
        Initialize UserProfile.

        Args:
            user_profile_repository: User profile repository (optional). If provided, uses repository for DB access.
                                   If None, falls back to direct Supabase client (backward compatible).
        """
        # Store repository (if provided)
        self._user_profile_repository = user_profile_repository

        self.client: Optional[Client] = None
        self._init_client()

    def _init_client(self):
        """Initialize Supabase client (fallback if repository not provided)."""
        if self._user_profile_repository is None:
            # Backward compatible: Use direct Supabase client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

            if supabase_url and supabase_key:
                try:
                    self.client = create_client(supabase_url, supabase_key)
                    logger.info("Supabase client initialized (direct client - backward compatible)")
                except Exception as e:
                    logger.error(f"Failed to initialize Supabase client: {e}")
                    self.client = None
            else:
                logger.warning("Supabase credentials not found, running in offline mode")
                self.client = None
        else:
            # Use repository (preferred path)
            self.client = None
            logger.info("UserProfile initialized with repository (preferred path)")

    def is_connected(self) -> bool:
        """Check if Supabase is connected."""
        return self.client is not None

    # ======================================================================
    # USER OPERATIONS
    # ======================================================================

    async def get_or_create_user(
        self,
        profile_id: str,
        username: Optional[str] = None,
        email: Optional[str] = None
    ) -> Dict:
        """
        Get existing user or create new one.

        Args:
            profile_id: Supabase Auth user ID
            username: Optional username
            email: Optional email

        Returns:
            User dict with id, username, email, created_at
        """
        if not self.is_connected():
            return {
                "id": profile_id,
                "username": username or "user",
                "email": email,
                "created_at": datetime.now().isoformat()
            }

        try:
            # Try to get existing profile
            response = self.client.table("profiles").select("*").eq("id", profile_id).execute()

            if response.data and len(response.data) > 0:
                logger.info(f"User found: {profile_id}")
                return response.data[0]

            # Create new profile
            new_profile = {
                "id": profile_id,
                "username": username or f"user_{profile_id[:8]}",
                "email": email,
                "created_at": datetime.now().isoformat()
            }

            result = self.client.table("profiles").insert(new_profile).execute()

            if result.data:
                logger.info(f"User created: {profile_id}")
                return result.data[0]

            return new_profile
        except Exception as e:
            logger.error(f"Failed to get/create user: {e}")
            return {
                "id": profile_id,
                "username": username or "user",
                "email": email
            }

    # ======================================================================
    # CHARACTER OPERATIONS
    # ======================================================================

    async def create_character(
        self,
        user_id: str,
        character_data: Dict
    ) -> Optional[Dict]:
        """
        Create a new character.

        Args:
            user_id: User UUID (profile_id)
            character_data: Character data dict

        Returns:
            Created character dict or None
        """
        if not self.is_connected():
            return None

        try:
            character = {
                "profile_id": user_id,
                "character_name": character_data.get("name"),
                "character_class": character_data.get("character_class", "Yolcu"),
                "archetype": character_data.get("archetype", "shadow"),
                "willpower": character_data.get("willpower", 10),
                "balance": character_data.get("balance", 10),
                "silence": character_data.get("silence", 10),
                "current_state": character_data.get("current_state", {}),
                "neurotransmitters": character_data.get("neurotransmitters", {}),
                "lore_character_id": character_data.get("lore_character_id"),
            }

            result = self.client.table("characters").insert(character).execute()

            if result.data:
                logger.info(f"Character created: {result.data[0]['id']}")
                return result.data[0]

            return None
        except Exception as e:
            logger.error(f"Failed to create character: {e}")
            return None

    async def get_character(
        self,
        character_id: str
    ) -> Optional[Dict]:
        """
        Get character by ID or name.

        Args:
            character_id: Character UUID or name or lore_character_id

        Returns:
            Character dict or None
        """
        if not self.is_connected():
            return None

        try:
            # Try by ID first
            response = self.client.table("characters").select("*").eq("id", character_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]

            # Try by name
            response = self.client.table("characters").select("*").eq("character_name", character_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]

            # Try by lore_character_id
            response = self.client.table("characters").select("*").eq("lore_character_id", character_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]

            return None
        except Exception as e:
            logger.error(f"Failed to get character: {e}")
            return None

    async def get_character_by_name(
        self,
        character_name: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Get character by name and user ID.

        Args:
            character_name: Character name
            user_id: User UUID

        Returns:
            Character dict or None
        """
        if not self.is_connected():
            return None

        try:
            response = self.client.table("characters").select("*").eq("character_name", character_name).eq("profile_id", user_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to get character by name: {e}")
            return None

    async def get_user_characters(self, user_id: str) -> List[Dict]:
        """
        Get all characters for a user.

        Args:
            user_id: User UUID

        Returns:
            List of character dicts
        """
        if not self.is_connected():
            return []

        try:
            response = self.client.table("characters").select("*").eq("profile_id", user_id).execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Failed to get user characters: {e}")
            return []

    # ======================================================================
    # GAME SESSION OPERATIONS
    # ======================================================================

    async def start_session(
        self,
        character_id: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Start a new game session.

        Args:
            character_id: Character UUID or name
            user_id: User UUID (profile_id)

        Returns:
            Session dict or None
        """
        if not self.is_connected():
            return {"id": f"offline-{character_id}", "turn_count": 0, "character_id": character_id}

        try:
            # Get character ID if character_id is a name
            character = await self.get_character(character_id)
            actual_character_id = character.get("id") if character else character_id

            # Check for existing active session
            response = self.client.table("game_sessions").select("*").eq("character_id", actual_character_id).eq("is_active", True).execute()

            if response.data and len(response.data) > 0:
                logger.info(f"Active session found: {response.data[0]['id']}")
                return response.data[0]

            # Create new session
            session = {
                "character_id": actual_character_id,
                "user_id": user_id,
                "started_at": datetime.now().isoformat(),
                "turn_count": 0,
                "is_active": True
            }

            result = self.client.table("game_sessions").insert(session).execute()

            if result.data:
                logger.info(f"Session started: {result.data[0]['id']}")
                return result.data[0]

            return {"id": f"offline-{character_id}", "turn_count": 0, "character_id": actual_character_id}
        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            return {"id": f"offline-{character_id}", "turn_count": 0, "character_id": character_id}

    async def get_active_session(
        self,
        character_id: str
    ) -> Optional[Dict]:
        """
        Get active game session for a character.

        Args:
            character_id: Character UUID or name

        Returns:
            Session dict or None
        """
        if not self.is_connected():
            return None

        try:
            # Get character ID if character_id is a name
            character = await self.get_character(character_id)
            actual_character_id = character.get("id") if character else character_id

            response = self.client.table("game_sessions").select("*").eq("character_id", actual_character_id).eq("is_active", True).order("started_at", desc=True).limit(1).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]

            return None
        except Exception as e:
            logger.error(f"Failed to get active session: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        updates: Dict
    ) -> Optional[Dict]:
        """
        Update a game session.

        Args:
            session_id: Session UUID
            updates: Dict of updates

        Returns:
            Updated session dict or None
        """
        if not self.is_connected():
            return None

        try:
            result = self.client.table("game_sessions").update(updates).eq("id", session_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return None

    # ======================================================================
    # ECHO OPERATIONS
    # ======================================================================

    async def save_echo(
        self,
        session_id: str,
        character_id: str,
        turn_number: int,
        echo_data: Dict
    ) -> Optional[str]:
        """
        Save an echo (game action) to database.

        Args:
            session_id: Session UUID
            character_id: Character UUID
            turn_number: Turn number
            echo_data: Echo data dict

        Returns:
            Echo ID if successful, None otherwise
        """
        if not self.is_connected():
            return None

        try:
            echo = {
                "session_id": session_id,
                "character_id": character_id,
                "turn_number": turn_number,
                "echo_type": echo_data.get("action_type", "unknown"),
                "echo_data": echo_data,
                "phi": echo_data.get("physics_snapshot", {}).get("phi", 0.0),
                "created_at": datetime.now().isoformat()
            }

            result = self.client.table("echoes").insert(echo).execute()

            if result.data:
                logger.info(f"Echo saved: {result.data[0]['id']}")
                return result.data[0]["id"]

            return None
        except Exception as e:
            logger.error(f"Failed to save echo: {e}")
            return None

    # ======================================================================
    # GAME LOG OPERATIONS
    # ======================================================================

    async def save_game_log(
        self,
        character_id: str,
        action_type: str,
        action_data: Dict,
        user_input: Optional[str] = None,
        ai_response: Optional[str] = None,
        physics_snapshot: Optional[Dict] = None,
        emotional_state: Optional[Dict] = None,
        scene_context: Optional[str] = None,
        scene_result: Optional[str] = None,
        turn_number: int = 1,
        session_id: Optional[str] = None,
        profile_id: Optional[str] = None
    ) -> Optional[str]:
        """
        Save a game log entry.

        Args:
            character_id: Character UUID
            action_type: Type of action (card_selection, chat_message, etc.)
            action_data: Action data dict
            user_input: User input text
            ai_response: AI response text
            physics_snapshot: Physics state snapshot
            emotional_state: Emotional state snapshot
            scene_context: Scene context
            scene_result: Scene result
            turn_number: Turn number
            session_id: Session UUID
            profile_id: Profile UUID (optional)

        Returns:
            Game log ID if successful, None otherwise
        """
        if not self.is_connected():
            return None

        try:
            # Get actual character UUID if character_id is a name
            character = await self.get_character(character_id)
            actual_character_id = character.get("id") if character else character_id

            game_log = {
                "character_id": actual_character_id,
                "profile_id": profile_id,
                "action_type": action_type,
                "action_data": action_data,
                "user_input": user_input,
                "ai_response": ai_response,
                "physics_snapshot": physics_snapshot or {},
                "emotional_state": emotional_state or {},
                "scene_context": scene_context,
                "scene_result": scene_result,
                "turn_number": turn_number,
                "session_id": session_id,
                "created_at": datetime.now().isoformat()
            }

            result = self.client.table("game_logs").insert(game_log).execute()

            if result.data:
                logger.info(f"Game log saved: {result.data[0]['id']}")
                return result.data[0]["id"]

            return None
        except Exception as e:
            logger.error(f"Failed to save game log: {e}")
            return None


# Singleton instance
_user_profile_instance: Optional[UserProfile] = None

def get_user_profile_manager() -> UserProfile:
    """Get singleton UserProfile instance."""
    global _user_profile_instance
    if _user_profile_instance is None:
        _user_profile_instance = UserProfile()
    return _user_profile_instance
