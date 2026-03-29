from collections import defaultdict


ELEMENTS_LIST = [
    "e", # empty

    "w", # wizard
    "m", # mountain
    "gm", # gold mine
    "d", # dragon

    "r1", # red castle rank 1
    "r2", # red castle rank 2
    "r3", # red castle rank 3
    "r4", # red castle rank 4

    "b1", # blue castle rank 1
    "b2", # blue castle rank 2
    "b3", # blue castle rank 3
    "b4", # blue castle rank 4

    "g1", # green castle rank 1
    "g2", # green castle rank 2
    "g3", # green castle rank 3
    "g4", # green castle rank 4

    "y1", # yellow castle rank 1
    "y2", # yellow castle rank 2
    "y3", # yellow castle rank 3
    "y4", # yellow castle rank 4
    
    -6, # number card -6
    -5, # number card -5
    -4, # number card -4
    -3, # number card -3
    -2, # number card -2
    -1, # number card -1
    1, # number card 1
    2, # number card 2
    3, # number card 3
    4, # number card 4
    5, # number card 5
    6, # number card 6
]
FOUR_NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def apply_wizard_and_empty(board:list[list[str|int]]) -> list[list[str|int]]:
    n_rows = len(board)
    n_cols = len(board[0]) if board else 0

    for i, row in enumerate(board):
        for j, cell in enumerate(row):
            if cell == "w":
                for di, dj in FOUR_NEIGHBORS:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n_rows and 0 <= nj < n_cols:
                        # if element on position ni,nj matches r|b|g|y + 1|2|3|4 (ex. b3)
                        if isinstance(board[ni][nj], str) and len(board[ni][nj]) == 2 and board[ni][nj][0] in "rbgy" and board[ni][nj][1] in "1234":
                            # increase number card by 1 (ex. b3 becomes b4)
                            board[ni][nj] = board[ni][nj][0] + str(int(board[ni][nj][1]) + 1)
            elif cell == "e":
                board[i][j] = 0

    return board


def process_castle(board:list[list[str|int]], i:int, j:int) -> int:
    n_rows = len(board)
    n_cols = len(board[0]) if board else 0

    row_elements = []
    row_dragon = False
    row_gm = False

    column_elements = []
    column_dragon = False
    column_gm = False

    # collect row elements
    for col in range(j-1, -1, -1):
        if board[i][col] == "m":
            break
        elif board[i][col] == "d":
            row_dragon = True
        elif board[i][col] == "gm":
            row_gm = True
        elif isinstance(board[i][col], int):
            row_elements.append(board[i][col])

    for col in range(j + 1, n_cols):
        if board[i][col] == "m":
            break
        elif board[i][col] == "d":
            row_dragon = True
        elif board[i][col] == "gm":
            row_gm = True
        elif isinstance(board[i][col], int):
            row_elements.append(board[i][col])

    # collect column elements
    for row in range(i-1, -1, -1):
        if board[row][j] == "m":
            break
        elif board[row][j] == "d":
            column_dragon = True
        elif board[row][j] == "gm":
            column_gm = True
        elif isinstance(board[row][j], int):
            column_elements.append(board[row][j])

    for row in range(i + 1, n_rows):
        if board[row][j] == "m":
            break
        elif board[row][j] == "d":
            column_dragon = True
        elif board[row][j] == "gm":
            column_gm = True
        elif isinstance(board[row][j], int):
            column_elements.append(board[row][j])

    if row_dragon:
        row_elements = [0 if element > 0 else element for element in row_elements]
    if column_dragon:
        column_elements = [0 if element > 0 else element for element in column_elements]

    if row_gm:
        row_elements = [2*element for element in row_elements]
    if column_gm:
        column_elements = [2*element for element in column_elements]

    return sum(row_elements) + sum(column_elements)


def find_castles(board:list[list[str|int]]) -> dict[str, list[tuple[int,int]]]:
    castles = defaultdict(list)
    for i, row in enumerate(board):
        for j, cell in enumerate(row):
            if isinstance(cell, str) and len(cell) == 2 and cell[0] in "rbgy" and cell[1] in "12345":
                castles[cell[0]].append((i, j, int(cell[1])))
    return castles


def calculate_player_points(board:list[list[str|int]]) -> dict[str, int]:
    board = apply_wizard_and_empty(board)
    points = {
        "r": 0,
        "g": 0,
        "b": 0,
        "y": 0
    }
    castles = find_castles(board)

    for color in points.keys():
        for castle in castles[color]:
            i, j, level = castle
            points[color] += process_castle(board, i, j) * level

    return points


if __name__ == "__main__":
    board = [
        [3, "r1", "y4", "b1", -6, "y1"],
        ["b2", "gm", 4, 1, "m", "w"],
        [2, 4, "r2", -5, -2, "b1"],
        ["y2", "d", 3, "m", "b1", 5],
        [-1, -3, "b1", "y3", 6, 2],
    ]

    points = calculate_player_points(board)
    print(points)