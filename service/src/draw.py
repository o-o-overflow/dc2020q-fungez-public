import random

from builder import *
from config import *

class Optimizer(Builder):
    def __init__(self, path):
        self.load(path)

    def hide_bridges(self):
        # just replace them with C1(nops)
        for i in range(self.height):
            for j in range(self.width):
                if self.map[i][j] == BRIDGE:
                    self.map[i][j] = random.choice(C0)

    def hide_empty(self):
        # fill ' ' with CX(random)
        for i in range(self.height):
            for j in range(self.width):
                if self.map[i][j] == EMPTY:
                    self.map[i][j] = random.choice(CX)

if __name__ == '__main__':
    builder = Optimizer('map_static')
    print(builder.show())
    builder.hide_bridges()
    builder.save('map_no_bridge')
    builder.hide_empty()
    builder.save('map')
