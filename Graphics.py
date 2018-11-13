# # --- Graphics ---
# #
# # - General graphical functions
# #
# # --- --- --- ---

from Geometry import dist

# --- Constants ---

GRASS_COLOR = (131, 214, 131)
DARK_GRASS = (19, 135, 27)
OCEAN_COLOR = (125, 144, 225)
DARK_OCEAN = (25, 44, 225)
HIGHLIGHT = (235, 248, 95)
DRY_COLOR = (242, 244, 114)
COLD_COLOR = (99, 235, 255)
HOT_COLOR = (242, 56, 56)

LOADING_FONT = ('Garamond', 48)
HUD_FONT = ('Garamond', 22)

BORDER = 15
ZOOM_FACTOR = 1.5

# --- End Constants ---


def scale(point, data):
    # Returns the view coordinates of a given points
    return [(point[i] - data.viewPos[i]) * data.zoom + data.mapPos[i]
            for i in range(2)]


def rgbToColor(rgb):
    # Converts a tuple containing RGB values to a color string
    return "#{:0>2x}{:0>2x}{:0>2x}".format(*rgb)


def mixColors(rgb_1, rgb_2, factor):
    # Returns the hex code of a linear mix between two RGB triples
    # A factor of 0 gives rgb_1, a factor of 1 gives rgb_2
    return rgbToColor([int(rgb_2[i] * factor + rgb_1[i] * (1 - factor))
                       for i in range(3)])


def limitView(data):
    # Keep the view within bounds
    maxX = data.map.width + BORDER - data.viewSize[0] / data.zoom
    maxY = data.map.height + BORDER - data.viewSize[1] / data.zoom
    data.viewPos[0] = max(-BORDER, min(maxX, data.viewPos[0]))
    data.viewPos[1] = max(-BORDER, min(maxY, data.viewPos[1]))


def recheckCenter(data):
    # Checks that the center city is still in the center
    center = [data.viewPos[i] + data.viewSize[i] / data.zoom / 2
              for i in range(2)]
    closestDist = dist(data.map.centerCity.center, center)
    toCheck = list(data.map.centerCity.neighbors)
    checked = set()
    while len(toCheck) > 0:
        city = toCheck.pop(0)
        checked.add(city)
        if dist(city.center, center) < closestDist:
            closestDist = dist(city.center, center)
            data.map.centerCity = city
            for neigh in city.neighbors:
                if neigh not in checked:
                    toCheck.append(neigh)


def zoom(data, factor, x, y):
    # Handle zooming
    oldZoom = data.zoom
    data.zoom *= 1.1 ** factor
    data.zoom = max(1, data.zoom)
    scale = (1 / data.zoom - 1 / oldZoom)

    # 'Centralize' the target if cursor is off-center
    tracking = factor / 30
    data.viewPos[0] -= (data.width / 2 - x) * tracking + x * scale
    data.viewPos[1] -= (data.height / 2 - y) * tracking + y * scale

    limitView(data)
    recheckCenter(data)


def scroll(data, margin, x, y):
    if 0 < x < data.viewSize[0] and 0 < y < data.viewSize[1]:
        if 0 < x < margin:
            data.viewPos[0] -= (margin - x) / ZOOM_FACTOR / data.zoom
        elif data.viewSize[0] > x > data.viewSize[0] - margin:
            data.viewPos[0] += (x - data.viewSize[0] + margin) / \
                ZOOM_FACTOR / data.zoom

        if 0 < y < margin:
            data.viewPos[1] -= (margin - y) / ZOOM_FACTOR / data.zoom
        elif data.viewSize[1] > y > data.viewSize[1] - margin:
            data.viewPos[1] += (y - data.viewSize[1] + margin) / \
                ZOOM_FACTOR / data.zoom

    limitView(data)
    recheckCenter(data)
