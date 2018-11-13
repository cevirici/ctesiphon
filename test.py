from tkinter import *
from Voronoi import *
from Terrain import *
from random import *

MAP_SIZE = 4000


def keyPressed(event, data):
    if event.keysym in ['Left', 'Right', 'Up', 'Down']:
        mode = ['Left', 'Right', 'Up', 'Down'].index(event.keysym)
        shift = [(-10, 0), (10, 0), (0, -10), (0, 10)][mode]
        data.viewPos = [data.viewPos[i] + shift[i] for i in range(2)]
    elif event.keysym == 'k':
        temp = data.map
        data.map = data.oldMap
        data.oldMap = temp
    elif event.keysym == 'p':
        print(data.root.winfo_pointerxy())


def redrawAll(canvas, data):
    data.map.draw(canvas, data)


def redrawAllWrapper(canvas, data):
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, data.width, data.height,
                            fill='#5E3C11', width=0)
    redrawAll(canvas, data)
    canvas.update()


def mouseWheel(event, data):
    # Handle zooming
    # The amount to zoom by
    factor = event.delta / 120
    zoom(data, factor, event.x, event.y)


def timerFired(data):
    # Handle scrolling
    SCROLL_MARGINS = 150
    relX = data.root.winfo_pointerx() - data.root.winfo_rootx()
    relY = data.root.winfo_pointery() - data.root.winfo_rooty()
    scroll(data, SCROLL_MARGINS, relX, relY)


def makeMap(canvas, data):
    data.points = [(random() * data.width, random() * data.height)
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.width, data.height)
    data.viewPos = [100, 100]
    data.zoom = 3.5
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
    data.map.spawnLand()
    data.map.generateRivers()
    redrawAllWrapper(canvas, data)


def init(canvas, data):
    data.viewSize = [700, 700]
    data.timerDelay = 10
    data.loadingMessage = 'Generating Initial Map'

    makeMap(canvas, data)


def run(width=700, height=700):
    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def mouseWheelWrapper(event, canvas, data):
        mouseWheel(event, data)
        redrawAllWrapper(canvas, data)

    def mouseMotionWrapper(event, canvas, data):
        mouseMotion(event, data)
        redrawAllWrapper(canvas, data)

    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)
        # pause, then call timerFired again
        canvas.after(data.timerDelay, timerFiredWrapper, canvas, data)

    # Set up data and call init
    class Struct(object):
        pass
    data = Struct()
    # Size the window appropriately
    data.width = width
    data.height = height
    data.root = Tk()
    data.root.resizable(width=False, height=False)  # prevents resizing window
    canvas = Canvas(data.root, width=data.width, height=data.height)
    canvas.configure(bd=0, highlightthickness=0)
    canvas.pack()
    # create the root and the canvas
    # set up events
    data.root.bind("<Key>", lambda event:
                   keyPressedWrapper(event, canvas, data))
    data.root.bind("<MouseWheel>", lambda event:
                   mouseWheelWrapper(event, canvas, data))
    init(canvas, data)
    timerFiredWrapper(canvas, data)
    # and launch the app
    data.root.mainloop()  # blocks until window is closed


run()
