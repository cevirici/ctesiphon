from tkinter import *
from Voronoi import *
from Map import *
from Terrain import *
from random import *
from PIL import ImageTk

MAP_SIZE = 800


def loadImages(data):
    # Preload images into data
    buttonimages = ['button-terrain.png',
                    'button-water.png',
                    'button-temp.png',
                    'button-farm.png',
                    'button-vegetation.png',
                    'button-culture.png',
                    'button-polity.png']
    data.buttons = []
    for i in range(len(buttonimages)):
        data.buttons.append(ImageTk.PhotoImage(file='img\\' + buttonimages[i]))
    data.sidebarImage = ImageTk.PhotoImage(file='img\\cityHud.png')

    data.hudTop = ImageTk.PhotoImage(file='img\\interfaceTop.png')
    data.hudLeft = ImageTk.PhotoImage(file='img\\interfaceLeft.png')
    data.hudBot = ImageTk.PhotoImage(file='img\\interfaceBot.png')
    data.hudRight = ImageTk.PhotoImage(file='img\\interfaceRight.png')
    data.pauseButton = ImageTk.PhotoImage(file='img\\button-pause.png')


def redrawSideButtons(canvas, data):
    # Redraws the sidebar buttons
    buttonPositions = [[980 + (i % 5) * 50,
                        140 + (i // 5) * 40] for i in range(7)]
    for i in range(len(buttonPositions)):
        if i == data.drawMode:
            corner = [buttonPositions[i][0] - 22,
                      buttonPositions[i][1] - 17]
            bottomCorner = [corner[0] + 44, corner[1] + 34]
            canvas.create_rectangle(corner, bottomCorner,
                                    fill=rgbToColor(HIGHLIGHT), width=0)
        canvas.create_image(buttonPositions[i],
                            image=data.buttons[i],
                            tag='HUD')

    if data.paused:
        canvas.create_rectangle(data.width - 53, 0, data.width, 52,
                                fill=rgbToColor(HIGHLIGHT), width=0,
                                tag='HUD')
    canvas.create_image(data.width, 0, image=data.pauseButton, anchor=NE,
                        tag='HUD')


def drawCityInfo(canvas, data):
    # Draws the info about tha active city
    ac = data.activeCity

    provNamePos = [950, 53]
    sidebarPos = [1096, 500]
    popPos = [953, 340]
    popNumsPos = [1240, 340]
    canvas.create_image(sidebarPos,
                        image=data.sidebarImage,
                        tag='HUD')
    canvas.create_text(provNamePos, anchor=NW, justify='left',
                       text=printWord(ac.name).capitalize(),
                       fill='white', font=HUD_FONT,
                       tag='HUD')

    totalPopPos = [1148, 256]
    capacityPos = [1180, 256]
    canvas.create_text(totalPopPos, anchor=E, justify='right',
                       text=int(ac.population),
                       fill='white', font=HUD_FONT,
                       tag='HUD')
    canvas.create_text(capacityPos, anchor=W, justify='left',
                       text=int(ac.capacity),
                       fill='white', font=HUD_FONT,
                       tag='HUD')

    popText = ""
    popNumsText = ""
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
                       tag='HUD')
    canvas.create_text(popNumsPos,
                       text=popNumsText,
                       anchor=NE, justify='right',
                       fill='white', font=HUD_FONT,
                       tag='HUD')

    fertilityPos = [1000, 562]
    fertility = min(1, ac.fertility)
    fertilityEnd = [fertilityPos[0] + 209 * fertility, fertilityPos[1] + 12]
    canvas.create_rectangle(fertilityPos, fertilityEnd,
                            fill='green', width=0, tag='HUD')

    tempPos = [1000, 616]
    temp = max(0, ac.temp)
    tempEnd = [tempPos[0] + 209 * temp, tempPos[1] + 12]
    canvas.create_rectangle(tempPos, tempEnd,
                            fill='green', width=0, tag='HUD')

    progressPos = [1000, 670]
    if ac.maxCulture:
        diff = (ac.population - ac.difficulty) / ac.difficulty
        diff = max(0, diff)
        progress = ac.maxCulture['INNOV'] * diff * (1 - ac.vegetation)
        rate = progress / (5 * ac.difficulty ** 0.5)
    else:
        rate = 0
    progressEnd = [progressPos[0] + 209 * rate, progressPos[1] + 12]
    canvas.create_rectangle(progressPos, progressEnd,
                            fill='green', width=0, tag='HUD')

    infraPos = [1150, 732]
    canvas.create_text(infraPos,
                       text=int(ac.infrastructure * 10),
                       anchor=NE, justify='right',
                       fill='white', font=HUD_FONT,
                       tag='HUD')


def redrawHud(canvas, data):
    # Redraws the interface
    canvas.create_image(0, 0, anchor=NW, image=data.hudTop, tag='HUD')
    canvas.create_image(0, 0, anchor=NW, image=data.hudLeft, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE,
                        image=data.hudRight, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE, image=data.hudBot,
                        tag='HUD')
    redrawSideButtons(canvas, data)

    canvas.create_text(1220, 10, text=data.ticks)

    if data.activeCity:
        drawCityInfo(canvas, data)


def keyPressed(event, data):
    if event.keysym == 'k':
        data.drawMode += 1
        if data.drawMode == 7:
            data.drawMode = 0
    elif event.keysym == 'l':
        data.map.update()
    elif event.keysym == 'p':
        data.paused = not data.paused
    elif event.keysym == 'n':
        data.tickRate -= 2
        data.ticks = 0
    elif event.keysym == 'm':
        data.tickRate += 2
        data.ticks = 0


def checkButtonPresses(event, data):
    # Check for clicking on interface buttons
    positions = [[980 + (i % 5) * 50,
                  140 + (i // 5) * 40] for i in range(7)]
    size = [20, 15]
    for i in range(len(positions)):
        if positions[i][0] - size[0] <= event.x <= \
                positions[i][0] + size[0] and \
                positions[i][1] - size[1] <= event.y <= \
                positions[i][1] + size[1]:
            data.drawMode = i

    if event.x > data.width - 50 and event.y < 50:
        data.paused = not data.paused


def mousePressed(event, data):
    if isinstance(data.map, Map):
        x = event.x - data.mapPos[0]
        y = event.y - data.mapPos[1]
        if 0 < x < data.viewSize[0] and 0 < y < data.viewSize[1]:
            clickPoint = [x / data.zoom + data.viewPos[0],
                          y / data.zoom + data.viewPos[1]]
            closest = data.map.findClosestCity(clickPoint, data)
            if closest:
                data.activeCity = closest
            else:
                data.activeCity = None

    checkButtonPresses(event, data)


def mouseWheel(event, data):
    # Handle zooming
    # The amount to zoom by
    factor = event.delta / 120
    zoom(data, factor, event.x, event.y)


def redrawAll(canvas, data):
    # Calls each draw function
    data.map.draw(canvas, data)
    redrawHud(canvas, data)


def redrawHudWrapper(canvas, data):
    canvas.delete('HUD')
    redrawHud(canvas, data)
    canvas.update()


def redrawAllWrapper(canvas, data):
    # Wrapper for redraw events
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, data.width, data.height,
                            fill='#5E3C11', width=0)
    redrawAll(canvas, data)
    canvas.update()


def timerFired(canvas, data):
    updateMap = False
    # Handle scrolling
    SCROLL_MARGINS = 250
    x = data.root.winfo_pointerx() - data.root.winfo_rootx() - data.mapPos[0]
    y = data.root.winfo_pointery() - data.root.winfo_rooty() - data.mapPos[1]
    if scroll(data, SCROLL_MARGINS, x, y):
        updateMap = True
    if not data.paused:
        data.ticks += 1
        if data.ticks == data.tickRate:
            data.ticks = 0
            if isinstance(data.map, Map):
                data.map.update()
                updateMap = True

    if updateMap:
        redrawAllWrapper(canvas, data)
    else:
        redrawHudWrapper(canvas, data)


def makeMap(canvas, data):
    data.points = [(random() * data.mapSize[0], random() * data.mapSize[1])
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.viewSize[0], data.viewSize[1])
    data.viewPos = [100, 100]
    data.zoom = 3.3
    redrawAllWrapper(canvas, data)

    for i in range(4):
        data.map.fullParse()
        data.loadingMessage = 'Applying Reduction {}'.format(i + 1)
        redrawAllWrapper(canvas, data)
        data.map.reduce()

    data.map.fullParse()
    redrawAllWrapper(canvas, data)

    data.oldMap = data.map
    data.map = Map(data.map, data)
    initializeTerrain(data.map)
    data.map.spawnCultures()
    redrawAllWrapper(canvas, data)
    data.ticks = -1


def init(canvas, data):
    data.activeCity = None
    data.mapPos = [30, 30]
    data.viewSize = [900, 900]
    data.mapSize = data.viewSize
    data.timerDelay = 10
    data.loadingMessage = 'Generating Initial Map'
    data.drawMode = 5
    data.ticks = 0
    data.tickRate = 10
    data.paused = False

    loadImages(data)
    makeMap(canvas, data)


def setup(data):
    def keyPressedWrapper(event, data):
        keyPressed(event, data)
        redrawAllWrapper(data.canvas, data)

    def mousePressedWrapper(event, data):
        mousePressed(event, data)
        redrawAllWrapper(data.canvas, data)

    def mouseWheelWrapper(event, data):
        mouseWheel(event, data)
        redrawAllWrapper(data.canvas, data)

    def mouseMotionWrapper(event, data):
        mouseMotion(event, data)
        redrawAllWrapper(data.canvas, data)

    windowSize = [1280, 960]
    data.width = windowSize[0]
    data.height = windowSize[1]
    data.root = Tk()
    data.root.resizable(width=False, height=False)  # prevents resizing window

    data.canvas = Canvas(data.root, width=windowSize[0], height=windowSize[1])
    data.canvas.configure(bd=0, highlightthickness=0)
    data.canvas.pack()
    # create the root and the canvas
    # set up events
    data.root.bind("<Key>", lambda event:
                   keyPressedWrapper(event, data))
    data.root.bind("<Button-1>", lambda event:
                   mousePressedWrapper(event, data))
    data.root.bind("<MouseWheel>", lambda event:
                   mouseWheelWrapper(event, data))


def run():
    def timerFiredWrapper(canvas, data):
        timerFired(canvas, data)

        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)

    class Struct(object):
        pass
    data = Struct()
    setup(data)
    # Size the window appropriately
    init(data.canvas, data)
    timerFiredWrapper(data.canvas, data)
    # and launch the app
    data.root.mainloop()  # blocks until window is closed


run()
