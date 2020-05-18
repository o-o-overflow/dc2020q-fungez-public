from builder import *
from config import *

def obfuscate(c):
    # insert one nop before every command
    s = ''
    for x in c:
        s += random.choice(C0)
        s += x
    return s

class ChallengeBuilder(Builder):
    def check9(self):
        '''
        check the set of 9 numbers is exactly `letter_primes`
        letter_primes = [2, 3, 5, 7, 11, 13, 17, 19, 23]
        print(''.join(list(map(lambda _: chr(_ + ord('a')), letter_primes)))) # cdfhlnrtx

        v1:
        B = [0] * 26
        for _ in range(9):
            x = POP()
            assert ord('a') <= x <= ord('z')
            assert B[x] == 0
            x -= ord('a')
            for t in range(x, 26, x):
                B[t] = 1
        assert sum(B) == 24

        v2:
        B = [0] * 26
        for _ in range(9):
            x = POP()
            c0 = x > (ord('a'))
            c1 = (ord('z') + 1) > x
            c2 = c0 * c1
            x = x - ord('a')
            x = x * c2
            x = x * ~B[x]
            for i in range(26):
                c3 = (i + 1) * x
                c4 = 26 > j
                c5 = c3 * c4
                B[c5] = 1

        prod = ~B[0]
        for i in range(25):
            prod *= B[i + 1]
        '''
        B = (0x40 - 26, 0)
        stage0, stage1 = self.memset(B, 0, 26)

        flag = self.regs.use()
        c = '1'
        c += store(*flag)
        stage2 = self.new_block(c)
        stage1.link(stage2)

        def inner():
            c = ''
            c += '::' # dup 2
            c += push(ord('a') - 1)
            c += '`' # cmp
            c += '\\' # swap
            c += push(ord('z') + 1)
            c += '\\' # swap
            c += '`' # cmp
            c += '*'
            c += load(*flag)
            c += '*'
            c += store(*flag)
            c += push(ord('a'))
            c += '-'
            c += ':'
            c += push(B[0])
            c += '+'
            c += '0g'
            c += '!'
            c += '*'
            head = self.new_block(c)

            def fill():
                i = self.regs.get()
                c = ':'
                c += '1'
                c += '\\'
                c += load(*i)
                c += '1+*'
                c += ':'
                c += push(26)
                c += '\\'
                c += '`'
                c += '*'
                c += push(B[0])
                c += '+'
                c += '0p'
                cb = self.new_block(c)
                return cb, cb

            b, e = self.repeat(26, fill)
            head.link(b)

            c = '$'
            tail = self.new_block(c)
            e.link(tail)
            return head, tail

        stage3, stage4 = self.repeat(9, inner)
        stage2.link(stage3)

        c = load(*flag)
        c += push(B[0] + 1)
        c += '0g!*'
        stage5 = self.new_block(c)
        stage4.link(stage5)

        self.regs.free()

        def prod():
            i = self.regs.get()
            c = load(*i)
            c += push(B[0] + 2)
            c += '+0g'
            c += '*'
            cb = self.new_block(c)
            return cb, cb
        stage6, stage7 = self.repeat(24, prod)
        stage5.link(stage6)

        return stage0, stage7

    def draw_sudoku(self, sudoku, genX, genY):
        for i in range(9):
            for j in range(9):
                x = genX(j)
                y = genY(i)
                assert self.map[y][x] == EMPTY

        charset = list(letter_primes)
        for i in range(9):
            for j in range(9):
                x = genX(j)
                y = genY(i)
                k = sudoku[i][j]
                if k == 0:
                    self.map[y][x] = UNKOWN
                else:
                    self.map[y][x] = charset[k - 1]

    def fill_soduku(self, genX='', genY=''):
        def outer():
            i = self.regs.get()
            def inner():
                j = self.regs.get()
                c = load(*i)
                c += genX
                c += load(*j)
                c += genY
                c += 'g'
                c += push(ord(UNKOWN))
                c += '-'
                check_unknown = self.new_block(c)
                end = self.new_block('')
                c = '~'
                c += load(*i)
                c += genX
                c += load(*j)
                c += genY
                c += 'p'
                is_unknown = self.new_block(c)
                is_unknown.link(end)
                check_unknown.choose(is_unknown, end)
                return check_unknown, end

            return self.repeat(9, inner)
        return self.repeat(9, outer)

    def check_sudoku(self, genX, genY):
        '''
        flag = 1
        for i in range(9):
            for j in range(9):
                x = genX(i)
                y = genX(j)
                push(map[y][x])
            flag *= check9()
        for i in range(9):
            for j in range(9):
                y = genX(i)
                x = genX(j)
                push(map[y][x])
            flag *= check9()
        for _i in range(9):
            for _j in range(9):
                i = _i // 3 * 3 + _j // 3
                j = _i % 3 * 3 + _j % 3
                x = genX(i)
                y = genX(j)
                push(map[y][x])
            flag *= check9()
        '''
        flag = self.regs.use()
        c = '1'
        c += store(*flag)
        stage0 = self.new_block(c)

        def outer0():
            i = self.regs.get()

            def inner0():
                j = self.regs.get()
                c = load(*i)
                c += genX
                c += load(*j)
                c += genY
                c += 'g'
                cb = self.new_block(c)
                return cb, cb

            load_begin, load_end = self.repeat(9, inner0)
            check_begin, check_end = self.check9()
            load_end.link(check_begin)
            c = load(*flag)
            c += '*'
            c += store(*flag)
            set_flag = self.new_block(c)
            check_end.link(set_flag)
            return load_begin, set_flag

        def outer1():
            i = self.regs.get()

            def inner1():
                j = self.regs.get()
                c = load(*j)
                c += genX
                c += load(*i)
                c += genY
                c += 'g'
                cb = self.new_block(c)
                return cb, cb

            load_begin, load_end = self.repeat(9, inner1)
            check_begin, check_end = self.check9()
            load_end.link(check_begin)
            c = load(*flag)
            c += '*'
            c += store(*flag)
            set_flag = self.new_block(c)
            check_end.link(set_flag)
            return load_begin, set_flag

        def outer2():
            i = self.regs.get()
            i0 = self.regs.use()
            i1 = self.regs.use()

            c = load(*i)
            c += ':' # dup
            c += '3/3*'
            c += store(*i0)
            c += '3%3*'
            c += store(*i1)

            header = self.new_block(c)

            def inner2():
                j = self.regs.get()
                c = load(*j)
                c += ':' # dup
                c += '3/'
                c += load(*i0)
                c += '+'
                c += genX
                c += '\\' # swap
                c += '3%'
                c += load(*i1)
                c += '+'
                c += genY
                c += 'g'
                cb = self.new_block(c)
                return cb, cb

            load_begin, load_end = self.repeat(9, inner2)
            check_begin, check_end = self.check9()
            header.link(load_begin)
            load_end.link(check_begin)
            c = load(*flag)
            c += '*'
            c += store(*flag)
            set_flag = self.new_block(c)
            check_end.link(set_flag)

            self.regs.free()
            self.regs.free()
            return header, set_flag

        stage1_begin, stage1_end = self.repeat(9, outer0)
        stage2_begin, stage2_end = self.repeat(9, outer1)
        stage3_begin, stage3_end = self.repeat(9, outer2)
        stage0.link(stage1_begin)
        stage1_end.link(stage2_begin)
        stage2_end.link(stage3_begin)

        c = load(*flag)
        final = self.new_block(c)
        stage3_end.link(final)

        self.regs.free()

        return stage0, final

    def build_trap(self, hint, storage):
        read_begin, read_end = self.read_string(len(hint), storage)
        compares = []
        deadends = []
        for i in range(len(hint)):
            c = push(storage[0] + i)
            c += push(storage[1])
            c += 'g'
            c += push(ord(hint[i]))
            c += '-'
            compares.append(self.new_block(c))
        final_trap = self.new_block('!@')
        compares.append(final_trap)

        read_end.link(compares[0])
        for i in range(len(hint)):
            dead = self.new_block(hint[i] + '@')
            deadends.append(dead)
            compares[i].choose(compares[i + 1], dead)

        # `deadends` will be replaced with random meaningless code. In the
        # deployed version, we changed `final_trap` from `!@` to `KzqXIhw`,
        # this (un)luckily connects the trap to the second stage.
        deadends.append(compares[-1]) # BUG HERE

        return read_begin, deadends

    def build_backdoor(self):
        c = BRIDGE * 8 + 'p' # BRIDGE will be obfuscated
        return self.new_block(c)

if __name__ == '__main__':
    builder = ChallengeBuilder(W, H)

    c = ''
    prog_start = builder.new_block(c)
    prog_stop = builder.new_block('@')
    builder.locate(prog_start, d=2, depth=0)

    hint = 'trappedinhell'
    main, deadends = builder.build_trap(hint, (0x10, 0))
    backdoor = builder.build_backdoor()
    for de in deadends:
        k = random.randint(5, 10)
        de._code = ''.join([random.choice(C0 + C2) for _ in range(k)])
    # backdoor in deadend[-5]: triggers a 'p' code to modify one block in
    flag0_last_char = '1'
    deadends[-5]._code = obfuscate(push(ord(flag0_last_char)) + '-')
    hub = builder.new_block('0')
    deadends[-5].choose(hub, deadends[-6])
    hub.choose(backdoor, deadends[-4])

    fill_begin, fill_end = builder.fill_soduku(gen_x, gen_y)
    check_begin, check_end = builder.check_sudoku(gen_x, gen_y)
    backdoor.link(fill_begin)
    fill_end.link(check_begin)
    success = builder.new_block('"%s",,,' % 'win'[::-1])
    fail = builder.new_block('')
    fail.link(fail)
    check_end.choose(fail, success)

    deadends[-1].link(fill_begin)
    end = success

    builder.draw_sudoku(sudoku, genX, genY)

    prog_start.link(main)
    end.link(prog_stop)
    builder.locate(main, e=3, depth=1)

    builder.emit(prog_start)
    builder.link()

    for cb in builder.codeblocks:
        print(cb, cb.dir, cb.code)

    # HOT FIX
    assert builder.map[90][139] == '|'
    builder.map[90][139] = '@'

    # hide the magical switch: corrupt a 'v' to '<' so that the main logic
    # is unreachable even from the backdoor. the player has to notice the
    # backdoor branch which execute a 'p' command. by controlling the
    # arguments of 'p' command, he can change the corrupted '<' to 'v' and
    # open the door to the next stage.
    assert backdoor.dir == 2
    print('backdoor at %r=>%r' % (backdoor.loc, backdoor.end))
    x, y = backdoor.end
    x += 1
    assert builder.map[y][x] == 'v'
    builder.map[y][x] = '<'
    flag0 = hint[:-4] + 'v' + chr(x) + chr(y) + flag0_last_char
    print('flag0 = %s' % flag0)

    # print(builder.show())
    builder.save('map_static')
