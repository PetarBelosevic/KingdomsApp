import sys
import cv2
import os
import random
import numpy as np
import cell_augmentation

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from variables import IMAGE_DIR


def display_images_in_grid(images, cols=4, title="Image Grid"):
    """
    Display a list of images in a grid format using OpenCV.

    :param images: List of images as numpy arrays (typically read with cv2.imread).
    :param cols: Number of columns in the grid, default is 4.
    """
    num_images = len(images)
    rows = (num_images + cols - 1) // cols
    img_h, img_w = images[0].shape[:2]
    display_img = np.zeros((img_h * rows, img_w * cols, 3), dtype=np.uint8)

    for i, img in enumerate(images):
        row = i // cols
        col = i % cols
        display_img[row*img_h:(row+1)*img_h, col*img_w:(col+1)*img_w] = cv2.resize(img, (img_w, img_h))

    cv2.imshow(title, display_img)
    cv2.waitKey(0)


def test_glare_spread():
    img_path = os.path.join(IMAGE_DIR, random.choice(os.listdir(IMAGE_DIR)))
    img = cv2.imread(img_path)

    img = cell_augmentation.brightness_contrast(img, brightness=-30, contrast=0.95)

    augmented_images = [cell_augmentation.add_glare(img, intensity=0.7, center=(0.5, 0.5), spread=s) for s in range(1, 10)]
    display_images_in_grid(augmented_images, cols=3, title="Glare Spread Test")


def test_shadows():
    img_path = os.path.join(IMAGE_DIR, random.choice(os.listdir(IMAGE_DIR)))
    img = cv2.imread(img_path)

    print("Original image brightness:", np.mean(img))

    augmented_images = [img]
    augmented_images.extend([cell_augmentation.add_random_shadow(img) for _ in range(24)])
    display_images_in_grid(augmented_images, cols=5, title="Shadow Spread Test")


def test_shadow_lines():
    img_path = os.path.join(IMAGE_DIR, random.choice(os.listdir(IMAGE_DIR)))
    img = cv2.imread(img_path)
    
    print("Original image brightness:", np.mean(img))

    augmented_images = [img]
    augmented_images.extend([cell_augmentation.add_random_shadow_line(img) for _ in range(24)])
    display_images_in_grid(augmented_images, cols=5, title="Shadow Line Test")


if __name__ == "__main__":
    # test_glare_spread()
    # exit(0)
    # Example usage of the augmentation functions
    
    # list all images in the directory
    image_files = [f for f in os.listdir(IMAGE_DIR) if cv2.haveImageReader(os.path.join(IMAGE_DIR, f))]
    # select a random image    
    img_path = os.path.join(IMAGE_DIR, random.choice(image_files))
    img = cv2.imread(img_path)

    print("Original image brightness:", np.mean(img))

    # original + separate augmentations
    augmentations = cell_augmentation.apply_all_augmentations_separetly(img)
    all_images = [img] + augmentations
    display_images_in_grid(all_images, cols=4, title="Augmentations")

    N = 36
    # random augmentations
    random_aug_images = [img] + [cell_augmentation.augment_image(img) for _ in range(N-1)]
    display_images_in_grid(random_aug_images, cols=int(np.ceil(np.sqrt(N))), title="Random Augmentations")

    # glares
    # glared_images = cell_augmentation.generate_random_glares(img, num_glares=N)
    # display_images_in_grid(glared_images, cols=int(np.ceil(np.sqrt(N))), title="Random Glares")

    # shadows
    test_shadows()
    # shadow lines
    test_shadow_lines()
