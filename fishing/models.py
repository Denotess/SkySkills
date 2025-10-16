from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid


class Player(models.Model):
    """Represents a Hypixel player tracked by Skyskills."""
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ign = models.CharField(max_length=16, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.ign


class ProfileSnapshot(models.Model):
    """A snapshot of a player's Hypixel Skyblock profile at a point in time."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='snapshots')
    hypixel_profile_id = models.CharField(max_length=64, db_index=True)
    skill_fishing_level = models.IntegerField(default=0)
    raw_json = models.JSONField(default=dict, help_text="Full Hypixel API response for reproducibility")
    derived_stats = models.JSONField(
        default=dict,
        help_text="Computed stats: SCC, FS, Wisdom, MF, etc."
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['player', '-created_at']),
            models.Index(fields=['hypixel_profile_id']),
        ]

    def __str__(self):
        return f"{self.player.ign} L{self.skill_fishing_level} @ {self.created_at.isoformat()}"


class Item(models.Model):
    """A Hypixel Skyblock item (rod, armor, pet, accessory, bait, equipment)."""
    ITEM_TYPES = [
        ('rod', 'Fishing Rod'),
        ('helmet', 'Helmet'),
        ('chestplate', 'Chestplate'),
        ('leggings', 'Leggings'),
        ('boots', 'Boots'),
        ('pet', 'Pet'),
        ('accessory', 'Accessory'),
        ('equipment', 'Equipment'),
        ('bait', 'Bait'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPES)
    rarity = models.CharField(max_length=20, default='COMMON')
    base_stats = models.JSONField(
        default=dict,
        help_text="Base stats: SCC, FS, Wisdom, MF, Health, Defense, etc."
    )
    attributes = models.JSONField(
        default=dict,
        help_text="Special attributes, reforge info, pet level, etc."
    )
    cost_source = models.CharField(
        max_length=20,
        choices=[('bazaar', 'Bazaar'), ('ah', 'Auction House'), ('manual', 'Manual Entry')],
        default='manual'
    )
    active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rarity} {self.get_item_type_display()})"


class GearSet(models.Model):
    """A complete gear loadout (armor + rod + pet + accessories + equipment)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    pieces = models.ManyToManyField(Item, related_name='gear_sets')
    set_bonuses = models.JSONField(
        default=dict,
        help_text="Set bonuses applied when full set equipped"
    )
    requirements = models.JSONField(
        default=dict,
        help_text="Requirements: min_level, island, quest_completion, etc."
    )
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    """A fishing location in Hypixel Skyblock."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    coords = models.CharField(max_length=64, blank=True, help_text="x y z coords")
    water_or_lava = models.CharField(
        max_length=10,
        choices=[('water', 'Water'), ('lava', 'Lava')],
        default='water'
    )
    island = models.CharField(max_length=64, default='Hub')
    requirements = models.JSONField(
        default=dict,
        help_text="Requirements: min_level, quest, etc."
    )
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.island})"


class Method(models.Model):
    """A fishing method/strategy."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, unique=True)
    description = models.TextField()
    requirements = models.JSONField(default=dict)
    tags = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    calculators_used = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
        help_text="List of calculator names: SCC, FS, XP, Profit, etc."
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Recommendation(models.Model):
    """A computed recommendation for a profile snapshot."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    snapshot = models.ForeignKey(ProfileSnapshot, on_delete=models.CASCADE, related_name='recommendations')
    top_choice_json = models.JSONField(
        help_text="Top recommended gear/location/method"
    )
    breakdown_json = models.JSONField(
        help_text="Factor breakdown: XP/hr, Profit/hr, SCC, FS, etc."
    )
    score = models.FloatField()
    version = models.CharField(max_length=32, help_text="Data version + calculator version")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['snapshot', '-created_at']),
        ]

    def __str__(self):
        return f"Rec for {self.snapshot.player.ign} @ {self.created_at.isoformat()}"


class DataVersion(models.Model):
    """Tracks data/calculator versions for cache invalidation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.CharField(
        max_length=32,
        unique=True,
        help_text="Domain: fishing, dungeons, mining, etc."
    )
    version = models.CharField(max_length=32)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['domain']

    def __str__(self):
        return f"{self.domain} v{self.version}"


class BazaarPrice(models.Model):
    """Tracks Bazaar/AH prices for items (stub for Phase 7+)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='prices')
    price = models.DecimalField(max_digits=15, decimal_places=2)
    source_ts = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-source_ts']
        indexes = [
            models.Index(fields=['item', '-source_ts']),
        ]

    def __str__(self):
        return f"{self.item.name} @ {self.price} coins"