from django.contrib import admin
from .models import (
    Player, ProfileSnapshot, Item, GearSet, Location,
    Method, Recommendation, DataVersion, BazaarPrice
)


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['ign', 'uuid', 'created_at']
    search_fields = ['ign']


@admin.register(ProfileSnapshot)
class ProfileSnapshotAdmin(admin.ModelAdmin):
    list_display = ['player', 'skill_fishing_level', 'hypixel_profile_id', 'created_at']
    list_filter = ['skill_fishing_level', 'created_at']
    search_fields = ['player__ign', 'hypixel_profile_id']


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'item_type', 'rarity', 'active', 'cost_source']
    list_filter = ['item_type', 'rarity', 'active']
    search_fields = ['name']


@admin.register(GearSet)
class GearSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'created_at']
    filter_horizontal = ['pieces']
    search_fields = ['name']


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'island', 'water_or_lava', 'active']
    list_filter = ['island', 'water_or_lava', 'active']
    search_fields = ['name']


@admin.register(Method)
class MethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'active', 'created_at']
    search_fields = ['name']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['snapshot', 'score', 'version', 'created_at']
    list_filter = ['version', 'created_at']


@admin.register(DataVersion)
class DataVersionAdmin(admin.ModelAdmin):
    list_display = ['domain', 'version', 'created_at']
    search_fields = ['domain']


@admin.register(BazaarPrice)
class BazaarPriceAdmin(admin.ModelAdmin):
    list_display = ['item', 'price', 'source_ts', 'created_at']
    list_filter = ['source_ts']
