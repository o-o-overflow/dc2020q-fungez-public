import random, string

# use static random seed
random.seed(1337)

# map size
W, H = 0x180, 0x180

# letter primes
letter_primes = 'cdfhlnrtx' # [2, 3, 5, 7, 11, 13, 17, 19, 23]

# gen* controls the location of sudoku
genX = lambda j:  (j + 2) ** 2 + 0xf * 0xe
gen_x = '2+:*fe*+'
genY = lambda i:  (0xf - i) * 3
gen_y =  'f\\-3*'

# the sudoku challenge
# sudoku.name #22661
sudoku = [
        [0, 5, 0, 0, 4, 0, 0, 8, 6],
        [3, 0, 0, 6, 0, 0, 7, 0, 0],
        [0, 0, 6, 0, 0, 0, 0, 0, 0],
        [2, 4, 1, 0, 0, 9, 0, 0, 0],
        [0, 0, 8, 0, 7, 0, 3, 0, 0],
        [0, 0, 0, 1, 0, 0, 8, 2, 4],
        [0, 0, 0, 0, 0, 0, 4, 0, 0],
        [0, 0, 3, 0, 0, 7, 5, 6, 2],
        [6, 9, 0, 0, 5, 0, 1, 3, 0]
        ]

solution = [
        [1, 5, 9, 7, 4, 3, 2, 8, 6],
        [3, 2, 4, 6, 9, 8, 7, 5, 1],
        [8, 7, 6, 5, 2, 1, 9, 4, 3],
        [2, 4, 1, 3, 8, 9, 6, 7, 5],
        [5, 6, 8, 4, 7, 2, 3, 1, 9],
        [9, 3, 7, 1, 6, 5, 8, 2, 4],
        [7, 1, 5, 2, 3, 6, 4, 9, 8],
        [4, 8, 3, 9, 1, 7, 5, 6, 2],
        [6, 9, 2, 8, 5, 4, 1, 3, 7]
        ]

# classes of commands
C0 = string.ascii_uppercase + 'hijklmnoqrstuwxyz' + '{}()[];'
C1 = string.digits + 'abcdef'
C2 = '+-*/%`'
CX = string.ascii_letters + string.digits + string.punctuation
