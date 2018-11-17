# # --- Terrain ---
# #
# # - The Map class, and things to do with the Map
# #
# # --- --- --- ---

from Terrain import *


class Map:
    def __init__(self, source, data):
        # Imports the geometry from a Mapmaker object
        self.cities = {}
        self.cityCount = len(source.pointSet)

        self.centerCity = None
        closestDist = float('inf')
        center = [data.viewPos[i] + data.viewSize[i] / data.zoom / 2
                  for i in range(2)]

        for point in source.pointSet:
            self.cities[point] = City(point, source.vertices[point])
            if dist(point, center) < closestDist:
                closestDist = dist(point, center)
                self.centerCity = self.cities[point]

        # Populate adjacency dictionary
        for edge in source.edges:
            if edge[0] != edge[1] and len(source.edges[edge]) > 0:
                self.cities[edge[0]].neighbors.add(self.cities[edge[1]])
                self.cities[edge[1]].neighbors.add(self.cities[edge[0]])

        self.rivers = []

        self.width = source.width
        self.height = source.height

    # --- Geography ---

    def randomCity(self):
        # Returns a random city
        return choice(tuple(self.cities.values()))

    def findClosestCity(self, point, data):
        # Returns the closest city from a point on screen
        toCheck = [self.centerCity]
        checked = set()
        bestDistance = float('inf')
        closest = None
        while len(toCheck) > 0:
            city = toCheck.pop(0)
            if city not in checked:
                if dist(city.center, point) < bestDistance:
                    bestDistance = dist(city.center, point)
                    closest = city
                checked.add(city)
                for neigh in city.neighbors:
                    if neigh not in checked and neigh.visible(data):
                        toCheck.append(neigh)
        return closest

    def getStraightestCity(self, origin, heading, candidates):
        # Returns a city among the candidates that's keeps to the course
        # as closely as possible
        def straightness(city):
            return headingDiff(getHeading(origin, city), heading)
        return sorted(candidates, key=straightness)[0]

    # --- Culture ---

    def spawnCultures(self):
        # Spawn some cultures
        for i in range(10):
            sources = [city for city in self.cities.values()
                       if city.altitude > 0]

            origin = choice(sources)
            newCulture = Culture(origin)
            origin.emigrate(newCulture, -50)

    def update(self):
        # Call tick events
        for city in self.cities.values():
            city.tick()

        # Enact transfers
        for city in self.cities.values():
            city.midTick()

        # After redistribution is done, rescale
        for city in self.cities.values():
            city.postTick()

        # Tick polities
        for polity in Polity.polities:
            polity.tick()

    # --- Drawing ---

    def drawCitiesBG(self, canvas, data):
        # Draw cities, starting from the center, and spreading out until
        # the cities are no longer visible
        toDraw = [self.centerCity]
        drawn = set()
        while len(toDraw) > 0:
            city = toDraw.pop(0)
            if city not in drawn:
                city.draw(canvas, data)
                drawn.add(city)
                for neigh in city.neighbors:
                    if neigh not in drawn and neigh.visible(data):
                        toDraw.append(neigh)

    def drawCities(self, canvas, data):
        # Draw cities, starting from the center, and spreading out until
        # the cities are no longer visible
        toDraw = [self.centerCity]
        drawn = set()
        while len(toDraw) > 0:
            city = toDraw.pop(0)
            if city not in drawn:
                city.drawDecorations(canvas, data)
                drawn.add(city)
                for neigh in city.neighbors:
                    if neigh not in drawn and neigh.visible(data):
                        toDraw.append(neigh)

    def drawCulture(self, origin, searched, canvas, data):
        culture = origin.maxCulture
        if culture is not None:
            A, B = culture.origin, culture.origin
            lastA, lastB = None, None
            while A != lastA or B != lastB:
                lastA, lastB = A, B
                aCand = [n for n in A.neighbors
                         if A.maxCulture == n.maxCulture]
                if aCand:
                    A = sorted(aCand,
                               key=lambda x: dist(x.center, B.center))[-1]
                    if dist(A.center, B.center) < dist(lastA.center, B.center):
                        A = lastA
                        break
                else:
                    break
                bCand = [n for n in B.neighbors
                         if B.maxCulture == n.maxCulture]
                if bCand:
                    B = sorted(bCand,
                               key=lambda x: dist(x.center, A.center))[-1]
                    if dist(A.center, B.center) < dist(lastB.center, A.center):
                        B = lastB
                        break
                else:
                    break

            scaleA = scale(A.center, data)
            scaleB = scale(B.center, data)
            midPt = [(scaleA[i] + scaleB[i]) / 2 for i in range(2)]
            name = printWord(culture.name).capitalize()
            fSize = int(dist(scaleA, scaleB) / len(name)) + 16
            font = ('Times New Roman', fSize)
            canvas.create_text(midPt,
                               font=font,
                               text=name)

    def drawCultures(self, canvas, data):
        # Draw the culture name over the geographical centers
        queue = [self.centerCity]
        painted = set()
        searched = set()
        while len(queue) > 0:
            target = queue.pop()
            if target not in searched:
                searched.add(target)
                if target not in painted:
                    self.drawCulture(target, searched, canvas, data)
                for n in target.neighbors:
                    if n not in searched:
                        queue.append(n)
                    if n.maxCulture == target.maxCulture:
                        painted.add(n)

    def draw(self, canvas, data):
        self.drawCitiesBG(canvas, data)

        for river in self.rivers:
            sRiver = []
            for city in river:
                sRiver.append(scale(city.center, data))

            canvas.create_line(sRiver,
                               fill=rgbToColor(DARK_OCEAN),
                               smooth=True,
                               width=2 * data.zoom)

        # Highlighting active province
        if data.activeCity:
            sVertices = [scale(vertex, data) for vertex in
                         data.activeCity.vertices]
            canvas.create_polygon(sVertices,
                                  fill='',
                                  outline=rgbToColor(HIGHLIGHT),
                                  width=1.5 * data.zoom)

        self.drawCities(canvas, data)

        # if data.drawMode == 5:
        #     self.drawCultures(canvas, data)
