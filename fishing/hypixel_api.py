"""
Hypixel API client with rate limiting, retries, and error handling.
"""
import httpx
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from datetime import datetime

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
    - Error responses (404, 429, 5xx)
    - Timeout handling
    """
    
    BASE_URL = "https://api.hypixel.net"
    TIMEOUT = 10.0  # seconds
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize client.
        
        Args:
            api_key: Optional Hypixel API key for authenticated requests
        """
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
    
    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True
    )
    async def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make GET request with retries.
        
        Args:
            endpoint: API endpoint (e.g., "/player")
            params: Query parameters
        
        Returns:
            JSON response as dict
        
        Raises:
            PlayerNotFoundError: Player not found (404)
            RateLimitError: Rate limit exceeded (429)
            HypixelAPIError: Other API errors
        """
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
        data = await self._get("/skyblock/profiles", {"uuid": uuid_clean})
        
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
        data = await self._get("/player", {"uuid": uuid_clean})
        return data
    
    def extract_fishing_stats(self, profile: Dict[str, Any], uuid: str) -> Dict[str, Any]:
        """
        Extract fishing-relevant stats from a Skyblock profile.
        
        Args:
            profile: Skyblock profile dict
            uuid: Player UUID (to find correct member data)
        
        Returns:
            Dict with fishing stats
        """
        uuid_clean = uuid.replace('-', '')
        member = profile.get('members', {}).get(uuid_clean, {})
        
        # Fishing skill XP - try multiple paths (Hypixel API structure varies)
        fishing_xp = 0
        
        # Path 1: leveling.experience (most common in newer profiles)
        if 'leveling' in member and 'experience' in member['leveling']:
            fishing_xp = member['leveling']['experience'].get('SKILL_FISHING', 0)
        
        # Path 2: player_data.experience (older format)
        if not fishing_xp and 'player_data' in member and 'experience' in member['player_data']:
            fishing_xp = member['player_data']['experience'].get('SKILL_FISHING', 0)
        
        # Path 3: direct experience_skill_fishing key
        if not fishing_xp:
            fishing_xp = member.get('experience_skill_fishing', 0)
        
        # Calculate level from XP
        fishing_level = self._xp_to_level(fishing_xp)
        
        # Trophy fish
        trophy_fish = member.get('trophy_fish', {})
        
        # Bestiary (sea creatures)
        bestiary = member.get('bestiary', {}).get('kills', {})
        sea_creature_kills = {
            k: v for k, v in bestiary.items()
            if 'sea' in k.lower() or 'shark' in k.lower() or 'squid' in k.lower()
        }
        
        # Equipment
        equipment = member.get('inventory', {}).get('equipment_contents', {}).get('data', [])
        
        # Wardrobe
        wardrobe = member.get('inventory', {}).get('wardrobe_contents', {}).get('data', [])
        
        return {
            'fishing_level': fishing_level,
            'fishing_xp': fishing_xp,
            'trophy_fish': trophy_fish,
            'sea_creature_kills': sea_creature_kills,
            'equipment': equipment,
            'wardrobe': wardrobe,
            'profile_id': profile.get('profile_id'),
            'cute_name': profile.get('cute_name'),
            'last_save': profile.get('members', {}).get(uuid_clean, {}).get('last_save', 0)
        }

    @staticmethod
    def _xp_to_level(xp: float) -> int:
        """
        Convert fishing XP to level (simplified).
        Real formula uses cumulative XP thresholds.
        """
        # Simplified: 1M XP ≈ Level 50
        if xp >= 55172425:  # Level 50
            return 50
        elif xp >= 27652625:  # Level 45
            return 45
        elif xp >= 13512625:  # Level 40
            return 40
        elif xp >= 6452625:   # Level 35
            return 35
        elif xp >= 2982625:   # Level 30
            return 30
        elif xp >= 1332625:   # Level 25
            return 25
        elif xp >= 572625:    # Level 20
            return 20
        elif xp >= 232625:    # Level 15
            return 15
        elif xp >= 87625:     # Level 10
            return 10
        elif xp >= 27625:     # Level 5
            return 5
        else:
            return int(xp / 5000)  # Rough approximation
