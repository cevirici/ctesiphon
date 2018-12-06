# # --- Army ---
# #
# # - Armies, and their behaviors
# #
# # --- --- --- ---

from Geometry import dist
from random import random


class Army:
    def __init__(self, location, owner, size):
        self.location = location
        self.owner = owner
        self.size = size
        self.instructions = []

    def demobilize(self):
        self.location.armies.remove(self)
        self.owner.armies.remove(self)
        del self

    def move(self):
        # If instructions exist, move to the next instruction
        if self.instructions:
            self.location.armies.remove(self)
            self.location = self.instructions.pop(0)
            self.location.armies.add(self)

    def pathfind(self, start, target, checked=None):
        # Returns a list of cities from the start to the end, with enough
        # supplies
        if checked is None:
            checked = {start}
        else:
            checked.add(start)
        if start == target:
            return [target]
        candidates = [n for n in start.neighbors if not n.isSea() and
                      n not in checked and
                      n.supplies + n.capacity > self.size]
        candidates.sort(key=lambda n: dist(n.center, target.center))
        for c in candidates:
            trial = self.pathfind(c, target, checked)
            if trial:
                return [start] + trial

    def fight(self):
        here = self.location
        for army in here.armies:
            if army.owner in self.owner.enemies:
                army.size -= self.size * random()
                self.size -= army.size * random()

                if army.size <= 0:
                    army.demobilize()
                if self.size <= 0:
                    self.demobilize()
            if here.polity in self.owner.enemies:
                if here.garrison > 0:
                    here.garrison -= self.size * random()
                    self.size -= here.garrison * random() * 2

                    if self.size <= 0:
                        self.demobilize()
                if here.garrison <= 0:
                    if here != here.polity.capital:
                        here.polity = self.owner
                        here.garrison = self.size
                        self.demobilize()
                    else:
                        here.polity.liege = self.owner
