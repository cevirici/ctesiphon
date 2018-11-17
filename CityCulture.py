# # --- CityCulture ---
# #
# # - Deals with cities and their interactions with cultures
# #
# # --- --- --- ---

# --- Constants ---

DIVERGENCE_THRESHOLD = 18
MERGE_THRESHOLD = 12

# ------


def diverge(target):
    target.divergencePressure = 0
    oldMax = target.maxCulture
    newCulture = None
    # Try a subculture, if not, make a new one
    if oldMax in oldMax.subCultures:
        candidates = sorted(oldMax.subCultures[oldMax],
                            key=lambda c: target.suitability(c))
        if candidates:
            if target.suitability(candidates[-1]) > target.suitability(oldMax):
                newCulture = candidates[-1]

    if newCulture is None:
        newCulture = oldMax.diverge(target)

    target.cultures[newCulture] = target.cultures[oldMax]
    target.cultures[oldMax] = 0
    target.maxCulture = newCulture

    queue = [n for n in target.neighbors]
    checked = set([target])
    while len(queue) > 0:
        city = queue.pop(0)
        if city not in checked:
            checked.add(city)
            if city.maxCulture == oldMax:
                if city.suitability(oldMax) < city.suitability(newCulture):
                    cc = city.cultures
                    cc[newCulture] = cc[oldMax]
                    city.maxCulture = newCulture
                    cc[oldMax] = 0

                    for n in city.neighbors:
                        if n not in checked:
                            queue.append(n)

                city.divergencePressure = 0


def reform(target):
    # Adaptible cultures can 'reform' instead of diverging
    target.divergencePressure = 0
    queue = [n for n in target.neighbors]
    checked = set([target])
    while len(queue) > 0:
        city = queue.pop(0)
        if city not in checked:
            checked.add(city)
            if city.maxCulture == target.maxCulture and \
                    city.divergencePressure > DIVERGENCE_THRESHOLD / 2:
                city.divergencePressure = 0
                for n in city.neighbors:
                    if n not in checked:
                        queue.append(n)
    target.maxCulture.reform(target)


def assimilate(target):
    # If isolated, and adjacent to ancestor/descendant, swap to that
    mc = target.maxCulture
    if mc:
        comrades = [n for n in target.neighbors if
                    n.maxCulture == mc]
        if len(comrades) == 0:
            for n in target.neighbors:
                c = n.maxCulture
                if c:
                    if c.isAncestor(mc) or mc.isAncestor(c):
                        amount = target.cultures[mc] * 0.8
                        if c in target.cultures:
                            target.cultures[c] += amount
                        else:
                            target.cultures[c] = amount
                        target.cultures[mc] -= amount
                        return


def merge(target, other):
    # Merge the max culture with a minority
    target.mergePressures[other] = 0
    oldMax = target.maxCulture
    newCulture = None
    # Check if other culture is a descendant
    if oldMax.isAncestor(other) or other.isAncestor(oldMax):
        newCulture = other if target.suitability(oldMax) > \
            target.suitability(other) else oldMax
    elif other in oldMax.subCultures:
        candidates = sorted(oldMax.subCultures[other],
                            key=lambda c: target.suitability(c),
                            reverse=True)
        if candidates:
            newCulture = candidates[0]

    if newCulture is None:
        newCulture = oldMax.merge(other, target)

    target.cultures[newCulture] = target.cultures[oldMax] + \
        target.cultures[other]

    if newCulture != oldMax:
        target.cultures[oldMax] = 0
    if newCulture != other:
        target.cultures[other] = 0
    target.maxCulture = newCulture

    queue = [n for n in target.neighbors]
    checked = set([target])
    while len(queue) > 0:
        city = queue.pop(0)
        if city not in checked:
            checked.add(city)
            if city.maxCulture == oldMax and other in city.mergePressures:
                if city.mergePressures[other] > MERGE_THRESHOLD / 2:
                    cc = city.cultures
                    cc[newCulture] = cc[oldMax] + cc[other]

                    if newCulture != oldMax:
                        cc[oldMax] = 0
                    if newCulture != other:
                        cc[other] = 0
                    city.maxCulture = newCulture

                    for n in city.neighbors:
                        if n not in checked:
                            queue.append(n)

                city.mergePressures[other] = 0
