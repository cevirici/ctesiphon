from tkinter import *
from Voronoi import *
from Map import *
from Terrain import *
from random import *
from HUD import *
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


def keyPressed(event, data):
    if event.keysym == 'k':
        data.drawMode += 1
        if data.drawMode == 8:
            data.drawMode = 0
    elif event.keysym == 'l':
        data.map.update(data)
    elif event.keysym == 'p':
        data.paused = not data.paused
    elif event.keysym == 'n':
        data.tickRate -= 2
        data.ticks = 0
    elif event.keysym == 'm':
        data.tickRate += 2
        data.ticks = 0
    elif event.keysym == 'x':
        data.activeCity.polity.mobilize(data.activeCity)


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
                data.map.update(data)
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
