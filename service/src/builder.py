EMPTY = ' '
BRIDGE = '#'
UNKOWN = '?'
D = [(-1, 0), (0, 1), (1, 0), (0, -1)]
S = '<v>^'

def push(x):
    assert x >= 0
    if x <= 9:
        return chr(ord('0') + x)
    elif x <= 0xf:
        return chr(ord('a') + x - 10)
    elif x <= 0xf * 0xf:
        a, b = x % 0xf, x // 0xf
        if b == 1:
            c = 'f'
        else:
            c = push(b) + 'f*'
        if a != 0:
            c += push(a) + '+'
        return c
    assert 0, 'unsupported number %#x' % x

# mem[y][x] => stack
def load(x, y):
    return push(x) + push(y) + 'g'

# stack => mem[y][x]
def store(x, y):
    return push(x) + push(y) + 'p'

def merge(A, B):
    if A is None:
        return B
    if B is None:
        return A
    C = [min(A[0], B[0]), max(A[1], B[1]), min(A[2], B[2]), max(A[3], B[3])]
    # print(A, B, C)
    return C

class RegFrame(object):
    def __init__(self, n):
        self.regs = [(i, 0) for i in range(n)] # iterator register
        self.idx = -1

    def get(self, k=0):
        return self.regs[self.idx - k]

    def use(self):
        self.idx += 1
        return self.regs[self.idx]

    def free(self):
        self.idx -= 1

class CodeBlock(object):
    def __init__(self, code):
        self._code = code
        self.succ = []
        self.pred = set()
        self.start = None
        self.end = None
        self.compiled = False
        self.loc = None
        self.dir = -1
        self.depth = -1

    def link(self, other):
        self.succ = [other]
        other.pred.add(self)

    def choose(self, ifFalse, ifTrue):
        self.succ = [ifFalse, ifTrue]
        ifFalse.pred.add(self)
        ifTrue.pred.add(self)

    @property
    def code(self):
        c = self._code
        if self.dir == -1:
            c = ' ' + c
        else:
            c = S[self.dir] + c
        if len(self.succ) == 2:
            if self.dir == 0 or self.dir == 2:
                c += '|'
            else:
                c += '_'
        return c

    def shift(self, dx, dy):
        x, y = self.loc
        self.loc = dx + x, dy + y
        x, y = self.end
        self.end = dx + x, dy + y
        for s in self.succ:
            assert s.depth != -1
            if s.depth == self.depth + 1:
                s.shift(dx, dy)

    def region(self, pos, d, depth):
        if self.depth != -1:
            return None
        self.loc = pos
        self.dir = d
        self.depth = depth
        l = len(self.code)
        x, y = pos
        dx, dy = D[d]
        R = [x, x, y, y]
        x, y = x + dx * (l - 1), y + dy * (l - 1)
        R = merge(R, [x, x, y, y])
        self.end = (x, y)

        if len(self.succ) == 2:
            if d == 0 or d == 2:
                A = self.succ[0].region((x, y + 1), 1, depth + 1)
                if A and A[2] <= y:
                    k = y - A[2] + 1
                    A[2] += k
                    A[3] += k
                    self.succ[0].shift(0, k)
                B = self.succ[1].region((x, y - 1), 3, depth + 1)
                if B and B[3] >= y:
                    k = B[3] - y + 1
                    B[3] -= k
                    B[2] -= k
                    self.succ[1].shift(0, -k)
            else:
                A = self.succ[0].region((x + 1, y), 2, depth + 1)
                if A and A[0] <= x:
                    k = x - A[0] + 1
                    A[0] += k
                    A[1] += k
                    self.succ[0].shift(k, 0)
                B = self.succ[1].region((x - 1, y), 0, depth + 1)
                if B and B[1] >= x:
                    k = B[1] - x + 1
                    B[1] -= k
                    B[0] -= k
                    self.succ[1].shift(-k, 0)
            C = merge(A, B)
        elif len(self.succ) == 1:
            C = self.succ[0].region((x + dx, y + dy), d, depth + 1)
        else:
            C = R
        R = merge(C, R)
        return R

class Builder(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.codeblocks = []
        self.regs = RegFrame(width)
        self.refs = []
        self.map = [[EMPTY] * self.width for _ in range(self.height)]

    def new_block(self, *args):
        cb = CodeBlock(*args)
        self.codeblocks.append(cb)
        return cb

    def locate(self, entry, d=1, e=0, depth=0):
        R = entry.region((0, 0), d, depth)
        assert R[1] - R[0] < self.width
        assert R[3] - R[2] < self.height
        sx, sy = (-R[0] + e, -R[2] + e)
        entry.shift(sx, sy)

    def emit(self, entry):
        Q = [entry]

        # compile
        while len(Q) > 0:
            q = Q.pop()
            if q.compiled:
                continue
            x, y = q.loc
            d = q.dir
            dx, dy = D[d]
            code = q.code
            for i in range(len(code)):
                assert self.map[y][x] == EMPTY
                self.map[y][x] = code[i]
                x, y = x + dx, y + dy
            if len(q.succ) == 1:
                self.refs.append((q, q.succ[0], d))
            elif len(q.succ) == 2:
                if d == 0 or d == 2:
                    self.refs.append((q, q.succ[0], 1))
                    self.refs.append((q, q.succ[1], 3))
                else:
                    self.refs.append((q, q.succ[0], 2))
                    self.refs.append((q, q.succ[1], 0))
            Q.extend(q.succ)
            q.compiled = True

    def find_path(self, src, dst, d):
        x, y = src
        q = [(x, y, d)]
        h = 0
        pre = {(x, y): None}
        while h < len(q):
            u = q[h]
            h += 1
            x, y, d = u
            for _d in range(4):
                if self.map[y][x] == BRIDGE and _d != d:
                    # we can not change direction on a bridge
                    continue
                dx, dy = D[_d]
                tx, ty = x + dx, y + dy
                if 0 <= tx < self.width and 0 < ty < self.height:
                    v = (tx, ty)
                    if v == dst:
                        assert v not in pre
                        pre[v] = (x, y, _d)
                        path = []
                        while True:
                            u = pre.get(v)
                            if u is None:
                                return path[::-1]
                            path.append(u)
                            v = u[:2]
                    if (self.map[ty][tx] == EMPTY or self.map[ty][tx] == BRIDGE):
                        if v not in pre:
                            pre[v] = (x, y, _d)
                            q.append((tx, ty, _d))
        return None

    def link(self):
        for caller, callee, d in self.refs:
            x, y = caller.end
            assert 0 <= x < self.width and 0 <= y < self.height
            dx, dy = D[d]
            x, y = x + dx, y + dy
            src = (x, y)
            assert callee.loc is not None
            dst = callee.loc
            print('find path from %r/%r to %r/%r' % (caller, src, callee, dst))
            if src == dst:
                continue
            # print(self.show())
            path = self.find_path(src, dst, d)
            print(path)
            # for _x, _y, _d in path:
            for x, y, _d in path:
                if _d == d:
                    self.map[y][x] = BRIDGE
                else:
                    self.map[y][x] = S[_d]
                # x, y, d = _x, _y, _d
                d = _d

    def save(self, path):
        with open(path, 'w') as f:
            f.write(self.show())

    def load(self, path):
        with open(path) as f:
            raw = f.read().split('\n')
        height = len(raw)
        width = len(raw[0])
        self.width = width
        self.height = height
        self.codeblocks = []
        self.regs = RegFrame(width)
        self.refs = []
        self.map = list(map(list, raw))

    def repeat(self, n, action):
        i = self.regs.use()

        c = ''
        # loop header
        c += push(0)
        c += store(*i)
        loop_header = self.new_block(c)

        # loop condition
        c = ''
        c += push(n)
        # c += ':' # dup n
        c += load(*i)
        c += '`' # if i < n
        loop_condition = self.new_block(c)

        # loop step
        c = ''
        c += load(*i)
        c += '1+'
        c += store(*i)
        loop_step = self.new_block(c)

        # loop body
        loop_body_begin, loop_body_end = action()

        # restore register
        loop_end = self.new_block('')

        loop_header.link(loop_condition)
        loop_condition.choose(loop_end, loop_body_begin)
        loop_body_end.link(loop_step)
        loop_step.link(loop_condition)

        self.regs.free()
        return loop_header, loop_end

    def memset(self, pos, char, size):
        x, y = pos
        def gen():
            i = self.regs.get()
            c = push(char)
            c += load(*i)
            c += push(x)
            c += '+'
            c += push(y)
            c += 'p' # mem[y][x + i] = char
            cb = self.new_block(c)
            return cb, cb
        return self.repeat(size, gen)

    def read_string(self, n, storage):
        def read_char():
            i = self.regs.get()
            c = '~'
            c += ':' # dup => keep one extra copy on stack :)
            c += load(*i)
            c += push(storage[0])
            c += '+'
            c += push(storage[1])
            c += 'p'
            cb = self.new_block(c)
            return cb, cb
        return self.repeat(n, read_char)

    def show(self, c='#'):
        mm = ('\n'.join([''.join(m).replace('#', c) for m in self.map]))
        return mm
