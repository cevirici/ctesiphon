from tkinter import *
from Voronoi import *
from Map import *
from Terrain import *
from random import *
from Panels import *
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
                    'button-polity.png',
                    'button-pop.png']
    data.buttons = []
    for i in range(len(buttonimages)):
        data.buttons.append(ImageTk.PhotoImage(file='img\\' + buttonimages[i]))
    data.sidebarImage = ImageTk.PhotoImage(file='img\\cityHud.png')

    data.hudTop = ImageTk.PhotoImage(file='img\\interfaceTop.png')
    data.hudLeft = ImageTk.PhotoImage(file='img\\interfaceLeft.png')
    data.hudBot = ImageTk.PhotoImage(file='img\\interfaceBot.png')
    data.hudRight = ImageTk.PhotoImage(file='img\\interfaceRight.png')
    data.pauseButton = ImageTk.PhotoImage(file='img\\button-pause.png')

    cultureIcons = ['culture-temp.png', 'culture-altitude.png',
                    'culture-coastal.png', 'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png',
                    'culture-temp.png']
    data.cultureIcons = []
    for i in range(len(cultureIcons)):
        data.cultureIcons.append(ImageTk.PhotoImage(file='img\\' +
                                                    cultureIcons[i]))


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
        for war in War.wars:
            print('Attackers:')
            for polity in war.attackers:
                print(printWord(polity.name).capitalize(), end=', ')
            print('Defenders:')
            for polity in war.defenders:
                print(printWord(polity.name).capitalize(), end=', ')


def mousePressed(coords, data):
    # Bubble click events in reverse order
    for panel in data.panels[::-1]:
        if panel.click(coords, data):
            return


def mouseReleased(event, data):
    data.clicking = False


def mouseWheel(event, data):
    # Handle zooming
    # The amount to zoom by
    factor = event.delta / 120
    zoom(data, factor, event.x, event.y)


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


def timerFired(canvas, data):
    # Handle scrolling
    updateMap = False
    SCROLL_MARGINS = 250
    x = data.root.winfo_pointerx() - data.root.winfo_rootx() - MAP_POS[0]
    y = data.root.winfo_pointery() - data.root.winfo_rooty() - MAP_POS[1]
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
        # Not calling redrawPanel here, because we should only update canvas
        # once
        mapPanel.redraw(canvas, data)

    if data.clicking:
        mousePressed([data.root.winfo_pointerx() - data.root.winfo_rootx(),
                      data.root.winfo_pointery() - data.root.winfo_rooty()],
                     data)

    redrawNotMap(canvas, data)


def makeMap(canvas, data):
    data.points = [(random() * data.mapSize[0], random() * data.mapSize[1])
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.mapSize[0], data.mapSize[1])
    data.viewPos = [100, 100]
    data.zoom = 3.3
    redrawAll(canvas, data)

    for i in range(4):
        data.map.fullParse()
        data.loadingMessage = 'Applying Reduction {}'.format(i + 1)
        redrawAll(canvas, data)
        data.map.reduce()

    data.map.fullParse()
    redrawAll(canvas, data)

    data.oldMap = data.map
    data.map = Map(data.map, data)
    initializeTerrain(data.map)
    data.map.spawnCultures()

    removePanel(canvas, data, loadPanel)
    data.panels.insert(0, mapPanel)
    redrawAll(canvas, data)
    data.ticks = -1


def init(canvas, data):
    data.timerDelay = 10
    data.ticks = 0
    data.tickRate = 10
    data.scrollBuffer = 8
    data.scrolling = 0
    data.paused = False
    data.clicking = False

    data.panels = [loadPanel, hudPanel]
    data.activeCity = None

    data.mapSize = [MAP_SIZE, MAP_SIZE]
    data.viewSize = VIEW_SIZE

    data.loadingMessage = 'Generating Initial Map'
    data.drawMode = 5

    loadImages(data)

    makeMap(canvas, data)


def setup(data):
    def keyPressedWrapper(event, data):
        keyPressed(event, data)
        redrawAll(data.canvas, data)

    def mousePressedWrapper(event, data):
        data.clicking = True
        mousePressed([event.x, event.y], data)
        redrawAll(data.canvas, data)

    def mouseWheelWrapper(event, data):
        mouseWheel(event, data)
        redrawAll(data.canvas, data)

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
    data.root.bind("<ButtonRelease-1>", lambda event:
                   mouseReleased(event, data))
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
