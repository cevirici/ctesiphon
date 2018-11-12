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


def redrawAll(canvas, data):
    data.map.draw(canvas, data)


def redrawAllWrapper(canvas, data):
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, data.width, data.height,
                            fill='#5E3C11', width=0)
    redrawAll(canvas, data)
    canvas.update()


def mouseWheel(event, data):
    zoomPoint = (event.x * data.zoom - data.viewPos[0],
                 event.y * data.zoom - data.viewPos[1])
    oldZoom = data.zoom
    data.zoom += event.delta / 1200
    data.zoom = max(0, data.zoom)
    factor = (data.zoom - oldZoom)
    for i in range(2):
        data.viewPos[i] += zoomPoint[i] * factor


def makeMap(canvas, data):

    data.points = [(random() * data.width, random() * data.height)
                   for i in range(MAP_SIZE)]
    data.map = Mapmaker(data.points, data.width, data.height)
    data.viewPos = [0, 0]
    data.zoom = 1
    redrawAllWrapper(canvas, data)

    for i in range(4):
        data.map.fullParse()
        redrawAllWrapper(canvas, data)
        data.map.reduce()

    data.map.fullParse()
    redrawAllWrapper(canvas, data)
    data.oldMap = data.map
    data.map = Map(data.map)
    data.map.spawnLand()
    data.map.generateRivers()
    redrawAllWrapper(canvas, data)


def run(width=700, height=700):
    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
        redrawAllWrapper(canvas, data)

    def mouseWheelWrapper(event, canvas, data):
        mouseWheel(event, data)
        redrawAllWrapper(canvas, data)

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
    makeMap(canvas, data)
    # and launch the app
    data.root.mainloop()  # blocks until window is closed


run()
