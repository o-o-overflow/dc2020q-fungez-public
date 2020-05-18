# DEFCON 2020 Quals Fungez(z)

## Fungez

Race `FUNGEZ_IOCTL_START` to bypass `befunge_check`

## Fungezz

*OOO{trappedinvYP1ctlxrhdrnfctxhrldrlfhdxtxdtnfcftcdlnhdxnlhrcxcflxtr}*

You should not follow the path of `trappedinhell`.

Find the branch to trigger the backdoor (a 'p' command) to modify the map
at runtime. Change the direction '<' to 'v' then you will reach the second
stage of the game, which is a sudoku challenge.

The second stage was accidently exposed to the `trappedinhell` path due to
an implementation bug (see comments in gen.py). It made the challenge
broing, so we disabled the shortcut in the old map and released a new one.

There are 3 teams solved the real one during the ctf. Many other teams
stopped at the trivial one and started complaining.

Most people only accept easy challenges that are within their capability :)

## References

1. [gen.py](service/src/gen.py) design and errors

2. [solve.py](service/src/solve.py) quick solution

3. [deopt.py](service/src/deopt.py) script to help you reverse and
   analyze

4. [map\*](service/src/map) maps in different optimization levels
