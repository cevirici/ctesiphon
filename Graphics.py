# # --- Graphics ---
# #
# # - General graphical functions
# #
# # --- --- --- ---

from Geometry import dist

# --- Constants ---

GRASS_COLOR = (131, 214, 131)
DARK_GRASS = (19, 135, 27)
FOREST_COLOR = (19, 82, 11)
OCEAN_COLOR = (125, 144, 225)
DARK_OCEAN = (25, 44, 225)
HIGHLIGHT = (235, 248, 95)
DRY_COLOR = (242, 244, 114)
COLD_COLOR = (99, 235, 255)
HOT_COLOR = (242, 56, 56)
HUD_WOOD = (196, 136, 42)
WOOD_DARK = (128, 90, 30)
WOOD_DARKER = (102, 71, 22)
HUD_GREY = (152, 152, 152)
MENU_COLOR = (0, 0, 0)
HUD_GREEN = (97, 232, 61)
HUD_RED = (220, 84, 84)

LOADING_FONT = ('Bahnschrift', 36)
HUD_FONT = ('Consolas', 16)
HUD_FONT_SMALL = ('Consolas', 11)

BORDER = 15
VIEW_SIZE = [901, 900]
MAP_POS = [26, 32]
MAP_BOUNDS = [MAP_POS[i] + VIEW_SIZE[i] for i in range(2)]
ZOOM_FACTOR = 1.5

# --- End Constants ---


def scale(point, data):
    # Returns the view coordinates of a given points
    return [(point[i] - data.viewPos[i]) * data.zoom + MAP_POS[i]
            for i in range(2)]


def rgbToColor(rgb):
    # Converts a tuple containing RGB values to a color string
    return "#{:0>2x}{:0>2x}{:0>2x}".format(*[int(x) for x in rgb])


def mixColors(rgb_1, rgb_2, factor):
    # Returns the hex code of a linear mix between two RGB triples
    # A factor of 0 gives rgb_1, a factor of 1 gives rgb_2
    return [int(rgb_2[i] * factor + rgb_1[i] * (1 - factor)) for i in range(3)]


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
    data.zoom = max(data.map.cityCount ** 0.5 / 30, data.zoom)
    scale = (1 / data.zoom - 1 / oldZoom)

    # 'Centralize' the target if cursor is off-center
    tracking = factor / 30
    data.viewPos[0] -= (data.width / 2 - x) * tracking + x * scale
    data.viewPos[1] -= (data.height / 2 - y) * tracking + y * scale

    limitView(data)
    recheckCenter(data)


def scroll(data, margin, x, y):
    scrolled = False
    if 0 < x < data.viewSize[0] and 0 < y < data.viewSize[1]:
        if 0 < x < margin:
            if data.scrolling >= data.scrollBuffer:
                data.viewPos[0] -= (margin - x) / ZOOM_FACTOR / data.zoom
            else:
                data.scrolling += 1
            scrolled = True

        elif data.viewSize[0] > x > data.viewSize[0] - margin:
            if data.scrolling >= data.scrollBuffer:
                data.viewPos[0] += (x - data.viewSize[0] + margin) / \
                    ZOOM_FACTOR / data.zoom
            else:
                data.scrolling += 1
            scrolled = True

        if 0 < y < margin:
            if data.scrolling >= data.scrollBuffer:
                data.viewPos[1] -= (margin - y) / ZOOM_FACTOR / data.zoom
            else:
                data.scrolling += 1
            scrolled = True

        elif data.viewSize[1] > y > data.viewSize[1] - margin:
            if data.scrolling >= data.scrollBuffer:
                data.viewPos[1] += (y - data.viewSize[1] + margin) / \
                    ZOOM_FACTOR / data.zoom
            else:
                data.scrolling += 1
            scrolled = True

    if not scrolled:
        data.scrolling = max(0, data.scrollBuffer - 2)

    limitView(data)
    recheckCenter(data)
    return scrolled
