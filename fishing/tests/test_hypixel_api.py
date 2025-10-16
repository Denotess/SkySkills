"""
Unit tests for Hypixel API client.
Uses pytest-httpx to mock HTTP responses.
"""
import pytest
import httpx
from fishing.hypixel_api import (
    HypixelAPIClient,
    PlayerNotFoundError,
    RateLimitError,
    HypixelAPIError
)


@pytest.mark.asyncio
class TestHypixelAPIClient:
    """Test Hypixel API client."""
    
    async def test_get_uuid_from_ign_success(self, httpx_mock):
        """Test successful UUID lookup."""
        httpx_mock.add_response(
            url="https://api.mojang.com/users/profiles/minecraft/Technoblade",
            json={"id": "b876ec32e396476ba1158438d83c67d4", "name": "Technoblade"}
        )
        
        client = HypixelAPIClient()
        uuid = await client.get_uuid_from_ign("Technoblade")
        
        assert uuid == "b876ec32-e396-476b-a115-8438d83c67d4"
        await client.close()
    
    async def test_get_uuid_from_ign_not_found(self, httpx_mock):
        """Test IGN not found."""
        httpx_mock.add_response(
            url="https://api.mojang.com/users/profiles/minecraft/NonExistentPlayer123",
            status_code=404
        )
        
        client = HypixelAPIClient()
        
        with pytest.raises(PlayerNotFoundError, match="IGN 'NonExistentPlayer123' not found"):
            await client.get_uuid_from_ign("NonExistentPlayer123")
        
        await client.close()
    
    async def test_get_skyblock_profiles_success(self, httpx_mock):
        """Test successful profile fetch."""
        # Mock response matches the full URL including API key parameter
        httpx_mock.add_response(
            method="GET",
            url="https://api.hypixel.net/skyblock/profiles?uuid=b876ec32e396476ba1158438d83c67d4&key=test-key",
            json={
                "success": True,
                "profiles": [
                    {
                        "profile_id": "abc123",
                        "cute_name": "Apple",
                        "members": {
                            "b876ec32e396476ba1158438d83c67d4": {
                                "last_save": 1697462400000
                            }
                        }
                    }
                ]
            }
        )
        
        client = HypixelAPIClient(api_key="test-key")
        data = await client.get_skyblock_profiles("b876ec32-e396-476b-a115-8438d83c67d4")
        
        assert len(data['profiles']) == 1
        assert data['profiles'][0]['cute_name'] == "Apple"
        await client.close()
    
    async def test_get_skyblock_profiles_no_profiles(self, httpx_mock):
        """Test player with no Skyblock profiles."""
        httpx_mock.add_response(
            url="https://api.hypixel.net/skyblock/profiles?uuid=test123",
            json={"success": True, "profiles": None}
        )
        
        client = HypixelAPIClient()
        
        with pytest.raises(PlayerNotFoundError, match="Player has no Skyblock profiles"):
            await client.get_skyblock_profiles("test123")
        
        await client.close()
    
    async def test_rate_limit_error(self, httpx_mock):
        """Test 429 rate limit response."""
        httpx_mock.add_response(
            url="https://api.hypixel.net/skyblock/profiles?uuid=test123",
            status_code=429
        )
        
        client = HypixelAPIClient()
        
        with pytest.raises(RateLimitError, match="API rate limit exceeded"):
            await client.get_skyblock_profiles("test123")
        
        await client.close()


class TestFishingStatsExtraction:
    """Test fishing stats extraction (non-async)."""
    
    def test_extract_fishing_stats_with_leveling_path(self):
        """Test fishing stats extraction with leveling.experience path."""
        profile = {
            "profile_id": "abc123",
            "cute_name": "Apple",
            "members": {
                "testuuid": {  # UUID WITHOUT hyphens (Hypixel API format)
                    "leveling": {
                        "experience": {
                            "SKILL_FISHING": 1332625  # Level 25
                        }
                    },
                    "trophy_fish": {
                        "sulphur_skitter": 5,
                        "obfuscated_fish_1": 2
                    },
                    "bestiary": {
                        "kills": {
                            "sea_walker": 100,
                            "night_squid": 50,
                            "sea_guardian": 25
                        }
                    },
                    "last_save": 1697462400000
                }
            }
        }
        
        client = HypixelAPIClient()
        stats = client.extract_fishing_stats(profile, "test-uuid")  # Pass WITH hyphens, method removes them
        
        assert stats['fishing_level'] == 25
        assert stats['fishing_xp'] == 1332625
        assert stats['trophy_fish']['sulphur_skitter'] == 5
        assert stats['sea_creature_kills']['sea_walker'] == 100
        assert stats['profile_id'] == "abc123"
        assert stats['cute_name'] == "Apple"
    
    def test_extract_fishing_stats_with_alternative_path(self):
        """Test fishing stats extraction with experience_skill_fishing path."""
        profile = {
            "profile_id": "xyz789",
            "cute_name": "Banana",
            "members": {
                "player123": {  # UUID WITHOUT hyphens
                    "experience_skill_fishing": 572625,  # Level 20
                    "trophy_fish": {},
                    "bestiary": {"kills": {}},
                    "last_save": 1697462400000
                }
            }
        }
        
        client = HypixelAPIClient()
        stats = client.extract_fishing_stats(profile, "player-123")  # Pass WITH hyphens
        
        assert stats['fishing_level'] == 20
        assert stats['fishing_xp'] == 572625
