# rectifies board
import cv2
import numpy as np

# cannonical board size
BOARD_HEIGHT = 500
BOARD_WIDTH = 2*BOARD_HEIGHT # standard ratio 2:1 for the board


def rectify_board(image, corners, width=BOARD_WIDTH, height=BOARD_HEIGHT, save_path=None):
    """
    Method takes an image and 4 corners of the board in the image and applies perspective transformation to obtain a rectified image of the board.
    
    :param image: original image containing the board
    :param corners: array of shape (4, 2) containing the coordinates of the corners of the board in the original image, ordered in consistent way
    :param width: desired width of the rectified board image (default BOARD_WIDTH)
    :param height: desired height of the rectified board image (default BOARD_HEIGHT)
    :param save_path: if not None, path to save the rectified board image
    """
    target_corners = np.array([
        [0, 0],
        [width - 1, 0],
        [width - 1, height - 1],
        [0, height - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(corners, target_corners)
    warped = cv2.warpPerspective(image, M, (width, height))

    if save_path is not None:
        cv2.imwrite(save_path, warped)

    return warped

