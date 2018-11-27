# # --- Panels ---
# #
# # - Parts of the screen
# #
# # --- --- --- ---

from Culture import *
from Language import *
from Map import *
from Voronoi import *
from Graphics import *
from tkinter import *

MAP_SIZE = 800


class Panel:
    def __init__(self, tag, onDraw, onClick, onScroll, bounds):
        self.tag = tag
        self.onDraw = onDraw
        self.onClick = onClick
        self.onScroll = onScroll
        self.bounds = bounds

    def __hash__(self):
        return hash(self.tag)

    def __repr__(self):
        return self.tag

    def draw(self, canvas, data):
        self.onDraw(canvas, data)

    def inBounds(self, x, y):
        return self.bounds[0][0] <= x <= self.bounds[1][0] and \
            self.bounds[0][1] <= y <= self.bounds[1][1]

    def click(self, coords, data, held):
        if self.inBounds(*coords):
            self.onClick(coords, data, held)
            return True
        else:
            return False

    def scroll(self, coords, data, factor):
        if self.inBounds(*coords):
            self.onScroll(coords, data, factor)
            return True
        else:
            return False

    def wipe(self, canvas):
        canvas.delete(self.tag)

    def redraw(self, canvas, data):
        self.wipe(canvas)
        self.draw(canvas, data)


def removePanel(canvas, data, panel):
    # Remove a panel and wipe it
    panel.wipe(canvas)
    data.panels.remove(panel)


def redrawPanel(canvas, data, panel):
    panel.redraw(canvas, data)
    canvas.update()


def redrawNotMap(canvas, data):
    for panel in data.panels:
        if panel != mapPanel:
            panel.redraw(canvas, data)
    canvas.update()


def redrawAll(canvas, data):
    for panel in data.panels:
        panel.redraw(canvas, data)
    canvas.update()


def noClick(coords, data, held):
    pass


def noScroll(coords, data, factor):
    pass

# --- Preloader ---


def drawPreloader(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height,
                            outline='', fill=rgbToColor(MENU_COLOR),
                            tag='preloader')
    textPos = [data.width / 2, data.height / 2]
    canvas.create_text(textPos, text='Loading, please wait...',
                       font=LOADING_FONT, tag='preloader',
                       fill='white')


preloaderPanel = Panel('preloader', drawPreloader, noClick, noScroll,
                       [[0, 0], [1280, 960]])

# --- Main Menu ---


def drawMenu(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height,
                            outline='', fill=rgbToColor(MENU_COLOR),
                            tag='menu')
    # Background
    canvas.create_image(data.width, data.height + data.offset, anchor=SE,
                        image=data.globeImages[data.globeFrame],
                        tag='menu')
    # Logo
    canvas.create_image(data.width / 2, - data.offset / 2, anchor=N,
                        image=data.logo,
                        tag='menu')

    if data.offset <= 20:
        canvas.create_image(data.width / 2, 450,
                            image=data.menuStart,
                            tag='menu')
    if data.offset == 0:
        canvas.create_image(data.width / 2, 650,
                            image=data.menuLoad,
                            tag='menu')


def makeMap(canvas, data):
    stepAmount = MAP_SIZE // 8

    def mapStep():
        # Advances the map a certain amount, and draws a new brick
        for step in range(stepAmount):
            data.map.step()
        newBrick(canvas, data, data.bricks)
        data.bricks += 1
        redrawPanel(canvas, data, loadPanel)
        redrawPanel(canvas, data, hudPanel)
        canvas.update()

    data.points = [(random() * data.mapSize[0], random() * data.mapSize[1])
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.mapSize[0], data.mapSize[1])
    data.viewPos = [100, 100]
    data.zoom = 3.3
    data.bricks = 0
    # Loading background
    canvas.create_rectangle(MAP_POS, MAP_BOUNDS, outline='',
                            fill=rgbToColor(HUD_WOOD), tag='load')
    menuPanel.wipe(canvas)
    data.panels = [loadPanel, hudPanel]
    redrawAll(canvas, data)

    for i in range(4):
        while not data.map.done:
            mapStep()
        data.loadingMessage = choice(data.messages)
        data.map.reduce()

    data.loadingMessage = choice(data.messages)
    while not data.map.done:
        mapStep()

    data.oldMap = data.map
    data.map = Map(data.map, data)
    initializeTerrain(data.map)
    data.map.spawnCultures()

    canvas.delete('bricks')
    redrawAll(canvas, data)
    removePanel(canvas, data, loadPanel)
    data.panels.insert(0, mapPanel)
    redrawAll(canvas, data)
    data.ticks = -1


def clickMenu(coords, data, held):
    if data.offset == 0:
        # New Game
        if 490 <= coords[0] <= 790 and \
                398 <= coords[1] <= 562:
            makeMap(data.canvas, data)


menuPanel = Panel('menu', drawMenu, clickMenu, noScroll,
                  [[0, 0], [1280, 960]])


# --- Loading Panel ---


def newBrick(canvas, data, index):
    # Call this outside the normal redraw flow - faster
    brickSize = [80, 50]
    rowNum = VIEW_SIZE[0] // brickSize[0] + 1
    y = MAP_BOUNDS[1] - (index // rowNum) * brickSize[1]
    x = MAP_POS[0] + (index % rowNum - 0.5) * brickSize[0]
    if (index // rowNum % 2) == 1:
        x += brickSize[0] / 2
    canvas.create_image(x, y, anchor=SW, image=data.brick, tag='bricks')


def drawLoad(canvas, data):
    textPos = [MAP_POS[0] + VIEW_SIZE[0] / 2, MAP_POS[1] + 30]
    canvas.create_text(textPos, text=data.loadingMessage,
                       font=LOADING_FONT, tag='load')


def clickLoad(coords, data, held):
    pass


loadPanel = Panel('load', drawLoad, clickLoad, noScroll, [[0, 0], [0, 0]])


# --- Map Display ---


def drawMap(canvas, data):
    canvas.create_rectangle(MAP_POS, MAP_BOUNDS, fill=rgbToColor(WOOD_DARK),
                            outline='',
                            tag='map')
    data.map.draw(canvas, data)


def clickMap(coords, data, held):
    x = coords[0] - MAP_POS[0]
    y = coords[1] - MAP_POS[1]
    if 0 < x < VIEW_SIZE[0] and 0 < y < VIEW_SIZE[1]:
        clickPoint = [x / data.zoom + data.viewPos[0],
                      y / data.zoom + data.viewPos[1]]
        closest = data.map.findClosestCity(clickPoint, data)
        if closest:
            data.activeCity = closest
            # If in culture mode, swap to culture
            if culturePanel in data.panels:
                if data.activeCity.maxCulture:
                    data.activeCulture = data.activeCity.maxCulture
                else:
                    data.panels.remove(culturePanel)
                    data.panels.append(cityPanel)
            else:
                if cityPanel in data.panels:
                    data.panels.remove(cityPanel)
                data.panels.append(cityPanel)
        else:
            data.activeCity = None
            data.panels = [mapPanel, hudPanel]

    mapPanel.redraw(data.canvas, data)


def scrollMap(coords, data, factor):
    zoom(data, factor / 120, coords[0], coords[1])


mapPanel = Panel('map', drawMap, clickMap, scrollMap, [MAP_POS, MAP_BOUNDS])


# --- HUD Background ---


def drawHud(canvas, data):
    # Draw the HUD
    canvas.create_image(0, 0, anchor=NW, image=data.hudTop, tag='HUD')
    canvas.create_image(0, 0, anchor=NW, image=data.hudLeft, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE,
                        image=data.hudRight, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE, image=data.hudBot,
                        tag='HUD')

    canvas.create_text(1220, 10, text=data.ticks, tag='HUD')

    # Redraw side buttons
    buttonPositions = [[980 + (i % 5) * 50,
                        140 + (i // 5) * 40] for i in range(len(data.buttons))]
    for i in range(len(buttonPositions)):
        if i == data.drawMode:
            corner = [buttonPositions[i][0] - 22,
                      buttonPositions[i][1] - 17]
            bottomCorner = [corner[0] + 44, corner[1] + 34]
            canvas.create_rectangle(corner, bottomCorner,
                                    fill=rgbToColor(HIGHLIGHT), width=0,
                                    tag='HUD')
        canvas.create_image(buttonPositions[i],
                            image=data.buttons[i],
                            tag='HUD')

    if data.paused:
        canvas.create_rectangle(data.width - 53, 0, data.width, 52,
                                fill=rgbToColor(HIGHLIGHT), width=0,
                                tag='HUD')
    canvas.create_image(data.width, 0, image=data.pauseButton, anchor=NE,
                        tag='HUD')


def clickHud(coords, data, held):
    positions = [[980 + (i % 5) * 50,
                  140 + (i // 5) * 40] for i in range(len(data.buttons))]
    size = [20, 15]
    clicked = False

    # Map Mode buttons
    for i in range(len(positions)):
        if positions[i][0] - size[0] <= coords[0] <= \
                positions[i][0] + size[0] and \
                positions[i][1] - size[1] <= coords[1] <= \
                positions[i][1] + size[1]:
            data.drawMode = i
            clicked = True

    # Pause buttons
    if not held:
        if coords[0] > data.width - 50 and coords[1] < 50:
            data.paused = not data.paused
            clicked = True

        if not clicked and hudPanel.inBounds(coords[0], coords[1]):
            data.activeCity = None
            data.panels = [mapPanel, hudPanel]


hudPanel = Panel('HUD', drawHud, clickHud, noScroll, [[980, 140], [1200, 195]])


# --- City Display ---


def drawCityInfo(canvas, data):
    # Draws the info about tha active city
    ac = data.activeCity

    bgPos = [1096, 521]
    provNamePos = [950, 66]

    provName = printWord(ac.name).capitalize()
    if ac.polity:
        provNamePos = [950, 56]
        polityPos = [950, 76]
        polityName = printWord(ac.polity.name).capitalize()
        canvas.create_text(polityPos, anchor=W, justify='left',
                           text=polityName,
                           fill='white', font=HUD_FONT,
                           tag='city')
    canvas.create_image(bgPos,
                        image=data.sidebarImage,
                        tag='city')
    canvas.create_text(provNamePos, anchor=W, justify='left',
                       text=provName,
                       fill='white', font=HUD_FONT,
                       tag='city')

    totalPopPos = [1148, 255]
    capacityPos = [1180, 255]
    canvas.create_text(totalPopPos, anchor=E, justify='right',
                       text=int(ac.population),
                       fill='white', font=HUD_FONT,
                       tag='city')
    canvas.create_text(capacityPos, anchor=W, justify='left',
                       text=int(ac.capacity),
                       fill='white', font=HUD_FONT,
                       tag='city')

    popText = ""
    popNumsText = ""
    popPos = [953, 340]
    popNumsPos = [1240, 340]
    cultures = sorted(ac.cultures.keys(),
                      key=lambda c: ac.cultures[c],
                      reverse=True)[:5]
    for culture in cultures:
        pop = int(ac.cultures[culture])
        popText += "{}:\n".format(printWord(culture.name).capitalize())
        popNumsText += "{}\n".format(pop)

    canvas.create_text(popPos,
                       text=popText,
                       anchor=NW, justify='left',
                       fill='white', font=HUD_FONT,
                       tag='city')
    canvas.create_text(popNumsPos,
                       text=popNumsText,
                       anchor=NE, justify='right',
                       fill='white', font=HUD_FONT,
                       tag='city')

    fertilityPos = [1000, 562]
    fertility = min(1, ac.fertility)
    fertilityEnd = [fertilityPos[0] + 209 * fertility, fertilityPos[1] + 12]
    canvas.create_rectangle(fertilityPos, fertilityEnd,
                            fill='green', width=0, tag='city')

    tempPos = [1000, 616]
    temp = max(0, ac.temp)
    tempEnd = [tempPos[0] + 209 * temp, tempPos[1] + 12]
    canvas.create_rectangle(tempPos, tempEnd,
                            fill='green', width=0, tag='city')

    progressPos = [1000, 670]
    if ac.maxCulture:
        rate = min(1, ac.progress / ac.currentBuilding.requirement)
    else:
        rate = 0
    progressEnd = [progressPos[0] + 209 * rate, progressPos[1] + 12]
    canvas.create_rectangle(progressPos, progressEnd,
                            fill='green', width=0, tag='city')

    builderPos = [1047, 744]
    soldierPos = [1047, 794]
    supplyPos = [1204, 744]
    canvas.create_text(builderPos,
                       text=int(ac.builders),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='city')
    canvas.create_text(soldierPos,
                       text=int(ac.garrison),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='city')
    canvas.create_text(supplyPos,
                       text=int(ac.supplies),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='city')


def cityClick(coords, data, held):
    popPos = [953, 340]
    popWidth = 250
    lineHeight = 24
    ac = data.activeCity

    # Cultures
    if popPos[0] <= coords[0] <= popPos[0] + popWidth and \
            popPos[1] <= coords[1] <= popPos[1] + lineHeight * 5:
        lineNum = (coords[1] - popPos[1]) // lineHeight
        cultures = sorted(ac.cultures.keys(),
                          key=lambda c: ac.cultures[c],
                          reverse=True)[:5]
        if lineNum < len(cultures):
            data.activeCulture = cultures[lineNum]
            data.panels.remove(cityPanel)
            if culturePanel in data.panels:
                data.panels.remove(culturePanel)
            data.panels.append(culturePanel)


cityPanel = Panel('city', drawCityInfo, cityClick, noScroll,
                  [[936, 221], [1256, 821]])


# --- Culture Display ---


def drawSlider(canvas, position, fillness, tag):
    # Sizes are constant
    sliderWidth = 220
    sliderHeight = 20
    radius = sliderHeight / 2
    startX = position[0]
    startY = position[1]
    margin = 2

    canvas.create_rectangle(startX + radius, startY,
                            startX + sliderWidth - radius,
                            startY + sliderHeight,
                            fill=rgbToColor(WOOD_DARKER), outline='',
                            tag=tag)

    # Bevels
    canvas.create_oval(startX, startY,
                       startX + sliderHeight,
                       startY + sliderHeight - 1,
                       fill=rgbToColor(WOOD_DARKER), outline='', tag=tag)
    canvas.create_oval(startX + sliderWidth - sliderHeight, startY,
                       startX + sliderWidth,
                       startY + sliderHeight - 1,
                       fill=rgbToColor(WOOD_DARKER), outline='', tag=tag)

    # Inner bar
    canvas.create_rectangle(startX + radius, startY + margin,
                            startX + sliderWidth - radius,
                            startY + sliderHeight - margin,
                            fill=rgbToColor(HUD_GREY), outline='',
                            tag=tag)

    barX = startX + radius + (sliderWidth - 2 * radius) * fillness
    canvas.create_rectangle(startX + radius, startY + margin,
                            barX,
                            startY + sliderHeight - margin,
                            fill=rgbToColor(GRASS_COLOR), outline='',
                            tag=tag)

    # Dragger Ball
    canvas.create_oval(barX - radius + margin,
                       startY + margin,
                       barX + radius - margin,
                       startY + sliderHeight - margin,
                       fill=rgbToColor(WOOD_DARKER), outline='',
                       tag=tag)


def cultureDraw(canvas, data):
    ac = data.activeCulture

    # Culture name and color
    cultureNamePos = [950, 66]

    cultureName = printWord(ac.name).capitalize()
    canvas.create_text(cultureNamePos, anchor=W, justify='left',
                       text=cultureName,
                       fill='white', font=HUD_FONT,
                       tag='culture')

    cultureColorPos = [[1180, 60], [1192, 72]]
    canvas.create_rectangle(cultureColorPos,
                            fill=rgbToColor(ac.color), tag='culture')

    quantities = [ac.idealTemp,
                  ac.idealAltitude,
                  ac.coastal]
    for trait in ac.traits:
        quantities.append((ac.traits[trait] - trait.range[0]) /
                          (trait.range[1] - trait.range[0]))

    # Background
    bgPos = [1096, 521]
    canvas.create_image(bgPos,
                        image=data.cultureImage,
                        tag='culture')

    for i in range(len(data.cultureIcons)):
        position = (980, 300 + i * 60 - culturePanel.scrollPos[0])
        # check if position is inbounds
        if 260 < position[1] < 450:
            canvas.create_image(position, image=data.cultureIcons[i],
                                tag='culture')
            drawSlider(canvas, (position[0] + 35, position[1] - 10),
                       quantities[i], 'culture')

    # Supercultures and Subcultures
    superPos = [955, 535]
    subPos = [955, 630]
    position = superPos
    for culture in ac.superCultures:
        canvas.create_text(position,
                           justify='left', anchor=W,
                           fill='white', font=HUD_FONT,
                           text=printWord(culture.name).capitalize(),
                           tag='culture')
        position[1] += 24

    subCultures = []
    for cList in ac.subCultures.values():
        for culture in cList:
            subCultures.append(culture)
    subCultures.sort()

    culturePanel.scrollPos[1] = max(0, min(culturePanel.scrollPos[1],
                                           len(subCultures) - 7))
    index = culturePanel.scrollPos[1]

    position = subPos
    for culture in subCultures[index: index + 6]:
        canvas.create_text(position,
                           justify='left', anchor=W,
                           fill='white', font=HUD_FONT,
                           text=printWord(culture.name).capitalize(),
                           tag='culture')
        position[1] += 24


def cultureClick(coords, data, held):
    ac = data.activeCulture
    sliderWidth = 180
    sliderHeight = 40
    for i in range(len(data.cultureIcons)):
        position = (990, 290 + i * 60 - culturePanel.scrollPos[0])
        bounds = [position[0] + sliderWidth, position[1] + sliderHeight]
        # check if position is inbounds
        superPos = 523
        subPos = 618
        lineHeight = 24

        if 260 < position[1] < 470:
            if position[0] < coords[0] < bounds[0] and \
                    position[1] < coords[1] < bounds[1]:
                value = (coords[0] - position[0]) / sliderWidth

                # Massive if statement to set the correct value
                if i == 0:
                    ac.idealTemp = value
                elif i == 1:
                    ac.idealAltitude = value
                elif i == 2:
                    ac.coastal = value
                elif i in range(3, 11):
                    # Traits
                    traits = [Culture.AGRICULTURALIST, Culture.BIRTHRATE,
                              Culture.MIGRATORY,
                              Culture.EXPLORATIVE, Culture.HARDINESS,
                              Culture.TOLERANT, Culture.INNOVATION,
                              Culture.MILITANCE]
                    trait = traits[i - 3]
                    scaledValue = trait.range[0] + \
                        value * (trait.range[1] - trait.range[0])
                    ac.traits[trait] = scaledValue

                culturePanel.redraw(data.canvas, data)
                break
        # Supercultures
        elif superPos < coords[1] < superPos + 75:
            lineNum = (coords[1] - superPos) // lineHeight
            if lineNum < len(ac.superCultures):
                data.activeCulture = list(ac.superCultures)[lineNum]
        elif subPos < coords[1] < subPos + 145:
            lineNum = (coords[1] - subPos) // lineHeight
            lineNum += culturePanel.scrollPos[1]
            subCultures = []
            for cList in ac.subCultures.values():
                for culture in cList:
                    subCultures.append(culture)
            subCultures.sort()

            if lineNum < len(subCultures):
                data.activeCulture = subCultures[lineNum]


def scrollCulture(coords, data, factor):
    if 260 < coords[1] < 470:
        culturePanel.scrollPos[0] -= factor / 2
        culturePanel.scrollPos[0] = max(0, min(480, culturePanel.scrollPos[0]))
        culturePanel.redraw(data.canvas, data)
    elif coords[1] > 630:
        culturePanel.scrollPos[1] += 1 if factor > 0 else -1
        culturePanel.scrollPos[1] = max(0, culturePanel.scrollPos[1])


culturePanel = Panel('culture', cultureDraw, cultureClick, scrollCulture,
                     [[900, 221], [1280, 960]])
culturePanel.scrollPos = [0, 0]
