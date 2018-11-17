# # --- Biome ---
# #
# # - A small class to help with differentiating cimates
# #
# # --- --- --- ---

from Graphics import *

# --- Colors ---

GRASS_COLOR = (131, 214, 131)
DARK_GRASS = (19, 135, 27)
FOREST_COLOR = (19, 82, 11)
OCEAN_COLOR = (125, 144, 225)
DARK_OCEAN = (25, 44, 225)
LAKE_COLOR = (46, 79, 206)
DESERT_COLOR = (247, 243, 143)
DARK_DESERT = (243, 220, 80)
TUNDRA_COLOR = (127, 138, 155)
DARK_TUNDRA = (77, 77, 77)
ICE_COLOR = (202, 225, 225)
HIGHLANDS_COLOR = (148, 209, 68)
DARK_HIGHLANDS = (108, 145, 56)
MOUNTAIN_COLOR = (110, 66, 14)
DARK_MOUNTAIN = (71, 50, 8)

# ------


class Biome:
    def __init__(self, isLand, baseColor, darkColor):
        self.isLand = isLand
        self.baseColor = baseColor
        self.darkColor = darkColor

    def getColor(self, city):
        return mixColors(self.darkColor, self.baseColor, abs(city.altitude))


biomes = {}
biomes['Ocean'] = Biome(False, OCEAN_COLOR, DARK_OCEAN)
biomes['Lake'] = Biome(False, LAKE_COLOR, LAKE_COLOR)
biomes['Grassland'] = Biome(True, GRASS_COLOR, DARK_GRASS)
biomes['Forest'] = Biome(True, DARK_GRASS, FOREST_COLOR)
biomes['Flood Plain'] = Biome(True, GRASS_COLOR, DARK_GRASS)
biomes['Desert'] = Biome(True, DESERT_COLOR, DARK_DESERT)
biomes['Tundra'] = Biome(True, TUNDRA_COLOR, DARK_TUNDRA)
biomes['Icy'] = Biome(True, ICE_COLOR, ICE_COLOR)
biomes['Highlands'] = Biome(True, HIGHLANDS_COLOR, DARK_HIGHLANDS)
biomes['Mountains'] = Biome(True, MOUNTAIN_COLOR, DARK_MOUNTAIN)
