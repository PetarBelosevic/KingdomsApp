import cv2
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from board.board_detection import detect_board
from board.board_rectification import rectify_board
from board.grid_model import GridModel

from variables import OG_BOARDS_DIR, RECTIFIED_BOARDS_DIR, CROP_DEST_DIR


def process_board_image(image_name:str, save_results:bool=True) -> None:
    """
    Method takes an image of the board, detects it, rectifies it and crops the cells, optionally saving the cropped cells to disk.
    
    :param image_name: filename of the board image to process (should be located in OG_BOARDS_DIR)
    :param save_results: if True, save rectified board and cropped cells to CROP_DEST_DIR
    """
    path = f"{OG_BOARDS_DIR}/{image_name}"
    # check of file exists
    if not cv2.haveImageReader(path):
        raise FileNotFoundError(f"File not found: {path}")

    img = cv2.imread(path)
    # resize if too large
    height, width = img.shape[:2]
    scale = 1.0
    if max(height, width) > 1000:
        scale = 1000 / max(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))

    # fixed_width = 1000
    # aspect_ratio = fixed_width / img.shape[1]
    # new_dimensions = (fixed_width, int(img.shape[0] * aspect_ratio))
    # img = cv2.resize(img, new_dimensions)

    corners = detect_board(img)
    rectified = rectify_board(img, corners, save_path=f"{RECTIFIED_BOARDS_DIR}/rectified_{image_name}" if save_results else None)

    grid = GridModel(rows=5, cols=6, board_width=rectified.shape[1], board_height=rectified.shape[0])
    cells = grid.crop_cells(rectified, margin=0.1)

    # ! plot all cells in single window for verification
    board_h = rectified.shape[0]
    board_w = rectified.shape[1]
    display_img = cv2.resize(rectified, (board_w, board_h))
    for cell in cells:
        r = cell["row"]
        c = cell["col"]
        x1, y1, x2, y2 = grid.cell_bbox(r, c, margin=0.0)
        cv2.rectangle(display_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.imshow("Cropped Cells", display_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if save_results:
        for cell in cells:
            cv2.imwrite(f"{CROP_DEST_DIR}/cell_{cell['row']}_{cell['col']}_{image_name}", cell["image"])



def process_new_board_image(save_results:bool=False) -> None:
    # list all images from OG_BOARDS_DIR that don't have corresponding rectified version in RECTIFIED_BOARDS_DIR
    og_images = set(os.listdir(OG_BOARDS_DIR))
    rectified_images = set(os.listdir(RECTIFIED_BOARDS_DIR))
    rectified_images = set([img.replace("rectified_", "") for img in rectified_images])
    images_to_process = og_images - rectified_images

    # print og images
    print("\nOriginal images:")
    for img in og_images:
        print(img)

    # print rectified images
    print("\nRectified images:")
    for img in rectified_images:
        print(img)

    while images_to_process:
        # list images to process
        print("\nImages to process:")
        for i,img in enumerate(images_to_process):
            print(f"{i}: {img}")

        print("\nSelect index of an image to process...")
        ind = int(input())

        image_name = list(images_to_process)[ind]
        process_board_image(image_name, save_results=save_results)
        images_to_process.remove(image_name)


def iterate_all_images():
    images = set(os.listdir(OG_BOARDS_DIR))
    print(len(images))

    for image_name in images:
        print(f"Processing {image_name}...")
        try:
            process_board_image(image_name, save_results=False)
        except RuntimeError as e:
            print("Failed!")
            print(e)


def iterate_bad_images():
    images = [
        "20260307_170006.jpg", 
        "20260307_165927.jpg",
        "20260307_165910.jpg",
    ]

    for image_name in images:
        print(f"Processing {image_name}...")
        try:
            process_board_image(image_name, save_results=False)
        except RuntimeError as e:
            print("Failed!")


if __name__ == "__main__":
    # 20260123_104439.jpg !
    # 20260123_104500.jpg 
    # 20260123_104508.jpg !!!!
    # 20260123_105352.jpg !
    # 20260123_105400.jpg 
    # 20260123_105405.jpg 

    # 20260307_165424.jpg 
    # 20260307_165951.jpg 
    # 20260307_165812.jpg !!!!
    # 20260307_170045.jpg 
    # 20260307_165314.jpg 
    # 20260307_170006.jpg !!! (svjetlost) <-
    # 20260307_165224.jpg 
    # 20260307_170059.jpg 
    # 20260307_165151.jpg 
    # 20260307_165927.jpg !!! (svjetlost) !!!!
    # 20260307_165210.jpg 
    # 20260307_164340.jpg 
    # 20260307_165910.jpg !!! (svjetlost) !!!! <-
    # 20260307_165827.jpg 
    # 20260307_165130.jpg 
    # 20260307_164330.jpg 
    # 20260307_170113.jpg 


    # 20260310_165804.jpg
    # 20260307_170006.jpg
    # 20260123_105352.jpg
    # 20260307_165151.jpg


    # 20260312_185651.jpg
    # 20260310_222953.jpg
    # 20260307_165224.jpg

    image_name = "20260307_165224.jpg"
    process_board_image(image_name, save_results=False)

    # iterate_all_images()
    # iterate_bad_images()

    # process_new_board_image(save_results=False)