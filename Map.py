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
        self.borderCities = set()

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
            if len(source.edges[edge]) > 0:
                if edge[0] != edge[1]:
                    self.cities[edge[0]].neighbors.add(self.cities[edge[1]])
                    self.cities[edge[1]].neighbors.add(self.cities[edge[0]])
                else:
                    self.borderCities.add(self.cities[edge[0]])
                    self.borderCities.add(self.cities[edge[1]])

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
                       if not city.isSea() and city.fertility > 0.5]

            origin = choice(sources)
            newCulture = Culture(origin)
            origin.cultures[newCulture] = 2000
            origin.currentBuilding = buildings[-4]
            for building in buildings[:-4]:
                building.build(origin)

    def update(self, data):
        # Call tick events
        for city in self.cities.values():
            city.tick()
            if city.population < 0:
                data.activeCity = city

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

    def draw(self, canvas, data):
        self.drawCitiesBG(canvas, data)

        for river in self.rivers:
            sRiver = []
            for city in river:
                sRiver.append(scale(city.center, data))

            canvas.create_line(sRiver,
                               fill=rgbToColor(DARK_OCEAN),
                               smooth=True,
                               width=2 * data.zoom,
                               tag='map')

        # Highlighting active province
        if data.activeCity:
            sVertices = [scale(vertex, data) for vertex in
                         data.activeCity.vertices]
            canvas.create_polygon(sVertices,
                                  fill='',
                                  outline=rgbToColor(HIGHLIGHT),
                                  width=1.5 * data.zoom,
                                  tag='map')

        self.drawCities(canvas, data)
