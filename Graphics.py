# # --- Graphics ---
# #
# # - General graphical functions
# #
# # --- --- --- ---


# --- Constants ---

GRASS_COLOR = (131, 214, 131)
DARK_GRASS = (19, 135, 27)
OCEAN_COLOR = (125, 144, 225)
DARK_OCEAN = (25, 44, 225)

# --- End Constants ---


def scale(point, data):
    return [point[i] * data.zoom - data.viewPos[i] for i in range(2)]


def rgbToColor(rgb):
    # Converts a tuple containing RGB values to a color string
    return "#{:0>2x}{:0>2x}{:0>2x}".format(*rgb)


def mixColors(rgb_1, rgb_2, factor):
    # Returns the hex code of a linear mix between two RGB triples
    # A factor of 0 gives rgb_1, a factor of 1 gives rgb_2
    return rgbToColor([int(rgb_2[i] * factor + rgb_1[i] * (1 - factor))
                       for i in range(3)])
