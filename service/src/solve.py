from config import *

flag0 = 'trappedinvYP1'
flag1 = ''
for i in range(9):
    for j in range(9):
        if sudoku[j][i] == 0:
            k = solution[j][i] - 1
            flag1 += letter_primes[k]

flag = flag0 + flag1
print('flag = OOO{%s} length = %d' % (flag, len(flag)))
# flag = OOO{trappedinvYP1ctlxrhdrnfctxhrldrlfhdxtxdtnfcftcdlnhdxnlhrcxcflxtr} length = 64
