"""
Fishing calculators for Skyskills.
Each calculator is deterministic and unit-testable.
"""
from typing import Dict, Any


def calculate_scc(
    base_scc: float,
    rod_scc: float,
    armor_scc: float,
    pet_scc: float,
    equipment_scc: float,
    accessory_scc: float,
    bait_scc: float,
    set_bonuses: Dict[str, Any] = None
) -> float:
    """
    Calculate total Sea Creature Chance (SCC).
    
    Formula: Sum all SCC sources, then apply set bonuses.
    
    Args:
        base_scc: Player's base SCC (usually 0 unless from skills/perks)
        rod_scc: SCC from fishing rod
        armor_scc: Total SCC from all armor pieces
        pet_scc: SCC from pet
        equipment_scc: SCC from equipment slot
        accessory_scc: Total SCC from all accessories
        bait_scc: SCC from bait
        set_bonuses: Dict of set bonuses, e.g. {"scc_flat": 5, "scc_multiplier": 1.1}
    
    Returns:
        Total SCC as float, rounded to 2 decimals
    
    Examples:
        >>> calculate_scc(0, 4, 10, 5, 0, 3, 2)
        24.0
        >>> calculate_scc(0, 10, 10, 0, 0, 0, 0, {"scc_multiplier": 1.1})
        22.0
    """
    total = base_scc + rod_scc + armor_scc + pet_scc + equipment_scc + accessory_scc + bait_scc
    
    if set_bonuses:
        flat_bonus = set_bonuses.get('scc_flat', 0)
        multiplier = set_bonuses.get('scc_multiplier', 1.0)
        total = (total + flat_bonus) * multiplier
    
    return round(total, 2)


def calculate_fishing_speed(
    base_fs: float,
    rod_fs: float,
    armor_fs: float,
    pet_fs: float,
    equipment_fs: float,
    accessory_fs: float,
    bait_fs: float,
    set_bonuses: Dict[str, Any] = None
) -> float:
    """
    Calculate total Fishing Speed (FS).
    
    Formula: Sum all FS sources, then apply set bonuses.
    
    Args:
        base_fs: Player's base FS
        rod_fs: FS from fishing rod
        armor_fs: Total FS from all armor pieces
        pet_fs: FS from pet
        equipment_fs: FS from equipment slot
        accessory_fs: Total FS from all accessories
        bait_fs: FS from bait
        set_bonuses: Dict of set bonuses, e.g. {"fs_flat": 10, "fs_multiplier": 1.2}
    
    Returns:
        Total FS as float, rounded to 2 decimals
    
    Examples:
        >>> calculate_fishing_speed(0, 20, 15, 10, 5, 8, 2)
        60.0
        >>> calculate_fishing_speed(0, 50, 0, 0, 0, 0, 0, {"fs_multiplier": 1.5})
        75.0
    """
    total = base_fs + rod_fs + armor_fs + pet_fs + equipment_fs + accessory_fs + bait_fs
    
    if set_bonuses:
        flat_bonus = set_bonuses.get('fs_flat', 0)
        multiplier = set_bonuses.get('fs_multiplier', 1.0)
        total = (total + flat_bonus) * multiplier
    
    return round(total, 2)
