from tkinter import *
from Voronoi import *
from random import *


def keyPressed(event, data):
    if event.keysym in ['Left', 'Right', 'Up', 'Down']:
        mode = ['Left', 'Right', 'Up', 'Down'].index(event.keysym)
        shift = [(-10, 0), (10, 0), (0, -10), (0, 10)][mode]
        data.viewPos = [data.viewPos[i] + shift[i] for i in range(2)]
    elif event.keysym == 'k':
        data.zoom -= 0.1


def redrawAll(canvas, data):
    data.map.draw(canvas, data)


def redrawAllWrapper(canvas, data):
    canvas.delete(ALL)
    canvas.create_rectangle(0, 0, data.width, data.height,
                            fill='white', width=0)
    redrawAll(canvas, data)
    canvas.update()


def makeMap(data):
    canvas = Canvas(data.root, width=data.width, height=data.height)
    canvas.configure(bd=0, highlightthickness=0)
    canvas.pack()

    data.points = [(random() * data.width, random() * data.height)
                   for i in range(4000)]
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

    data.map = Map(data.map)


def run(width=700, height=700):

    def keyPressedWrapper(event, canvas, data):
        keyPressed(event, data)
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
    makeMap(data)
    # create the root and the canvas
    # set up events
    data.root.bind("<Key>", lambda event:
                   keyPressedWrapper(event, canvas, data))
    # and launch the app
    data.root.mainloop()  # blocks until window is closed


run()
