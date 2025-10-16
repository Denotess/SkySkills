"""
Hypixel API client for fetching Skyblock data.

Handles rate limiting, retries, and error handling.
"""
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class HypixelAPIError(Exception):
    """Base exception for Hypixel API errors."""
    pass


class PlayerNotFoundError(HypixelAPIError):
    """Player does not exist."""
    pass


class RateLimitError(HypixelAPIError):
    """API rate limit exceeded."""
    pass


class HypixelAPIClient:
    """
    Async HTTP client for Hypixel API.
    
    Handles:
    - Rate limiting (120 req/min per Hypixel docs)
    - Retries with exponential backoff
    - Error handling
    """
    
    BASE_URL = "https://api.hypixel.net"
    
    # XP required for each fishing level (official Hypixel values)
    FISHING_XP_THRESHOLDS = [
        0, 50, 125, 200, 300, 500, 750, 1000, 1500, 2000,
        3500, 5000, 7500, 10000, 15000, 20000, 30000, 50000,
        75000, 100000, 200000, 300000, 400000, 500000, 600000,
        700000, 800000, 900000, 1000000, 1100000, 1200000,
        1300000, 1400000, 1500000, 1600000, 1700000, 1800000,
        1900000, 2000000, 2100000, 2200000, 2300000, 2400000,
        2500000, 2600000, 2750000, 2900000, 3100000, 3400000,
        3700000, 4000000
    ]
    
    def __init__(self, api_key: str = None):
        """
        Initialize API client.
        
        Args:
            api_key: Optional Hypixel API key for authenticated requests
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def _get(self, endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Make GET request to Hypixel API with retry logic.
        
        Args:
            endpoint: API endpoint (e.g., "/skyblock/profiles")
            params: Query parameters
        
        Returns:
            JSON response as dict
        
        Raises:
            PlayerNotFoundError: Player not found (404)
            RateLimitError: Rate limit exceeded (429)
            HypixelAPIError: Other API errors
        """
        if params is None:
            params = {}
        
        if self.api_key:
            params['key'] = self.api_key
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = await self.client.get(url, params=params)
            
            if response.status_code == 404:
                raise PlayerNotFoundError("Player not found")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            elif response.status_code >= 500:
                raise HypixelAPIError(f"Server error: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()
            
            if not data.get('success'):
                cause = data.get('cause', 'Unknown error')
                raise HypixelAPIError(f"API returned success=false: {cause}")
            
            return data
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise HypixelAPIError(f"HTTP error: {e.response.status_code}")
        except httpx.TimeoutException:
            logger.warning(f"Request timeout for {endpoint}")
            raise
        except httpx.NetworkError as e:
            logger.warning(f"Network error: {e}")
            raise
    
    async def get_uuid_from_ign(self, ign: str) -> str:
        """
        Convert IGN to UUID using Mojang API.
        
        Args:
            ign: In-game name (Minecraft username)
        
        Returns:
            UUID string (with hyphens)
        
        Raises:
            PlayerNotFoundError: IGN does not exist
        """
        url = f"https://api.mojang.com/users/profiles/minecraft/{ign}"
        
        try:
            response = await self.client.get(url)
            
            if response.status_code == 404:
                raise PlayerNotFoundError(f"IGN '{ign}' not found")
            
            response.raise_for_status()
            data = response.json()
            
            # Add hyphens to UUID
            uuid_raw = data['id']
            uuid = f"{uuid_raw[:8]}-{uuid_raw[8:12]}-{uuid_raw[12:16]}-{uuid_raw[16:20]}-{uuid_raw[20:]}"
            
            return uuid
        
        except httpx.HTTPStatusError as e:
            logger.error(f"Mojang API error: {e}")
            raise HypixelAPIError(f"Mojang API error: {e.response.status_code}")
    
    async def get_skyblock_profiles(self, uuid: str) -> Dict[str, Any]:
        """
        Get all Skyblock profiles for a player.
        
        Args:
            uuid: Player UUID (with or without hyphens)
        
        Returns:
            Dict with 'profiles' key containing list of profiles
        
        Raises:
            PlayerNotFoundError: Player has no Skyblock profiles
            HypixelAPIError: API request failed
        """
        uuid_clean = uuid.replace('-', '')
        data = await self._get("/v2/skyblock/profiles", {"uuid": uuid_clean})
        
        if not data.get('profiles'):
            raise PlayerNotFoundError("Player has no Skyblock profiles")
        
        return data
    
    async def get_player_data(self, uuid: str) -> Dict[str, Any]:
        """
        Get player data (for achievements, first login, etc.).
        
        Args:
            uuid: Player UUID
        
        Returns:
            Player data dict
        """
        uuid_clean = uuid.replace('-', '')
        return await self._get("/player", {"uuid": uuid_clean})
    
    def extract_fishing_stats(self, profile: Dict[str, Any], uuid: str) -> Dict[str, Any]:
        """
        Extract fishing-related stats from a Skyblock profile.
        
        Args:
            profile: Skyblock profile dict from API
            uuid: Player UUID (with hyphens)
        
        Returns:
            Dict with fishing stats including:
                - fishing_level: int
                - fishing_xp: float
                - trophy_fish: dict
                - sea_creature_kills: dict
                - profile_id: str
                - cute_name: str
        """
        uuid_clean = uuid.replace('-', '')
        member = profile.get('members', {}).get(uuid_clean, {})
        
        fishing_xp = 0
        
        # Path 1: player_data.experience.SKILL_FISHING (v2 API - most reliable)
        if 'player_data' in member and 'experience' in member['player_data']:
            experience = member['player_data']['experience']
            if isinstance(experience, dict):
                fishing_xp = experience.get('SKILL_FISHING', 0)
        
        # Path 2: leveling.experience (backup for v2 API)
        elif 'leveling' in member and 'experience' in member['leveling']:
            experience = member['leveling']['experience']
            if isinstance(experience, dict):
                fishing_xp = experience.get('SKILL_FISHING', 0)
        
        # Path 3: experience_skill_fishing (older profiles)
        elif 'experience_skill_fishing' in member:
            fishing_xp = member['experience_skill_fishing']
        
        # Convert XP to level
        fishing_level = self._xp_to_level(fishing_xp)
        
        # Extract trophy fish
        trophy_fish = member.get('trophy_fish', {})
        
        # Extract sea creature kills from bestiary
        bestiary = member.get('bestiary', {})
        sea_creature_kills = bestiary.get('kills', {})
        
        return {
            'fishing_level': fishing_level,
            'fishing_xp': fishing_xp,
            'trophy_fish': trophy_fish,
            'sea_creature_kills': sea_creature_kills,
            'profile_id': profile.get('profile_id'),
            'cute_name': profile.get('cute_name')
        }
    
    def _xp_to_level(self, xp: float) -> int:
        """
        Convert fishing XP to fishing level using official thresholds.
        
        Args:
            xp: Total fishing XP
        
        Returns:
            Fishing level (0-50)
        """
        cumulative_xp = 0
        
        for level, required_xp in enumerate(self.FISHING_XP_THRESHOLDS):
            cumulative_xp += required_xp
            if xp < cumulative_xp:
                return level
        
        return 50  # Max level
