from tkinter import *
from Voronoi import *
from Terrain import *
from random import *
from PIL import ImageTk

MAP_SIZE = 4000


def timerFired(data):
    # Handle scrolling
    SCROLL_MARGINS = 250
    x = data.root.winfo_pointerx() - data.root.winfo_rootx() - data.mapPos[0]
    y = data.root.winfo_pointery() - data.root.winfo_rooty() - data.mapPos[1]
    scroll(data, SCROLL_MARGINS, x, y)


def redrawHud(canvas, data):
    # Redraws the interface
    data.hudTop = ImageTk.PhotoImage(file='img\\interfaceTop.png')
    data.hudLeft = ImageTk.PhotoImage(file='img\\interfaceLeft.png')
    data.hudBot = ImageTk.PhotoImage(file='img\\interfaceBot.png')
    data.hudRight = ImageTk.PhotoImage(file='img\\interfaceRight.png')

    canvas.create_image(0, 0, anchor=NW, image=data.hudTop)
    canvas.create_image(0, 0, anchor=NW, image=data.hudLeft)
    canvas.create_image(data.width, data.height, anchor=SE,
                        image=data.hudRight)
    canvas.create_image(data.width, data.height, anchor=SE, image=data.hudBot)


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


def mouseWheel(event, data):
    # Handle zooming
    # The amount to zoom by
    factor = event.delta / 120
    zoom(data, factor, event.x, event.y)


def redrawAll(canvas, data):
    data.map.draw(canvas, data)
    redrawHud(canvas, data)


def redrawAllWrapper(canvas, data):
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, data.width, data.height,
                            fill='#5E3C11', width=0)
    redrawAll(canvas, data)
    canvas.update()


def makeMap(canvas, data):
    data.points = [(random() * data.viewSize[0], random() * data.viewSize[1])
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.viewSize[0], data.viewSize[1])
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
    data.viewSize = [900, 900]
    data.timerDelay = 10
    data.loadingMessage = 'Generating Initial Map'

    makeMap(canvas, data)


def setup(data):
    def keyPressedWrapper(event, data):
        keyPressed(event, data)
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

    data.mapSize = [900, 900]
    data.mapPos = [30, 30]

    data.canvas = Canvas(data.root, width=windowSize[0], height=windowSize[1])
    data.canvas.configure(bd=0, highlightthickness=0)
    data.canvas.pack()
    # create the root and the canvas
    # set up events
    data.root.bind("<Key>", lambda event:
                   keyPressedWrapper(event, data))
    data.root.bind("<MouseWheel>", lambda event:
                   mouseWheelWrapper(event, data))


def run():
    def timerFiredWrapper(canvas, data):
        timerFired(data)
        redrawAllWrapper(canvas, data)

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
