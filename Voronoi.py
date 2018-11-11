# # --- Voronoi ---
# #
# # - Main function outputs a Voronoi diagram of a list of given points
# #
# # --- --- --- ---

from Geometry import *
from heapq import *


def ordered(points):
    # Arranges a pair of points in increasing order of y
    return tuple(sorted(points, key=lambda x: x[1]))


def tryAppend(d, key, entries):
    # Attempts to extend the value of a key's value in a dictionary
    # If the relevant value doesn't exist, create it and set it to entries
    d[key] = d.get(key, []) + entries


class Mapmaker:
    # Class which takes a set of points, then iteratively generates its Voronoi
    # diagram. Has methods to draw the diagram at intermediate stages.
    def __init__(self, pointSet, width, height):
        self.pointSet = pointSet
        self.queue = []
        for p in pointSet:
            heappush(self.queue, (p[1], 0, p))

        self.frontLine = []
        self.sweepPos = 0
        self.vertices = {p: set() for p in pointSet}
        self.edgeVertices = {}
        self.edges = {}

        self.width = width
        self.height = height

        self.done = False

    def isOutside(self, vertex):
        return vertex[0] <= 0 or vertex[0] >= self.width or \
            vertex[1] <= 0 or vertex[1] >= self.height

    def isInside(self, vertex):
        return vertex[0] >= 0 and vertex[0] <= self.height and \
            vertex[1] >= 0 and vertex[1] <= self.height

    def addEvent(self, event):
        # Add an event into the event queue
        heappush(self.queue, event)

    def checkIntersectEvent(self, points):
        # Checks if we need to add an intersection event in the future
        if points[0] != points[2]:
            if not isClockwise(points):
                tip = circleTop(points)
                if tip[1] > self.sweepPos:
                    self.addEvent((tip[1], 1, points))

    def edgeInsert(self, edgeIndex, vertex, bias):
        # Attempt to add a new vertex into an edge between a pair of vertices
        # Bias is +1 if the ray points rightwards, and -1 otherwise
        edgeIndex = ordered(edgeIndex)
        port = (1 - bias) // 2
        if edgeIndex in self.edges:
            for edge in self.edges[edgeIndex]:
                if edge[port] is None:
                    edge[port] = vertex
                    for center in edgeIndex:
                        self.vertices[center].add(vertex)
                    break
        else:
            self.edges[edgeIndex] = [[vertex, None][::bias]]
            for center in edgeIndex:
                self.vertices[center].add(vertex)

    def insertParabola(self, focus, target, vertex):
        # Insert a new parabola into the frontLine,
        # intersecting the parabola target
        for i in range(len(self.frontLine)):
            # Check if this is the correct parabola
            if self.frontLine[i] != target:
                continue

            # Check if this is the correct section of the parabola
            if i > 0:
                if intersectParabolas(target, self.frontLine[i - 1],
                                      self.sweepPos)[0][0] > focus[0]:
                    continue
            if i < len(self.frontLine) - 1:
                if intersectParabolas(target, self.frontLine[i + 1],
                                      self.sweepPos)[1][0] < focus[0]:
                    continue

            # Check if any intersection events need to be added
            if i > 0:
                self.checkIntersectEvent([self.frontLine[i - 1],
                                          self.frontLine[i],
                                          focus])

            if i < len(self.frontLine) - 1:
                self.checkIntersectEvent([focus,
                                          self.frontLine[i],
                                          self.frontLine[i + 1]])

            self.frontLine.insert(i, focus)
            self.frontLine.insert(i, target)
            break

    def newParabola(self, focus):
        # Handling the new parabola event
        if not self.frontLine:
            self.frontLine.append(focus)
        else:
            intersects = []
            for curve in self.frontLine:
                intersect = intersectParabola(focus[0], curve, self.sweepPos)
                heappush(intersects, (-intersect, curve))

            target = heappop(intersects)
            vertex = (focus[0], -target[0])
            self.insertParabola(focus, target[1], vertex)

    def removeParabola(self, curve_set):
        for i in range(len(self.frontLine) - 2):
            if len([k for k in range(3)
                    if self.frontLine[i + k] == curve_set[k]]) == 3:
                vertex = tripleIntersect(*self.frontLine[i: i + 3],
                                         self.sweepPos)

                for j in range(3):
                    edgeIndex = ordered((curve_set[j], curve_set[(j + 1) % 3]))
                    factor = 1 if j == 2 else -1
                    bias = -factor if edgeIndex[1][0] > vertex[0] else factor
                    self.edgeInsert(edgeIndex, vertex, bias)

                del self.frontLine[i + 1]

                if i > 0:
                    self.checkIntersectEvent(self.frontLine[i - 1: i + 2])

                if i < len(self.frontLine) - 2:
                    self.checkIntersectEvent(self.frontLine[i: i + 3])
                break

    def extendEdges(self):
        for edgeIndex in self.edges:
            gradient = (edgeIndex[1][0] - edgeIndex[0][0]) /\
                (edgeIndex[0][1] - edgeIndex[1][1])

            for edge in self.edges[edgeIndex]:
                if edge[0] is None:
                    port = 0
                elif edge[1] is None:
                    port = 1
                else:
                    continue

                if self.isInside(edge[1 - port]):
                    vertexX = self.width * port
                    vertexY = (vertexX - edge[1 - port][0]) * gradient + \
                        edge[1 - port][1]
                    vertex = (vertexX, vertexY)
                    edge[port] = vertex
                    for center in edgeIndex:
                        self.vertices[center].add(vertex)
                else:
                    self.edges[edgeIndex].remove(edge)
                    for center in edgeIndex:
                        for vertex in edge:
                            self.vertices[center].discard(vertex)
                    del edge

    def truncateEdges(self):
        def truncatedEdge(edge, factor, edgeIndex):
            gradient = (edgeIndex[1][0] - edgeIndex[0][0]) / \
                (edgeIndex[0][1] - edgeIndex[1][1])

            hTarg = (1 - factor) * self.width / 2
            origin = edge[(1 + factor) // 2]

            vertical = 0 if gradient * factor > 0 else self.height
            vChoice = (origin[0] + (vertical - origin[1]) / gradient,
                       vertical)
            hShift = (hTarg - origin[0]) * gradient
            hChoice = (hTarg, origin[1] + hShift)

            if self.isInside(hChoice):
                return [hChoice, origin][::factor]
            else:
                return [vChoice, origin][::factor]

        def truncateAndReplace(edge, factor, edgeIndex):
            newEdge = truncatedEdge(edge, factor, edgeIndex)
            port = (1 - factor) // 2
            vertex = newEdge[port]
            for center in edgeIndex:
                self.vertices[center].discard(edge[port])
                self.vertices[center].add(newEdge[port])
            self.edgeVertices[vertex] = edgeIndex
            return newEdge

        for edgeIndex in self.edges:
            output = []

            for edge in self.edges[edgeIndex]:
                if self.isOutside(edge[0]):
                    if self.isInside(edge[1]):
                        edge = truncateAndReplace(edge, 1, edgeIndex)

                if self.isOutside(edge[1]):
                    edge = truncateAndReplace(edge, -1, edgeIndex)

                if self.isInside(edge[0]) and self.isInside(edge[1]):
                    output.append(edge)
                else:
                    for vertex in edge:
                        if vertex in self.edgeVertices:
                            self.edgeVertices.pop(vertex)
                        for center in edgeIndex:
                            self.vertices[center].discard(vertex)

            self.edges[edgeIndex] = output

    def arrangeRegions(self):
        for center in self.pointSet:
            output = []
            vertices = self.vertices[center]
            while len(vertices) > 0:
                vertex = vertices.pop()
                if len(output) < 2:
                    output.append(vertex)
                else:
                    for i in range(len(output)):
                        j = (i + 1) % len(output)
                        if isClockwise([output[i], vertex, output[j]]):
                            output.insert(j, vertex)
                            break
            self.vertices[center] = output

    # Insert corners
    def insertBorders(self):
        def edgeMetric(point):
            if point[1] == 0:
                return point[0]
            elif point[0] == self.width:
                return self.width + point[1]
            elif point[1] == self.height:
                return 2 * self.width + self.height - point[0]
            else:
                return 2 * (self.width + self.height) - point[1]

        edgeVertexOrder = []
        for vertex in self.edgeVertices:
            heappush(edgeVertexOrder, (edgeMetric(vertex), vertex))

        thresholds = [(self.width, 0),
                      (self.width, self.height),
                      (0, self.height),
                      (0, -1)]

        last = (0, 0)
        firstCenter = sorted(self.pointSet, key=lambda x: dist((0, 0), x))[0]
        self.vertices[firstCenter].add((0, 0))
        lastCenters = [firstCenter]
        while len(edgeVertexOrder) > 0:
            _, vertex = heappop(edgeVertexOrder)
            center = [c for c in lastCenters if c in
                      self.edgeVertices[vertex]][0]
            if (center, center) not in self.edges:
                self.edges[(center, center)] = []

            if edgeMetric(vertex) > edgeMetric(thresholds[0]):
                corner = thresholds.pop(0)
                self.edges[(center, center)].append([last, corner])
                self.vertices[center].add(corner)
                last = corner
            self.edges[(center, center)].append([last, vertex])

            last = vertex
            lastCenters = self.edgeVertices[vertex]

        self.edges[(firstCenter, firstCenter)].append([last, (0, 0)])

    def step(self):
        if not self.done:
            if len(self.queue) > 0:
                event = heappop(self.queue)
                self.sweepPos = event[0]
                if event[1] == 0:
                    self.newParabola(event[2])
                else:
                    self.removeParabola(event[2])
            else:
                self.extendEdges()
                self.truncateEdges()
                self.insertBorders()
                self.arrangeRegions()
                self.done = True

    def fullParse(self):
        while not self.done:
            self.step()

    def reduce(self):
        # Applies a Lloyd reduction on the Voronoi diagram (replaces each
        # vertex with its centroid)
        if self.done:
            newPoints = [findCentroid(vertices) for
                         vertices in self.vertices.values()]
            Mapmaker.__init__(self, newPoints, self.width, self.height)

    def draw_parabola(self, canvas, data, focus, directrix):
        coords = []
        for xFact in range(101):
            x = data.width / 100 * xFact
            y = intersectParabola(x, focus, directrix)
            coords.append((x, y))
        canvas.create_line(coords, fill='red', smooth='true')

    def scale(self, point, data):
        return [point[i] * data.zoom - data.viewPos[i] for i in range(2)]

    def draw(self, canvas, data):
        centerR = 2
        vertexR = 2
        for vertex in self.pointSet:
            sVertex = self.scale(vertex, data)
            canvas.create_oval(sVertex[0] - centerR,
                               sVertex[1] - centerR,
                               sVertex[0] + centerR,
                               sVertex[1] + centerR)

        for edgeIndex in self.edges:
            for edge in self.edges[edgeIndex]:
                if edge[0] is not None and edge[1] is not None:
                    canvas.create_line([self.scale(point, data)
                                        for point in edge])
                else:
                    gradient = (edgeIndex[1][0] - edgeIndex[0][0]) /\
                        (edgeIndex[0][1] - edgeIndex[1][1])
                    point = edge[0] if edge[1] is None else edge[1]
                    sPoint = self.scale(point, data)
                    canvas.create_oval(sPoint[0] - vertexR,
                                       sPoint[1] - vertexR,
                                       sPoint[0] + vertexR,
                                       sPoint[1] + vertexR)
                    norm = (1 + gradient ** 2) ** (0.5)
                    delt = [10 / norm, 10 * gradient / norm] \
                        if edge[1] is None \
                        else [-10 / norm, -10 * gradient / norm]

                    canvas.create_line(sPoint[0], sPoint[1],
                                       sPoint[0] + delt[0],
                                       sPoint[1] + delt[1])

        canvas.create_line(0, self.sweepPos,
                           data.width, self.sweepPos)
