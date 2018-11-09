# # --- Voronoi ---
# #
# # - Main function outputs a Voronoi diagram of a list of given points
# #
# # --- --- --- ---

from Geometry import *
from itertools import product
from heapq import *


def ordered(points):
    # Arranges a pair of points in increasing order of y
    return tuple(sorted(points, lambda x: x[1]))


def tryAppend(d, key, entries):
    # Attempts to extend the value of a key's value in a dictionary
    # If the relevant value doesn't exist, create it and set it to entries
    d[key] = d.get(key, []) + entries


def findVoronoiVertices(pointSet):
    # Finds the vertices of the regions of the Voronoi diagram defined
    # by the points in pointSet. Outputs as [{point : [vertices]}]

    # Uses a variant of Fortune's Algorithm

    # Events are (xcoord, 0: Removal, 1: Insertion, properties)
    pointSet = sorted(pointSet, key=lambda x: x[1], reverse=True)
    eventQueue = []
    for p in pointSet:
        heappush(eventQueue, (p[1], 0, p))

    frontLine = []
    sweepPos = 0
    vertices = {p: [] for p in pointSet}
    centers = {}
    edges = {}

    def addEvent(event):
        # Add an event into the event queue
        heappush(eventQueue, event)

    def checkIntersectEvent(points):
        # Checks if we need to add an intersection event in the future
        if points[0] != points[2]:
            tip = findCircleTip(points)
            if tip[1] > sweepPos:
                addEvent((tip[1], 1, points))

    def edgeInsert(edgeIndex, vertex, bias):
        # Attempt to add a new vertex into an edge between a pair of vertices
        # Bias is +1 if the ray points rightwards, and -1 otherwise
        edgeIndex = ordered(edgeIndex)
        if edgeIndex in edges:
            for edge in edges[edgeIndex]:
                port = 0 if edge[0] is None else 1
                if vertex[0] < edge[1 - port][0]:
                    edge[port] = vertex
                    break
        else:
            edges[edgeIndex] = [[vertex, None][::bias]]

    def insertParabola(focus, target, vertex):
        # Insert a new parabola into the frontLine,
        # intersecting parabola target
        for i in range(len(frontLine)):
            # Check if this is the correct parabola
            if frontLine[i] != target:
                continue

            # Check if this is the correct section of the parabola
            if i > 0:
                if intersectParabolas(target, frontLine[i - 1],
                                      sweepPos)[0][1] > focus[1]:
                    continue
            if i < len(frontLine) - 1:
                if intersectParabolas(target, frontLine[i + 1],
                                      sweepPos)[1][1] < focus[1]:
                    continue

            # Check if any intersection events need to be added
            if i > 0:
                checkIntersectEvent([frontLine[i - 1], frontLine[i], focus])

            if i < len(frontLine) - 1:
                checkIntersectEvent([focus, frontLine[i], frontLine[i + 1]])

            frontLine.insert(i, focus)
            frontLine.insert(i, target)

            for bias in [-1, 1]:
                edgeInsert(edgeIndex, vertex, bias)
            break

    def newParabola(focus):
        # Handling the new parabola event
        if not frontLine:
            frontLine.append(focus)
        else:
            intersects = []
            for curve in frontLine:
                intersect = intersectParabola(focus[1], curve, sweepPos)
                heappush(intersects, (intersect[1], curve))

            target = heappop(intersects)
            vertex = (focus[0], target[0])
            insertParabola(focus, target[1], vertex)

    def removeParabola(curve_set):
        for i in range(len(frontLine) - 2):
            if len([k for k in range(3)
                    if frontLine[i + k] == curve_set[k]]) == 3:

                cand1 = intersectParabolas(frontLine[i],
                                           frontLine[i + 1], sweepPos)
                cand2 = intersectParabolas(frontLine[i + 1],
                                           frontLine[i + 2], sweepPos)
                vertex = sorted([(v, w) for v, w in product(cand1, cand2)],
                                key=lambda t: dist(t[0], t[1]))[0][0]
                for f in curve_set:
                    vertices[f].append(vertex)
                centers[vertex] = curve_set

                for edgeIndex in [(curve_set[0], curve_set[1]),
                                  (curve_set[1], curve_set[2]),
                                  (curve_set[0], curve_set[2])]:

                    if edgeIndex[0][0] > edgeIndex[1][0]:
                        edgeIndex = (edgeIndex[1], edgeIndex[0])

                    direction = 1 if edgeIndex[1][1] < vertex[1] else 0
                    step = intersectParabolas(edgeIndex[0], edgeIndex[1],
                                              sweepPos + 0.0001)[direction]
                    bias = step[1] > vertex[1]

                    edgeInsert(edgeIndex, vertex, bias)

                del frontLine[i + 1]

                if i > 0:
                    checkIntersectEvent([frontLine[i - 1],
                                         frontLine[i],
                                         frontLine[i + 1]])

                if i < len(frontLine) - 2:
                    checkIntersectEvent([frontLine[i],
                                         frontLine[i + 1],
                                         frontLine[i + 2]])
                break

    def extendEdges():
        for edgeIndex in edges:
            grad = (edgeIndex[0][1] - edgeIndex[1][1]) / \
                   (edgeIndex[0][0] - edgeIndex[1][0])
            for edge in edges[edgeIndex]:
                if edge[0] is None:
                    vertex = (edge[1][1] * grad + edge[1][0], 0)

                    for center in edgeIndex:
                        vertices[center].append(vertex)
                    centers[vertex] = edgeIndex
                    edge[0] = vertex
                elif edge[1] is None:
                    vertex = (-(1 - edge[0][1]) * grad + edge[0][0], 1)
                    for center in edgeIndex:
                        vertices[center].append(vertex)
                    centers[vertex] = edgeIndex
                    edge[1] = vertex

    # Truncate Edges
    def truncateEdges():
        for edgeIndex in edges:
            output = []
            for edge in edges[edgeIndex]:
                gradient = (edge[0][1] - edge[1][1]) / (edge[0][0] - edge[1][0])
                if isInside(edge[0]) and isInside(edge[1]):
                    output.append(edge)

                elif isOutside(edge[0]) and isOutside(edge[1]):
                    for endpoint in edge:
                        for center in vertices:
                            if endpoint in vertices[center]:
                                vertices[center].remove(endpoint)
                                if endpoint in centers:
                                    del centers[endpoint]
                    continue

                elif isOutside(edge[0]):
                    candidates = [(0, edge[1][1] - edge[1][0] * gradient),
                                  (1, edge[1][1] + (1 - edge[1][0]) * gradient),
                                  (edge[1][0] - edge[1][1] / gradient, 0),
                                  (edge[1][0] + (1 - edge[1][1]) / gradient, 1)]
                    for cand in candidates:
                        if cand[1] < edge[1][1]:
                            if isInside(cand):
                                output.append([cand, edge[1]])
                                for endpoint in edgeIndex:
                                    vertices[endpoint].append(cand)
                                centers[cand] = edgeIndex
                                break

                elif isOutside(edge[1]):
                    candidates = [(0, edge[0][1] - edge[0][0] * gradient),
                                  (1, edge[0][1] + (1 - edge[0][0]) * gradient),
                                  (edge[0][0] - edge[0][1] / gradient, 0),
                                  (edge[0][0] + (1 - edge[0][1]) / gradient, 1)]
                    for cand in candidates:
                        if cand[1] > edge[0][1]:
                            if isInside(cand):
                                output.append([edge[0], cand])
                                for endpoint in edgeIndex:
                                    vertices[endpoint].append(cand)
                                centers[cand] = edgeIndex
                                break
            edges[edgeIndex] = output

    # Merge Edges
    def mergeEdges():
        toPurge = []
        for edgeIndex in edges:
            segments = edges[edgeIndex]
            if segments:
                bots = sorted([seg[0] for seg in segments], key=lambda x: x[1])
                lowestPoint = bots[0]
                tops = sorted([seg[1] for seg in segments], key=lambda x: -x[1])
                highestPoint = tops[0]
                edges[edgeIndex] = [[lowestPoint, highestPoint]]
            else:
                toPurge.append(edgeIndex)

        for edgeIndex in toPurge:
            del edges[edgeIndex]

    # Clear vertices
    def clearVertices():
        for center in vertices:
            output = []
            for vertex in vertices[center]:
                if isInside(vertex):
                    output.append(vertex)
                else:
                    if vertex in centers:
                        del centers[vertex]
            vertices[center] = output

    def isOutside(vertex):
        return vertex[0] <= 0 or vertex[0] >= 1 or \
            vertex[1] <= 0 or vertex[1] >= 1

    def isInside(vertex):
        return vertex[0] >= 0 and vertex[0] <= 1 and \
            vertex[1] >= 0 and vertex[1] <= 1

    # Insert corners
    def insertBorders():
        for corner in [(0, 0), (0, 1), (1, 0), (1, 1)]:
            foci = findVoronoiRegion(corner, pointSet)
            for center in foci:
                vertices[center].append(corner)
            centers[corner] = foci

        for vertex in centers:
            for center in centers[vertex]:
                try:
                    assert(center in pointSet)
                except AssertionError:
                    print(vertex)
                    print(center)

        def findNextVertex(now, last):
            for center in centers[now]:
                for vertex in vertices[center]:
                    if vertex != last and vertex != now:
                        if vertex[0] == now[0] or vertex[1] == now[1]:
                            return vertex

        # Insert Side Edges
        last = (0, 0)
        now = findNextVertex(last, last)
        while now != (0, 0):
            center = [c for c in centers[now] if c in centers[last]][0]
            edgeIndex = (center, center)
            if edgeIndex in edges:
                edges[edgeIndex].append([last, now])
            else:
                edges[edgeIndex] = [[last, now]]

            vertex = findNextVertex(now, last)
            last = now
            now = vertex

        center = [c for c in centers[now] if c in centers[last]][0]
        edgeIndex = (center, center)
        if edgeIndex in edges:
            edges[edgeIndex].append([last, now])
        else:
            edges[edgeIndex] = [[last, now]]


    while len(eventQueue) > 0:
        event = eventQueue.pop()
        sweepPos = event[0]
        if event[1] == 0:
            point = event[2]
            newParabola(point)
        else:
            curve_set = event[2]
            removeParabola(curve_set)

    extendEdges()
    truncateEdges()
    mergeEdges()
    clearVertices()
    insertBorders()

    return vertices, edges
