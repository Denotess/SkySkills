"""
Advanced fishing stats calculator for Hypixel SkyBlock.

Calculates derived stats like SCC, Magic Find, effective stats, etc.
"""
from typing import Dict, Any, List
import re


class FishingStatsCalculator:
    """Calculate advanced fishing statistics from profile data."""
    
    # Trophy fish tiers
    TROPHY_FISH_TIERS = {
        'sulphur_skitter': ['bronze', 'silver', 'gold', 'diamond'],
        'obfuscated_1': ['bronze', 'silver', 'gold', 'diamond'],
        'obfuscated_2': ['bronze', 'silver', 'gold', 'diamond'],
        'obfuscated_3': ['bronze', 'silver', 'gold', 'diamond'],
        'steaminghot_flounder': ['bronze', 'silver', 'gold', 'diamond'],
        'gusher': ['bronze', 'silver', 'gold', 'diamond'],
        'blobfish': ['bronze', 'silver', 'gold', 'diamond'],
        'slugfish': ['bronze', 'silver', 'gold', 'diamond'],
        'flyfish': ['bronze', 'silver', 'gold', 'diamond'],
        'lavahorse': ['bronze', 'silver', 'gold', 'diamond'],
        'mana_ray': ['bronze', 'silver', 'gold', 'diamond'],
        'volcanic_stonefish': ['bronze', 'silver', 'gold', 'diamond'],
        'vanille': ['bronze', 'silver', 'gold', 'diamond'],
        'skeleton_fish': ['bronze', 'silver', 'gold', 'diamond'],
        'moldfin': ['bronze', 'silver', 'gold', 'diamond'],
        'soul_fish': ['bronze', 'silver', 'gold', 'diamond'],
        'karate_fish': ['bronze', 'silver', 'gold', 'diamond'],
        'golden_fish': ['bronze', 'silver', 'gold', 'diamond'],
    }
    
    def __init__(self, profile_data: Dict[str, Any], uuid: str):
        """
        Initialize calculator with profile data.
        
        Args:
            profile_data: Full Hypixel profile dict
            uuid: Player UUID (with hyphens)
        """
        self.profile = profile_data
        self.uuid_clean = uuid.replace('-', '')
        self.member = profile_data.get('members', {}).get(self.uuid_clean, {})
    
    def calculate_trophy_fish_stats(self, trophy_fish: Dict[str, int]) -> Dict[str, Any]:
        """
        Calculate trophy fish statistics.
        
        Args:
            trophy_fish: Dict of trophy fish counts from API
        
        Returns:
            Dict with trophy fish breakdown by tier
        """
        stats = {
            'total_caught': 0,
            'by_tier': {'bronze': 0, 'silver': 0, 'gold': 0, 'diamond': 0},
            'by_fish': {}
        }
        
        for fish_key, count in trophy_fish.items():
            # Skip non-numeric values
            if not isinstance(count, (int, float)):
                continue
            
            # Parse fish name and tier (e.g., "sulphur_skitter_bronze")
            parts = fish_key.rsplit('_', 1)
            if len(parts) == 2:
                fish_name, tier = parts
                if tier in stats['by_tier']:
                    stats['by_tier'][tier] += int(count)
                    stats['total_caught'] += int(count)
                    
                    if fish_name not in stats['by_fish']:
                        stats['by_fish'][fish_name] = {'total': 0, 'tiers': {}}
                    
                    stats['by_fish'][fish_name]['total'] += int(count)
                    stats['by_fish'][fish_name]['tiers'][tier] = int(count)
        
        return stats
    
    def calculate_sea_creature_stats(self, sea_creature_kills: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate sea creature kill statistics.
        
        Args:
            sea_creature_kills: Dict of sea creature kills from API
        
        Returns:
            Dict with sea creature stats
        """
        # Notable creatures for fishing
        notable_creatures = {
            'water_hydra': 'Water Hydra',
            'the_sea_emperor': 'Sea Emperor',
            'thunder': 'Thunder',
            'lord_jawbus': 'Lord Jawbus',
            'great_white_shark': 'Great White Shark',
            'yeti': 'Yeti',
        }
        
        stats = {
            'total_kills': 0,
            'unique_types': 0,
            'notable': {}
        }
        
        # Filter out non-numeric values and sum
        numeric_kills = {}
        for creature_id, kill_count in sea_creature_kills.items():
            if isinstance(kill_count, (int, float)):
                numeric_kills[creature_id] = int(kill_count)
        
        stats['total_kills'] = sum(numeric_kills.values())
        stats['unique_types'] = len(numeric_kills)
        
        # Extract notable creatures
        for creature_id, display_name in notable_creatures.items():
            if creature_id in numeric_kills:
                stats['notable'][display_name] = numeric_kills[creature_id]
        
        return stats
    
    def get_fishing_recommendations(self, fishing_level: int, fishing_xp: float, 
                                   trophy_stats: Dict[str, Any]) -> List[str]:
        """
        Generate fishing recommendations based on current stats.
        
        Args:
            fishing_level: Current fishing level
            fishing_xp: Current fishing XP
            trophy_stats: Trophy fish statistics
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Level-based recommendations
        if fishing_level < 25:
            recommendations.append("�� Focus on leveling fishing to unlock better loot pools")
        elif fishing_level < 30:
            recommendations.append("🏆 Start trophy fishing in the Crimson Isle for better loot")
        
        if fishing_level >= 26:
            recommendations.append("✅ You can fish for Great White Sharks and Thunder")
        
        if fishing_level >= 40:
            recommendations.append("🌊 High fishing level! You have access to all sea creatures")
        
        # Trophy fish recommendations
        total_trophy = trophy_stats['total_caught']
        if total_trophy == 0:
            recommendations.append("🐠 Start trophy fishing to improve your Fishing Speed and earn rewards!")
        elif total_trophy < 100:
            recommendations.append("🐠 Catch more trophy fish to increase your Fishing Speed")
        elif total_trophy < 1000:
            recommendations.append("💎 Focus on catching diamond trophy fish for better rewards")
        else:
            recommendations.append("🌟 Impressive! You've caught {} trophy fish!".format(total_trophy))
        
        # Diamond trophy count
        diamond_count = trophy_stats['by_tier']['diamond']
        if diamond_count == 0 and total_trophy > 0:
            recommendations.append("💎 Try to catch your first diamond trophy fish!")
        elif diamond_count < 10:
            recommendations.append("💎 You need more diamond trophy fish (current: {})".format(diamond_count))
        elif diamond_count < 50:
            recommendations.append("💎 Good progress on diamond trophies! ({}/50)".format(diamond_count))
        elif diamond_count >= 50:
            recommendations.append("🌟 Outstanding! You have {} diamond trophy fish".format(diamond_count))
        
        return recommendations
    
    def calculate_all_stats(self, fishing_level: int, fishing_xp: float,
                           trophy_fish: Dict[str, int],
                           sea_creature_kills: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate all advanced fishing stats.
        
        Returns comprehensive stats dict.
        """
        trophy_stats = self.calculate_trophy_fish_stats(trophy_fish)
        sea_creature_stats = self.calculate_sea_creature_stats(sea_creature_kills)
        recommendations = self.get_fishing_recommendations(fishing_level, fishing_xp, trophy_stats)
        
        return {
            'trophy_fish': trophy_stats,
            'sea_creatures': sea_creature_stats,
            'recommendations': recommendations
        }
