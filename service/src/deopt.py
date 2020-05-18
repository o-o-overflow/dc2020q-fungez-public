import random

from builder import *
from config import *

class Simplifier(Builder):
    def __init__(self, path):
        self.load(path)

    def remove_nops(self):
        nop = set(C0)
        for i in range(self.height):
            for j in range(self.width):
                if self.map[i][j] in nop:
                    self.map[i][j] = ' '
    
    def remove_deadcode(self):
        assert self.map[0][0] == '>'

        q = [(0, 0, 2)]
        reachable = {q[0]}

        dx, dy = 0, 0
        h = 0
        x, y = 0, 0

        valid = lambda _x, _y, _d: 0 <= _x < self.width and 0 <= _y < self.height

        while h < len(q):
            # print(q[h])
            x, y, d = q[h]
            h += 1
            c = self.map[y][x]
            if c == '|':
                v = x, y - 1, 3
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
                v = x, y + 1, 1
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
            elif c == '_':
                v = x - 1, y, 0
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
                v = x + 1, y, 2
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
            elif c != '@':
                _d = '<v>^'.find(self.map[y][x])
                if _d != -1:
                    # new direction
                    d = _d
                else:
                    # keep moving
                    pass
                dx, dy = [[-1, 0], [0, 1], [1, 0], [0, -1]][d]
                v = x + dx, y + dy, d
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
        uniq = {(x, y) for x, y, _ in reachable}
        print('visisted %d cell, %d unique cell' % (len(q), len(uniq)))

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in uniq:
                    self.map[y][x] = ' '

    def build_bridge(self):
        assert self.map[0][0] == '>'

        q = [(0, 0, 2)]
        reachable = {q[0]}

        dx, dy = 0, 0
        h = 0
        x, y = 0, 0

        valid = lambda _x, _y, _d: 0 <= _x < self.width and 0 <= _y < self.height

        while h < len(q):
            # print(q[h])
            x, y, d = q[h]
            h += 1
            c = self.map[y][x]
            if c == '|':
                v = x, y - 1, 3
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
                v = x, y + 1, 1
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
            elif c == '_':
                v = x - 1, y, 0
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
                v = x + 1, y, 2
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)
            elif c != '@':
                _d = '<v>^'.find(self.map[y][x])
                if _d != -1:
                    # new direction
                    d = _d
                elif c == ' ':
                    self.map[y][x] = '#'
                dx, dy = [[-1, 0], [0, 1], [1, 0], [0, -1]][d]
                v = x + dx, y + dy, d
                if valid(*v) and v not in reachable:
                    reachable.add(v)
                    q.append(v)

if __name__ == '__main__':
    builder = Simplifier('map')
    print(builder.show())
    builder.remove_nops()
    builder.save('map_simple')
    builder.remove_deadcode()
    builder.save('map_better')

    builder = Simplifier('map_simple')
    # cheat
    assert builder.map[80][89] == '<'
    builder.map[80][89] = 'v'
    builder.remove_deadcode()
    builder.save('map_best')
    builder.build_bridge()
    builder.save('map_final')
