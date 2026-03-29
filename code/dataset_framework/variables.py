OBJECT_LABELS = {
        "card": {
            "number": [-6, -5, -4, -3, -2, -1, 1, 2, 3, 4, 5, 6],
            "special": ["wizard", "dragon", "mountain", "gold mine"]
        },
        "castle": {
            "color": ["red", "blue", "green", "yellow"],
            "rank": [1, 2, 3, 4]
        },
        "empty": {}
    }

IMAGE_DIR = "dataset/cells/original_cell_images"

GROUND_TRUTH_LABELS = "dataset/cells/original_cell_images/labels.json"

TRAIN_SET_LABELS = "dataset/train_set/labels.json"
VALIDATION_SET_LABELS = "dataset/validation_set/labels.json"
TEST_SET_LABELS = "dataset/test_set/labels.json"

TRAIN_SET_VIEW_LABEL_TEMPLATE = "dataset/train_set/views/{view}/labels.json"
VALIDATION_SET_VIEW_LABEL_TEMPLATE = "dataset/validation_set/views/{view}/labels.json"
TEST_SET_VIEW_LABEL_TEMPLATE = "dataset/test_set/views/{view}/labels.json"

TRAIN_SET_VIEW_STATISTICS_TEMPLATE = "dataset/train_set/views/{view}/stats.yaml"

OG_BOARDS_DIR = "dataset/board/original_board_images"
RECTIFIED_BOARDS_DIR = "dataset/board/rectified_boards"
CROP_DEST_DIR = IMAGE_DIR