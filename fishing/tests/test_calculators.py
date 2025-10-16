"""
Unit tests for fishing calculators.
Each test validates a specific calculation scenario.
"""
import pytest
from fishing.calculators import calculate_scc, calculate_fishing_speed


class TestSCCCalculator:
    """Test Sea Creature Chance calculator."""
    
    def test_scc_basic_sum(self):
        """Test basic SCC summation without bonuses."""
        result = calculate_scc(
            base_scc=0,
            rod_scc=4,
            armor_scc=10,
            pet_scc=5,
            equipment_scc=0,
            accessory_scc=3,
            bait_scc=2
        )
        assert result == 24.0
    
    def test_scc_with_flat_bonus(self):
        """Test SCC with flat set bonus."""
        result = calculate_scc(
            base_scc=0,
            rod_scc=4,
            armor_scc=10,
            pet_scc=5,
            equipment_scc=0,
            accessory_scc=0,
            bait_scc=0,
            set_bonuses={"scc_flat": 5}
        )
        # (0+4+10+5+0+0+0 + 5_flat) = 24
        assert result == 24.0
    
    def test_scc_with_multiplier(self):
        """Test SCC with percentage multiplier."""
        result = calculate_scc(
            base_scc=0,
            rod_scc=10,
            armor_scc=10,
            pet_scc=0,
            equipment_scc=0,
            accessory_scc=0,
            bait_scc=0,
            set_bonuses={"scc_multiplier": 1.1}
        )
        # (10+10) * 1.1 = 22.0
        assert result == 22.0
    
    def test_scc_with_both_flat_and_multiplier(self):
        """Test SCC with both flat bonus and multiplier."""
        result = calculate_scc(
            base_scc=0,
            rod_scc=10,
            armor_scc=5,
            pet_scc=0,
            equipment_scc=0,
            accessory_scc=0,
            bait_scc=0,
            set_bonuses={"scc_flat": 5, "scc_multiplier": 1.2}
        )
        # ((10+5) + 5_flat) * 1.2 = 20 * 1.2 = 24.0
        assert result == 24.0
    
    def test_scc_zero_inputs(self):
        """Test SCC with all zeroes."""
        result = calculate_scc(0, 0, 0, 0, 0, 0, 0)
        assert result == 0.0
    
    def test_scc_rounding(self):
        """Test SCC rounds to 2 decimal places."""
        result = calculate_scc(
            base_scc=0,
            rod_scc=10,
            armor_scc=10,
            pet_scc=0,
            equipment_scc=0,
            accessory_scc=0,
            bait_scc=0,
            set_bonuses={"scc_multiplier": 1.15}
        )
        # 20 * 1.15 = 23.0
        assert result == 23.0


class TestFishingSpeedCalculator:
    """Test Fishing Speed calculator."""
    
    def test_fs_basic_sum(self):
        """Test basic FS summation."""
        result = calculate_fishing_speed(
            base_fs=0,
            rod_fs=20,
            armor_fs=15,
            pet_fs=10,
            equipment_fs=5,
            accessory_fs=8,
            bait_fs=2
        )
        assert result == 60.0
    
    def test_fs_with_set_bonus(self):
        """Test FS with set bonus multiplier."""
        result = calculate_fishing_speed(
            base_fs=0,
            rod_fs=50,
            armor_fs=0,
            pet_fs=0,
            equipment_fs=0,
            accessory_fs=0,
            bait_fs=0,
            set_bonuses={"fs_multiplier": 1.5}
        )
        # 50 * 1.5 = 75.0
        assert result == 75.0
    
    def test_fs_with_flat_bonus(self):
        """Test FS with flat bonus."""
        result = calculate_fishing_speed(
            base_fs=0,
            rod_fs=40,
            armor_fs=0,
            pet_fs=0,
            equipment_fs=0,
            accessory_fs=0,
            bait_fs=0,
            set_bonuses={"fs_flat": 10}
        )
        # (40 + 10_flat) = 50.0
        assert result == 50.0
    
    def test_fs_combined_bonuses(self):
        """Test FS with both flat and multiplier bonuses."""
        result = calculate_fishing_speed(
            base_fs=0,
            rod_fs=30,
            armor_fs=10,
            pet_fs=0,
            equipment_fs=0,
            accessory_fs=0,
            bait_fs=0,
            set_bonuses={"fs_flat": 10, "fs_multiplier": 1.2}
        )
        # ((30+10) + 10_flat) * 1.2 = 50 * 1.2 = 60.0
        assert result == 60.0
    
    def test_fs_zero_inputs(self):
        """Test FS with all zeroes."""
        result = calculate_fishing_speed(0, 0, 0, 0, 0, 0, 0)
        assert result == 0.0
