import curses
import curses.ascii
from itertools import product

tracker = set[int]  # type alias

# tracking data
board: list[int] = [0 for _ in range(9*9)]  # main board.
battrs: list[int] = [curses.A_NORMAL for _ in range(9*9)]

# trackers will track the sudoku conditions, we initialize them to be full.
cols: list[tracker] = [{x+1 for x in range(9)} for _ in range(9)]
rows: list[tracker] = [{x+1 for x in range(9)} for _ in range(9)]
blks: list[tracker] = [{x+1 for x in range(9)} for _ in range(9)]

boxes: list[list[tuple[int, int]]] = []  # co-ordinates to box members

# boxes requires special initialization to calculate the co-ordinates
for x, y in product(range(3), range(3)):  # double for
    lst: list = []  # list for box
    for z, q in product(range(3), range(3)):  # double for
        lst.append((x*3 + z, y*3 + q))  # generate the members
    boxes.append(lst)  # list complete

# location globals
xloc: int = 4
yloc: int = 4


# helper functions
def loc2txt(x: int, y: int) -> tuple[int, int]:
    "returns screen/text (col,row) from board locations"

    return (y + y//3 + 2, x + x//3 + 2)  # board starts at (2,2) a//3 adds a spacer per 3.


def loc2tracker(x: int, y: int) -> tuple[tracker, tracker, tracker]:
    "returns trackers (col, row, block)"

    return (cols[x], rows[y], blks[x//3 + (y//3)*3])


def loc2boardpos(x: int, y: int) -> int:
    "returns the index in the board list/vector"

    return x + y*9


def getIntersection(x: int, y: int) -> tracker:
    "calculates the intersection of all three trackers for this location: col, row, block."

    c, r, b = loc2tracker(x, y)
    return c.intersection(r).intersection(b)


def setCell(x: int, y: int, v: int, attrs: int = curses.A_NORMAL):
    "sets a cell value, and updates trackers"
    global board, battrs

    # the position must not already be filled; it must be zero.
    if board[pos := loc2boardpos(x, y)] != 0:  # cache position
        return  # position is filled

    # make sure v is a valid value
    if v not in getIntersection(x, y):
        return  # v is not valid.

    # remove the value from all 3 trackers
    for s in loc2tracker(x, y):
        s.remove(v)

    # finally set ...
    board[pos] = v  # ... the position ...
    battrs[pos] = attrs  # ... and the attrs


def clearCell(x: int, y: int):
    "clears a value from a cell and updates trackers"
    global board, battrs

    # check that the cell has a value to clear
    if (val := board[pos := loc2boardpos(x, y)]) == 0:  # cache val and pos
        return  # cell already clear; don't add zero to trackers

    # add values back to all 3 trackers
    for t in loc2tracker(x, y):
        t.add(val)

    # finally ...
    board[pos] = 0  # ... clear the pos ...
    battrs[pos] = curses.A_NORMAL  # and attr


def empty(x: int, y: int):
    "returns if a cell is empty or not"

    return board[loc2boardpos(x, y)] == 0


def find() -> tuple[int, int, int]:  # (x, y, v)
    "finds the first cell with only one possibility if it exists"

    for x, y in product(range(9), range(9)):  # double for
        if not empty(x, y):
            continue  # skip filled in spaces to prevent false positives
        if len(inter := getIntersection(x, y)) == 1:  # a single value left means that we have found a value
            return (x, y, inter.pop())  # return the pos & value

    # we use this helper to check the cols, rows, and boxes
    def diff(i: int, cels: list[tuple[int, set[int]]]) -> set[int]:
        "helper to difference the a set from its neighbors"
        s = cels[i][1].copy()
        for _, vs in cels[0:i]+cels[i+1:]:
            s.difference_update(vs)

        return s

    cels: list[tuple[int, set[int]]]
    # check cols, rows and boxes for single values as well
    for x in range(9):
        cels = [(y, getIntersection(x, y)) for y in range(9) if empty(x, y)]
        for i in range(len(cels)):
            if len(s := diff(i, cels)) == 1:
                return (x, cels[i][0], s.pop())

    for y in range(9):
        cels = [(x, getIntersection(x, y)) for x in range(9) if empty(x, y)]
        for i in range(len(cels)):
            if len(s := diff(i, cels)) == 1:
                return (cels[i][0], y, s.pop())

    for b in range(9):
        cels = [(bx, getIntersection(*bx)) for bx in boxes[b] if empty(*bx)]
        for i in range(len(cels)):
            if len(s := diff(i, cels)) == 1:
                return (*cels[i][0], s.pop())

    return (0, 0, 0)  # sentinel value for not found.


def cursor(stdscr: curses.window):
    "sets the cursor to current x,y pos"

    y, x = loc2txt(xloc, yloc)
    stdscr.move(y, x)


def update(stdscr: curses.window):
    "updates the screen to match the data sources"
    global board

    # update board values on screen
    for x in range(9):
        for y in range(9):
            py, px = loc2txt(x, y)
            pos = loc2boardpos(x, y)
            v = board[pos]
            c = battrs[pos]
            out = str(v)
            if (v == 0):
                if (len(getIntersection(x, y)) == 0):
                    out = "X"  # cells that have no possibilities are marked with an X
                    c = curses.A_REVERSE
                else:
                    out = "."  # empty cels get a a .

            stdscr.addstr(py, px, out, c)

    # update column possibilities
    for c in range(9):
        col = cols[c]
        for v in range(9):
            stdscr.addch(14 + v, 2 + c + c//3, str(v+1) if v+1 in col else " ")

    # update row possibilities
    for r in range(9):
        row = rows[r]
        for h in range(9):
            stdscr.addch(2 + r + r//3, 15+h, str(h+1) if h+1 in row else " ")

    # update box possibilities
    for c in range(9):
        box = blks[c]
        stdscr.addch(13, 20 + 2*c, chr(ord("a")+c))
        for v in range(9):
            stdscr.addch(14 + v, 20 + 2*c, str(v+1) if v+1 in box else " ")

    # update intersection possibilities
    inter = getIntersection(xloc, yloc)
    stdscr.addstr(2, 26, "intersection")
    for v in range(9):
        stdscr.addch(3 + v, 30, str(v+1) if v+1 in inter else " ")

    # update the cursor.
    cursor(stdscr)


def clamp(v, low=0, high=8) -> int:
    "clamps values to low/high"

    return max(low, min(high, v))


def search():
    "searches for the next space with only one possible value, sets it and repeats until none are found."

    while (ret := find()) != (0, 0, 0):
        setCell(*ret, curses.A_REVERSE)


def reset():
    "resets all cels set by search; i.e. automatically"

    for x, y in product(range(9), range(9)):  # double for
        if battrs[loc2boardpos(x, y)] == curses.A_REVERSE:
            clearCell(x, y)


def output():
    "outputs the board to out.text; output is formatted with spaces and new lines"

    with open("out.txt", 'w') as f:
        for x in range(9):
            if x and not x % 3:  # split rows into groups of three
                f.write("\n")
            for y in range(9):
                if y and not y % 3:  # split cols into groups of three
                    f.write(" ")
                ch = '.'
                if val := board[loc2boardpos(x, y)] != 0:
                    ch = chr(ord('0')+val)
                f.write(ch)
            f.write("\n")


def clear():
    "clears the entire board."
    for x, y in product(range(9), range(9)):
        clearCell(x, y)


def main(stdscr: curses.window):
    "main: runs the sudoku logic"
    global board, battrs, xloc, yloc

    # print static elements
    stdscr.addstr(0, 20, "SUDOKU Solver/Creator")

    stdscr.addstr(0,   0, " |abc|def|ghi|")
    stdscr.addstr(1,   0, "-|---|---|---|-")
    stdscr.addstr(2,   0, "a|   |   |   |")
    stdscr.addstr(3,   0, "b|   |   |   |")
    stdscr.addstr(4,   0, "c|   |   |   |")
    stdscr.addstr(5,   0, "-|---|---|---|-")
    stdscr.addstr(6,   0, "d|   |   |   |")
    stdscr.addstr(7,   0, "e|   |   |   |")
    stdscr.addstr(8,   0, "f|   |   |   |")
    stdscr.addstr(9,   0, "-|---|---|---|-")
    stdscr.addstr(10,  0, "g|   |   |   |")
    stdscr.addstr(11,  0, "h|   |   |   |")
    stdscr.addstr(12,  0, "i|   |   |   |")
    stdscr.addstr(13,  0, "-|---|---|---|-")
    stdscr.addstr(14, 15, "abc")
    stdscr.addstr(15, 15, "def")
    stdscr.addstr(16, 15, "ghi")

    stdscr.addstr(1,  40, "keys")
    stdscr.addstr(3,  40, "ESC, q, Q, x, X: quit")
    stdscr.addstr(4,  40, "0-9: set cel to value and search")
    stdscr.addstr(5,  40, "UP, DOWN, LEFT, RIGHT: movement")
    stdscr.addstr(6,  40, "BACKSPACE, DEL: clear cel")
    stdscr.addstr(7,  40, "r, R: reset calculated values")
    stdscr.addstr(8,  40, "SPACE, s, S: search for cels to set")
    stdscr.addstr(9,  40, "o, O: outputs to out.txt")
    stdscr.addstr(10, 40, "c, C: clears all values")

    # initial update
    update(stdscr)
    stdscr.refresh()

    # program loop
    while key := stdscr.getch():
        # check which key is pressed and execute actions
        if key in (curses.ascii.ESC, ord('q'), ord('Q'), ord('x'), ord('X')):
            return

        if ord('1') <= key <= ord('9'):
            setCell(xloc, yloc, key - ord('0'))
            search()
        elif curses.KEY_UP == key:
            yloc = clamp(yloc-1)
        elif curses.KEY_DOWN == key:
            yloc = clamp(yloc+1)
        elif curses.KEY_LEFT == key:
            xloc = clamp(xloc-1)
        elif curses.KEY_RIGHT == key:
            xloc = clamp(xloc+1)
        elif key in (curses.KEY_DC, curses.KEY_BACKSPACE, curses.ascii.DEL, curses.ascii.BS):
            clearCell(xloc, yloc)
        elif key in (ord('r'), ('R')):
            reset()
        elif key in (curses.ascii.SP, ord('s'), ord('S')):
            search()
        elif key in (ord('o'), ord("O")):
            output()
        elif key in (ord('c'), ord("C")):
            clear()

        # update the screen
        update(stdscr)
        stdscr.refresh()


curses.wrapper(main)
