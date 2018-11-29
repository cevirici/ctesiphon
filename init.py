# Import everything necessary for pickling

from tkinter import *
from Culture import *
from Terrain import *
from random import *
from Panels import *
from PIL import ImageTk
from sys import setrecursionlimit
from string import ascii_letters


setrecursionlimit(30000)


def loadImages(data):
    # Preload images into data
    data.globeImages = []
    for i in range(200):
        filePath = 'img\\globe\\{:0>4}.png'.format(i + 1)
        data.globeImages.append(ImageTk.PhotoImage(file=filePath))

    data.logo = ImageTk.PhotoImage(file='img\\logo.png')
    data.menuStart = ImageTk.PhotoImage(file='img\\menu-start.png')
    data.menuLoad = ImageTk.PhotoImage(file='img\\menu-load.png')
    data.menuBase = ImageTk.PhotoImage(file='img\\menu-base.png')
    data.menuLeft = ImageTk.PhotoImage(file='img\\menu-left.png')
    data.menuRight = ImageTk.PhotoImage(file='img\\menu-right.png')
    data.menuLong = ImageTk.PhotoImage(file='img\\menu-long.png')
    data.menuLongActive = ImageTk.PhotoImage(file='img\\menu-longa.png')

    data.brick = ImageTk.PhotoImage(file='img\\brick.png')

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
    data.cultureImage = ImageTk.PhotoImage(file='img\\cultureHud.png')
    data.buildingImage = ImageTk.PhotoImage(file='img\\buildingHud.png')

    data.hudTop = ImageTk.PhotoImage(file='img\\interfaceTop.png')
    data.hudLeft = ImageTk.PhotoImage(file='img\\interfaceLeft.png')
    data.hudBot = ImageTk.PhotoImage(file='img\\interfaceBot.png')
    data.hudRight = ImageTk.PhotoImage(file='img\\interfaceRight.png')
    data.pauseButton = ImageTk.PhotoImage(file='img\\button-pause.png')
    data.speedControls = ImageTk.PhotoImage(file='img\\speed-controls.png')

    cultureIcons = ['culture-temp.png',
                    'culture-altitude.png',
                    'culture-coastal.png',
                    'culture-agri.png',
                    'culture-births.png',
                    'culture-migratory.png',
                    'culture-explorative.png',
                    'culture-adaptible.png',
                    'culture-tolerant.png',
                    'culture-innovative.png',
                    'culture-militant.png']
    data.cultureIcons = []
    for i in range(len(cultureIcons)):
        data.cultureIcons.append(ImageTk.PhotoImage(file='img\\' +
                                                    cultureIcons[i]))

    cityIcons = ['cityLevel-a.png', 'cityLevel-b.png']
    data.cityIcons = []
    for i in range(len(cityIcons)):
        data.cityIcons.append(ImageTk.PhotoImage(file='img\\' +
                                                 cityIcons[i]))


def keyPressed(event, data):
    global Culture, Polity
    if data.typing:
        if event.keysym in ascii_letters:
            data.saveName += event.keysym.lower()
        elif event.keysym == 'BackSpace':
            data.saveName = data.saveName[:-1]

    else:
        if data.map:
            if event.keysym == 'space':
                data.paused = not data.paused
            elif event.keysym == 'Escape':
                if data.map:
                    if escPanel in data.panels:
                        data.panels.remove(escPanel)
                        redrawAll(data.canvas, data)
                    else:
                        data.paused = True
                        data.panels.append(escPanel)
                        redrawAll(data.canvas, data)
            elif event.keysym == 'v':
                print(data.activeCity.buildings)
            elif event.keysym == 'w':
                print(buildings)
            elif event.keysym == 'x':
                for war in War.wars:
                    print('Attackers:')
                    for polity in war.attackers:
                        print(printWord(polity.name).capitalize(), end=', ')
                    print('Defenders:')
                    for polity in war.defenders:
                        print(printWord(polity.name).capitalize(), end=', ')


def mousePressed(coords, data, held=True):
    # Bubble click events in reverse order
    for panel in data.panels[::-1]:
        if panel.click(coords, data, held):
            return


def mouseReleased(event, data):
    data.clicking = False


def mouseWheel(event, data):
    # Bubble scroll events in reverse order too
    for panel in data.panels[::-1]:
        if panel.scroll([event.x, event.y], data, event.delta):
            return


def timerFired(canvas, data):
    # Check if we're on the main menu
    if menuPanel in data.panels or newGamePanel in data.panels:
        if data.offset > 0:
            if data.offset > 100:
                data.offset -= 6
            data.offset -= 2
        data.globeFrame = (data.globeFrame + 1) % 200
        redrawAll(canvas, data)
    elif mapPanel in data.panels:
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
            # Not calling redrawPanel here, because we should only update
            # canvas once
            mapPanel.redraw(canvas, data)

        if data.clicking:
            mousePressed([data.root.winfo_pointerx() - data.root.winfo_rootx(),
                          data.root.winfo_pointery() - data.root.winfo_rooty()
                          ],
                         data)

        redrawNotMap(canvas, data)


def init(canvas, data):
    data.timerDelay = 10
    data.globeFrame = 0
    data.ticks = 0
    data.tickRate = 10
    data.scrollBuffer = 8
    data.scrolling = 0
    data.paused = True
    data.clicking = False

    data.panels = [preloaderPanel]
    data.activeCity = None

    data.messages = ['Ironing Laundry',
                     '... Carthago Delando Est',
                     'Loading... Unless You\'re the Mongols',
                     'Not a Loading Message Placeholder',
                     'Laying Bricks',
                     'Installing Drivers',
                     'Uninstalling Drivers',
                     'Reticulating Splines',
                     'Calculating Antiderivatives',
                     'Pull the Lever, Kronk!',
                     'Salting the Earth',
                     'Invading Australia',
                     'Invading Madagascar',
                     'To the Batmobile!',
                     'Worrying about Deadlines',
                     'Burning Bridges',
                     'Running Out of Loading Messages',
                     'Making Mexico Pay for This']
    data.loadingMessage = choice(data.messages)
    data.offset = 800
    data.drawMode = 5

    data.size = 5
    data.sizeNums = [400, 800, 1500, 2000, 3000, 4000, 5000]
    data.sizeText = ['Super Tiny', 'Tiny', 'Small', 'Midsize',
                     'Standard', 'Large', 'Huge']
    data.cityCount = 4000
    data.typing = False
    data.saveName = ''

    data.mapSize = [data.cityCount ** 0.5 * 20, data.cityCount ** 0.5 * 20]
    data.viewSize = VIEW_SIZE

    redrawAll(canvas, data)
    preloaderPanel.wipe(canvas)
    data.panels = [menuPanel]
    loadImages(data)


def setup(data):
    def keyPressedWrapper(event, data):
        keyPressed(event, data)
        redrawAll(data.canvas, data)

    def mousePressedWrapper(event, data):
        data.clicking = True
        mousePressed([event.x, event.y], data, False)
        redrawAll(data.canvas, data)

    def mouseWheelWrapper(event, data):
        mouseWheel(event, data)
        redrawAll(data.canvas, data)

    windowSize = [1280, 960]
    data.width = windowSize[0]
    data.height = windowSize[1]
    data.root = Tk()
    data.root.resizable(width=False, height=False)  # prevents resizing window

    data.canvas = Canvas(data.root, width=windowSize[0], height=windowSize[1],
                         bg=rgbToColor(WOOD_DARK))
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
