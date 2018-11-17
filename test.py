from tkinter import *
from Voronoi import *
from Map import *
from Terrain import *
from random import *
from PIL import ImageTk

MAP_SIZE = 4000


def redrawHud(canvas, data):
    # Redraws the interface
    data.hudTop = ImageTk.PhotoImage(file='img\\interfaceTop.png')
    data.hudLeft = ImageTk.PhotoImage(file='img\\interfaceLeft.png')
    data.hudBot = ImageTk.PhotoImage(file='img\\interfaceBot.png')
    data.hudRight = ImageTk.PhotoImage(file='img\\interfaceRight.png')

    canvas.create_image(0, 0, anchor=NW, image=data.hudTop, tag='HUD')
    canvas.create_image(0, 0, anchor=NW, image=data.hudLeft, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE,
                        image=data.hudRight, tag='HUD')
    canvas.create_image(data.width, data.height, anchor=SE, image=data.hudBot,
                        tag='HUD')

    provNamePos = [950, 53]
    provWetnessPos = [950, 150]
    moreDataPos = [950, 200]
    morerDataPos = [950, 250]
    popPos = [950, 350]
    popNumsPos = [1260, 350]

    canvas.create_text(1250, 10, text=data.ticks)
    if data.activeCity:
        canvas.create_text(provNamePos, anchor=NW, justify='left',
                           text=printWord(data.activeCity.name).capitalize(),
                           fill='white', font=HUD_FONT,
                           tag='HUD')
        canvas.create_text(provWetnessPos, anchor=NW, justify='left',
                           text=data.activeCity.infrastructure * 100,
                           fill='white', font=HUD_FONT,
                           tag='HUD')
        if data.activeCity.polity:
            canvas.create_text(moreDataPos, anchor=NW, justify='left',
                               text=data.activeCity.polity.influence(data.activeCity),
                               fill='white', font=HUD_FONT,
                               tag='HUD')
        canvas.create_text(morerDataPos, anchor=NW, justify='left',
                           text=int(data.activeCity.population),
                           fill='white', font=HUD_FONT,
                           tag='HUD')

        popText = ""
        popNumsText = ""
        cultures = sorted(data.activeCity.cultures.keys(),
                          key=lambda c: data.activeCity.cultures[c],
                          reverse=True)
        for culture in cultures:
            pop = int(data.activeCity.cultures[culture])
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

        if data.activeCity.maxCulture:
            mc = data.activeCity.maxCulture
            baseString = 'A:{}\nB:{}\nM:{}\nE:{}\nT:{}'
            dataString = baseString.format(*mc.traits.values())
            canvas.create_text([950, 600],
                               text=dataString,
                               anchor=NW, justify='left',
                               fill='white', font=HUD_FONT,
                               tag='HUD')


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
