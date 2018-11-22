# # --- HUD ---
# #
# # - Functions to draw the HUD
# #
# # --- --- --- ---


from Graphics import *
from tkinter import *
from Language import *


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
    sidebarPos = [1096, 521]
    popPos = [953, 340]
    popNumsPos = [1240, 340]
    canvas.create_image(sidebarPos,
                        image=data.sidebarImage,
                        tag='HUD')
    canvas.create_text(provNamePos, anchor=NW, justify='left',
                       text=printWord(ac.name).capitalize(),
                       fill='white', font=HUD_FONT,
                       tag='HUD')

    totalPopPos = [1148, 255]
    capacityPos = [1180, 255]
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
        rate = min(1, ac.progress / ac.currentBuilding.requirement)
    else:
        rate = 0
    progressEnd = [progressPos[0] + 209 * rate, progressPos[1] + 12]
    canvas.create_rectangle(progressPos, progressEnd,
                            fill='green', width=0, tag='HUD')

    builderPos = [1047, 744]
    soldierPos = [1047, 794]
    supplyPos = [1204, 744]
    canvas.create_text(builderPos,
                       text=int(ac.builders),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='HUD')
    canvas.create_text(soldierPos,
                       text=int(ac.garrison),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='HUD')
    canvas.create_text(supplyPos,
                       text=int(ac.supplies),
                       justify='center',
                       fill='white', font=HUD_FONT,
                       tag='HUD')

    # Armies

    soldPos = [953, 800]
    soldNumsPos = [1240, 800]
    soldText = ""
    soldNumsText = ""
    for army in ac.armies:
        soldText += "{}:\n".format(printWord(army.owner.name).capitalize())
        soldNumsText += "{}\n".format(int(army.size))
    canvas.create_text(soldPos,
                       text=soldText,
                       anchor=NW, justify='left',
                       fill='white', font=HUD_FONT,
                       tag='HUD')
    canvas.create_text(soldNumsPos,
                       text=soldNumsText,
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
