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
import pickle
import os


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
    canvas.delete(ALL)
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
    stepAmount = data.cityCount // 8

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
                   for i in range(data.cityCount)]
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
            menuPanel.wipe(data.canvas)
            data.panels = [newGamePanel]
            redrawAll(data.canvas, data)

        # Load Game
        if 490 <= coords[0] <= 790 and \
                550 <= coords[1] <= 762:
            data.panels.append(loadMenuPanel)
            redrawAll(data.canvas, data)


menuPanel = Panel('menu', drawMenu, clickMenu, noScroll,
                  [[0, 0], [1280, 960]])


# --- Load Menu ---


def loadGame(canvas, data, saveGame):
    f = open('savefiles/' + saveGame, 'rb')
    data.map, Culture, Polity, Building = pickle.load(f)
    f.close()

    data.viewPos = [100, 100]
    data.zoom = 3.3

    for panel in data.panels:
        panel.wipe(canvas)
    data.panels = [mapPanel, hudPanel]
    redrawAll(canvas, data)
    data.ticks = -1


def drawLoadMenu(canvas, data):
    canvas.create_rectangle(400, 320, 860, 800,
                            fill=rgbToColor(HUD_WOOD),
                            outline=rgbToColor(WOOD_DARKER),
                            width=8, tag='loadMenu')
    position = [410, 350]
    data.savegames = os.listdir('savefiles')
    for file in data.savegames:
        color = 'white'
        if data.saveName == file:
            canvas.create_rectangle(400, position[1] - 12,
                                    860, position[1] + 12,
                                    fill=rgbToColor(HIGHLIGHT), tag='loadMenu',
                                    outline='')
            color = 'black'
        canvas.create_text(position,
                           fill=color, font=HUD_FONT,
                           anchor=W, justify='left',
                           text=file, tag='loadMenu')
        position[1] += 24

    canvas.create_image(420, 880,
                        image=data.menuBase,
                        tag='loadMenu')
    canvas.create_text(420, 880, fill='white',
                       font=LOADING_FONT, text='Back',
                       tag='loadMenu')

    canvas.create_image(860, 880,
                        image=data.menuBase,
                        tag='loadMenu')
    canvas.create_text(860, 880, fill='white',
                       justify='center',
                       font=LOADING_FONT, text='Load\nGame',
                       tag='loadMenu')


def clickLoadMenu(coords, data, held):
    if 270 <= coords[0] <= 570 and \
            798 <= coords[1] <= 962:
        data.panels.remove(loadMenuPanel)
        redrawAll(data.canvas, data)
    elif 710 <= coords[0] <= 1010 and \
            798 <= coords[1] <= 962:
        if data.saveName:
            loadGame(data.canvas, data, data.saveName)
    elif 400 <= coords[0] <= 860 and \
            338 <= coords[1] <= 800:
        lineNum = (coords[1] - 338) // 24
        if lineNum >= 0 and lineNum < len(data.savegames):
            data.saveName = data.savegames[lineNum]


loadMenuPanel = Panel('loadMenu', drawLoadMenu, clickLoadMenu, noScroll,
                      [[0, 0], [1280, 960]])


# --- New Game ---


def drawNewGame(canvas, data):
    canvas.create_rectangle(0, 0, data.width, data.height,
                            outline='', fill=rgbToColor(MENU_COLOR),
                            tag='newGame')
    # Background
    canvas.create_image(data.width, data.height, anchor=SE,
                        image=data.globeImages[data.globeFrame],
                        tag='newGame')
    # Logo
    canvas.create_image(data.width / 2, 0, anchor=N,
                        image=data.logo,
                        tag='newGame')

    canvas.create_image(data.width / 2, 450,
                        image=data.menuBase,
                        tag='newGame')
    canvas.create_text(data.width / 2, 350, fill='white',
                       font=HUD_FONT, text="Map Size",
                       tag='newGame')
    canvas.create_text(data.width / 2, 450, fill='white',
                       font=LOADING_FONT, text=data.sizeText[data.size],
                       tag='newGame')
    canvas.create_image(490, 450, image=data.menuLeft,
                        tag='newGame')
    canvas.create_image(805, 450, image=data.menuRight,
                        tag='newGame')

    typingImage = data.menuLongActive if data.typing else data.menuLong
    canvas.create_image(data.width / 2, 650,
                        image=typingImage,
                        tag='newGame')
    canvas.create_text(data.width / 2, 550, fill='white',
                       font=HUD_FONT, text="World Name",
                       tag='newGame')
    canvas.create_text(data.width / 2, 650, fill='white',
                       font=LOADING_FONT, text=data.saveName,
                       tag='newGame')

    canvas.create_image(data.width / 2, 850,
                        image=data.menuBase,
                        tag='newGame')
    canvas.create_text(data.width / 2, 850, fill='white',
                       justify='center',
                       font=LOADING_FONT, text='Start\nGame',
                       tag='newGame')


def clickNewGame(coords, data, held):
    if 445 <= coords[0] <= 535 and \
            380 <= coords[1] <= 523:
        data.size = max(0, data.size - 1)

    if 760 <= coords[0] <= 850 and \
            380 <= coords[1] <= 523:
        data.size = min(len(data.sizeNums) - 1, data.size + 1)

    if 530 <= coords[0] <= 750 and \
            620 <= coords[1] <= 680:
        data.typing = True
    else:
        data.typing = False

    if 550 <= coords[0] <= 730 and \
            810 <= coords[1] <= 890:
        if data.saveName == '':
            data.typing = True
        else:
            newGamePanel.wipe(data.canvas)
            makeMap(data.canvas, data)
    newGamePanel.redraw(data.canvas, data)


newGamePanel = Panel('newGame', drawNewGame, clickNewGame, noScroll,
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
    canvas.create_image(data.width - 55, 0, image=data.speedControls,
                        anchor=NE, tag='HUD')
    ticks = (12 - data.tickRate) // 2
    for i in range(ticks):
        x = data.width - 65
        y = 39 - i * 9
        canvas.create_rectangle(x, y, x + 7, y + 7,
                                fill=rgbToColor(HIGHLIGHT),
                                outline='',
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

    if not held:
        # Pause button
        if coords[0] > data.width - 50 and coords[1] < 50:
            data.paused = not data.paused
            clicked = True

        # Speed control
        if data.width - 75 < coords[0] < data.width - 55 and \
                coords[1] < 50:
            if coords[1] < 25:
                data.tickRate -= 2
            else:
                data.tickRate += 2
            data.tickRate = min(10, max(2, data.tickRate))
            clicked = True

        if not clicked and hudPanel.inBounds(coords[0], coords[1]):
            data.activeCity = None
            data.panels = [mapPanel, hudPanel]


hudPanel = Panel('HUD', drawHud, clickHud, noScroll, [[940, 0], [1280, 195]])


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

    if not held:
        if 1206 <= coords[0] <= 1243 and \
                291 <= coords[1] <= 325:
            data.panels.append(buildingPanel)
            redrawAll(data.canvas, data)


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
    subCultures.sort(key=lambda c: c.name)

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
        position = (1020, 290 + i * 60 - culturePanel.scrollPos[0])
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
            subCultures.sort(key=lambda c: c.name)

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


# --- Building Display ---

def drawBuilding(canvas, data):
    # Draw City name and Polity name
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
                           tag='building')
    canvas.create_image(bgPos,
                        image=data.buildingImage,
                        tag='building')
    canvas.create_text(provNamePos, anchor=W, justify='left',
                       text=provName,
                       fill='white', font=HUD_FONT,
                       tag='building')

    position = [950, 390]
    for building in buildings:
        if building in ac.buildings:
            color = 'white'
        else:
            color = 'grey'
        canvas.create_text(position,
                           justify='left', anchor=W,
                           text=building.name,
                           font=HUD_FONT, fill=color,
                           tag='building')
        position[1] += 24
        canvas.create_text(position,
                           justify='left', anchor=W,
                           text=building.description,
                           font=HUD_FONT_SMALL, fill=color,
                           tag='building')
        position[1] += 24


def clickBuilding(coords, data, held):
    if not held:
        if 1206 <= coords[0] <= 1243 and \
                291 <= coords[1] <= 325:
            data.panels.remove(buildingPanel)
            redrawAll(data.canvas, data)


buildingPanel = Panel('building', drawBuilding, clickBuilding, noScroll,
                      [[900, 221], [1280, 960]])
