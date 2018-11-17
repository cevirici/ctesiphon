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

# ------


class Biome:
    def __init__(self, isLand, fertility, baseColor, darkColor):
        self.isLand = isLand
        self.fertility = fertility
        self.baseColor = baseColor
        self.darkColor = darkColor

    def getColor(self, city):
        return mixColors(self.darkColor, self.baseColor, abs(city.altitude))

    biomes = {}
    biomes['Ocean'] = Biome(False, 0, OCEAN_COLOR, DARK_OCEAN)
    biomes['Lake'] = 
