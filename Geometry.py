# # --- Geometry ---
# #
# # - Various geometric functions
# #
# # --- --- --- ---

from itertools import product


def dist(p1, p2):
    # Returns the distance between two points.
    # Accepts p1, p2 as 2d coordinates (x, y)
    return sum([(p1[i] - p2[i]) ** 2 for i in range(2)]) ** 0.5


def grad(p1, p2):
    # Returns the gradient between p1 and p2.
    # If the gradient is infinity, returns None
    # Accepts p1, p2 as 2d coordinates (x, y)
    if p1[0] == p2[0]:
        return None
    else:
        return (p1[1] - p2[1]) / (p1[0] - p2[0])


def checkCollinear(*points):
    # Returns if a set of 3 points is collinear.
    # Accepts points, a set of 3 pairs of 2d coordinates.
    return grad(points[0], points[1]) == grad(points[1], points[2])


def circleTop(points):
    # Returns the uppermost point of the circumcenter of 3 vertices.
    # Accepts points, a set of 3 pairs of 2d coordinates.
    s = [dist(points[(i + 1) % 3], points[(i + 2) % 3]) for i in range(3)]
    m = [s[i]**2 * (s[(i + 1) % 3]**2 + s[(i + 2) % 3] ** 2 - s[i] ** 2)
         for i in range(3)]
    norm = sum(m)
    mnorm = [t / norm for t in m]
    parts = [(points[i][0] * mnorm[i], points[i][1] * mnorm[i])
             for i in range(3)]
    ccenter = (sum([t[0] for t in parts]), sum([t[1] for t in parts]))
    rad = dist(points[0], ccenter)
    return (ccenter[0], ccenter[1] + rad)


def intersectParabola(x, focus, d):
    # Finds the intersection point of a parabola, given by a focus and
    # a directrix parallel to the x-axis, and a line parallel to the y-axis
    return (d + focus[1]) / 2 - (x - focus[0]) ** 2 / 2 / (d - focus[1])


def intersectParabolas(f_1, f_2, d):
    # Finds the intersection point of two parabolas, given their foci and a
    # common directrix. Uses a particularly nice geometric idea.

    # Find the intersect of f_1f_2 and the directrix.
    n = ((f_2[0] - f_1[0]) / (f_2[1] - f_1[1]) * (d - f_1[1]) + f_1[0], d)

    # f_1f_2 and the projection of targ is tangent to the directrix!
    targA_x = n[0] - (dist(n, f_1) * dist(n, f_2)) ** 0.5
    targA_y = intersectParabola(targA_x, f_1, d)
    targB_x = n[0] + (dist(n, f_1) * dist(n, f_2)) ** 0.5
    targB_y = intersectParabola(targB_x, f_1, d)
    return ((targA_x, targA_y), (targB_x, targB_y))


def tripleIntersect(f_1, f_2, f_3, d):
    # Finds the common intersection point of three parabolas,
    # given their foci and a common directrix.

    # Finds the pairwise intersections
    cand1 = intersectParabolas(f_1, f_2, d)
    cand2 = intersectParabolas(f_2, f_3, d)

    # Look for the closest pair of pairwise intersections, and returns
    # their midpoint
    closest = sorted([(v, w) for v, w in product(cand1, cand2)],
                     key=lambda t: dist(t[0], t[1]))[0]
    return tuple([sum([point[i] for point in closest]) / 2 for i in range(2)])


def isClockwise(p):
    # Returns if three points form a clockwise circle (or are collinear)

    # Not using grad, because it fails if some segment is vertical
    return (p[1][0] - p[0][0]) * (p[2][1] - p[0][1]) <= \
           (p[2][0] - p[0][0]) * (p[1][1] - p[0][1])


def findCentroid(poly):
    # Finds the centroid of a polygon
    # Takes in a polygon that's already ordered in a clockwise order
    n = len(poly)
    poly.append(poly[0])
    A = 0.5 * sum([poly[i][0] * poly[i + 1][1] -
                   poly[i + 1][0] * poly[i][1] for i in range(n)])
    if A == 0:
        return None
    Cx = 1 / 6 / A * sum([(poly[i][0] + poly[i + 1][0]) *
                          (poly[i][0] * poly[i + 1][1] -
                           poly[i + 1][0] * poly[i][1]) for i in range(n)])
    Cy = 1 / 6 / A * sum([(poly[i][1] + poly[i + 1][1]) *
                          (poly[i][0] * poly[i + 1][1] -
                           poly[i + 1][0] * poly[i][1]) for i in range(n)])

    return (Cx, Cy)
