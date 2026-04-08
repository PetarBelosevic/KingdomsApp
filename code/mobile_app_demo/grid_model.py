from board_rectification import BOARD_HEIGHT, BOARD_WIDTH


class GridModel:
    """
    Class models simple grid in the rectified board image, based on known dimensions of the board and cells.
    Class expects symetrical left-right and top-bottom margins and square cells. 
    """
    def __init__(self, rows=5, cols=6, board_width=BOARD_WIDTH, board_height=BOARD_HEIGHT, height_margin=0.3/24.1, width_margin=4/19-0.008/2):
        self.rows = rows
        self.cols = cols

        # board: height 24.1 cm, width 48.2 cm
        # cell: 4.7 cm
        # => height margin: 0.3 cm (on each side)
        self.height_margin = height_margin * board_height
        self.cell_h = self.cell_w = (board_height - 2*self.height_margin) / rows

        # epsilon = 0.008
        # margin_factor = 4/19 - epsilon/2  # margin in width relative to board width
        self.width_margin = width_margin * board_width  # margin in width

        
    def cell_bbox(self, row, col, margin=0.1) -> tuple[int,int,int,int]:
        """
        Calculates bounding box of a cell in the grid, with optional margin.
        
        :param row: row index of the cell (0-based)
        :param col: column index of the cell (0-based)
        :param margin: relative margin to add around the cell bbox (default 0.1, i.e. 10% of cell size)
        :return: tuple of (x1, y1, x2, y2) coordinates of the cell bounding box with added margin
        """
        assert 0 <= row < self.rows
        assert 0 <= col < self.cols

        x1 = self.width_margin + col * self.cell_w
        y1 = self.height_margin + row * self.cell_h
        x2 = x1 + self.cell_w
        y2 = y1 + self.cell_h

        dx = self.cell_w * margin
        dy = self.cell_h * margin

        return (
            int(x1 - dx),
            int(y1 - dy),
            int(x2 + dx),
            int(y2 + dy),
        )
    
    def crop_cells(self, board_img, margin=0.1):
        """
        Method takes an image of the rectified board and crops the cells based on the grid model, with optional margin.

        :param board_img: image of the rectified board
        :param margin: relative margin to add around the cell bbox (default 0.1, i.e. 10% of cell size)
        :return: list of dicts, each containing "row", "col" and "image" of the cropped cell
        """
        cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                x1, y1, x2, y2 = self.cell_bbox(r, c, margin)
                cell = board_img[
                    max(0, y1):min(board_img.shape[0], y2),
                    max(0, x1):min(board_img.shape[1], x2)
                ]
                cells.append({
                    "row": r,
                    "col": c,
                    "image": cell
                })

        return cells
