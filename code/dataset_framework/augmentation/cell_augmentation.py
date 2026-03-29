"""
Image augmentation module for cell dataset processing.
This module provides various image augmentation techniques for data preprocessing,
including rotations, blur effects, brightness/contrast adjustments, and glare effects.\n
Functions:\n
    random_rotate_image(img): 
        Rotate image by a random 90-degree angle.\n
    rotate_image_all_angles(img): 
        Generate all 90-degree rotations of an image.\n
    apply_gaussian_blur(img, kernel_size=5): 
        Apply Gaussian blur to an image.\n
    random_brightness_contrast(img, brightness_range=(-80, 80), contrast_range=(0.60, 1.4)): 
        Randomly adjust brightness and contrast.\n
    brightness_contrast(img, contrast=1.0, brightness=0): 
        Adjust brightness and contrast with specified values.\n
    add_glare(img, intensity=0.7, center=(0.5, 0.5)): 
        Add radial glare effect to an image at specified center and intensity.\n
    random_glare(img): 
        Add glare effect with random intensity and center position.\n
Dependencies:
    - OpenCV (cv2)
    - NumPy (np)
    - random
"""
# Albumentations
    # RandomBrightnessContrast
    # GaussianNoise
    # Blur (light!)
    # Hue/Saturation shift (small)
    # Rotate (±3–5°)
    # JPEG compression

# Roboflow

# Blender

# TODO: salt and pepper noise, cutout, random erasing ?
# TODO: dokumentirati
# TODO: implementirati funkciju koja primjenjuje random kombinaciju augmentacija na sliku, ne sve odjednom, nego random subset ?
# TODO: igrati se jos

import cv2
import numpy as np
import random

BRIGHTNESS_HIGH_THRESHOLD = 136 # if image is brighter than this, it might already have some shadows and is already bright enough
BRIGHTNESS_LOW_THRESHOLD = 82

def get_line_parameters(x1, y1, x2, y2):
    """
    Calculate the parameters a, b, c for the line equation ax + by + c = 0 given two points (x1, y1) and (x2, y2).

    :param x1: x-coordinate of the first point.
    :param y1: y-coordinate of the first point.
    :param x2: x-coordinate of the second point.
    :param y2: y-coordinate of the second point.
    :return tuple: A tuple containing the parameters (a, b, c) for the line equation.
    """
    a = y2 - y1
    b = x1 - x2
    c = x2*y1 - x1*y2
    return a, b, c


def get_distance_from_line_map(a, b, c, h, w, absolute=True):
    """
    Generate a distance map from a line defined by parameters a, b, c for an image of height h and width w.

    :param a: Parameter a of the line equation ax + by + c = 0.
    :param b: Parameter b of the line equation ax + by + c = 0.
    :param c: Parameter c of the line equation ax + by + c = 0.
    :param h: Height of the image.
    :param w: Width of the image.
    :return numpy.ndarray: A 2D array where each value represents the distance from the line for each pixel.
    """
    Y, X = np.ogrid[:h, :w]
    map = (a*X + b*Y + c).astype(np.float32)
    distance_map = map / np.sqrt(a**2 + b**2 + 1e-10) # add small value to avoid division by zero
    if absolute:
        distance_map = np.abs(distance_map)
    return distance_map

# --------------------------------------------------------------------------------

# rotation
def random_rotate_image(img):
    """
    Rotate an image by a random angle (90, 180, or 270 degrees).

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :return numpy.ndarray: The rotated image with the same data type as the input.
    """
    angle = random.choice([cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE])
    return cv2.rotate(img, angle)


def rotate_image_all_angles(img):
    """
    Generate all 90-degree rotations of an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :return List[numpy.ndarray]: A list containing all 90-degree rotations of the input image.
    """
    angles = [cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE]
    return [cv2.rotate(img, angle) for angle in angles]

# --------------------------------------------------------------------------------

# blur
def apply_gaussian_blur(img, kernel_size=5):
    """
    Apply Gaussian blur to an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param kernel_size: Size of the Gaussian kernel (must be a positive odd integer).
    :return numpy.ndarray: The blurred image with the same data type as the input.
    """
    return cv2.GaussianBlur(img, (kernel_size, kernel_size), 0)

# --------------------------------------------------------------------------------

# brightness and contrast
def random_brightness_contrast(img, brightness_range=(0.8, 1.2), contrast_range=(0.8, 1.20)):
    """
    Randomly adjust the brightness and contrast of an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param brightness_range: Tuple specifying the range for random brightness adjustment (min, max), default is (0.8, 1.2).
    :param contrast_range: Tuple specifying the range for random contrast adjustment (min, max), default is (0.8, 1.20).
    :return numpy.ndarray: The adjusted image with the same data type as the input.
    """
    # if image is already bright, it might already have some shadows, so skip adding shadows
    brightness = np.mean(img)
    # put red dot on the image to indicate brightness level for testing
    if brightness > BRIGHTNESS_HIGH_THRESHOLD and (brightness_range[0] + brightness_range[1])/2 >= 1.0:
        brightness_range = (brightness_range[0] - 0.15, brightness_range[1] - 0.15) # bias towards darker images
    
    if brightness < BRIGHTNESS_LOW_THRESHOLD and (brightness_range[0] + brightness_range[1])/2 <= 1.0:
        brightness_range = (brightness_range[0] + 0.15, brightness_range[1] + 0.15) # bias towards brighter images
    
    brightness = brightness * (random.uniform(*brightness_range) - 1)
    contrast = random.uniform(*contrast_range)
    img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
    return img


def brightness_contrast(img, contrast=1.0, brightness=0):
    """
    Adjust the brightness and contrast of an image with specified values.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param contrast: Contrast adjustment factor (default is 1.0, where 1.0 means no change).
    :param brightness: Brightness adjustment value (default is 0, where 0 means no change).
    :return numpy.ndarray: The adjusted image with the same data type as the input.
    """
    return cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)

# --------------------------------------------------------------------------------

# glare
def add_glare(img, intensity=0.6, center=(0.5, 0.5), spread=4):
    """
    Add a radial glare effect to an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param intensity: Intensity of the glare effect (0 to 1, where 0 means no glare and 1 means maximum glare), default is 0.7.
    :param center: Tuple specifying the center of the glare as a fraction of the image dimensions (x, y), default is (0.5, 0.5) for the center of the image.
    :param spread: Exponent for the radial falloff of the glare effect, greater values create sharper falloff, default is 4.
    :return numpy.ndarray: The image with the added glare effect, with the same data type as the input.
    """
    h, w = img.shape[:2]
    # # if image is too dark, increase brightness and contrast
    brightness = np.mean(img)
    if brightness > BRIGHTNESS_HIGH_THRESHOLD:
        intensity *= 0.5 # reduce glare intensity for already bright images

    if brightness < BRIGHTNESS_LOW_THRESHOLD:
        # print("Image is too dark, increasing brightness and contrast for glare to be more visible")
        min_brightness_increase = ((BRIGHTNESS_LOW_THRESHOLD + BRIGHTNESS_HIGH_THRESHOLD) / 2) / brightness
        img = random_brightness_contrast(img, brightness_range=(min_brightness_increase, min_brightness_increase + 0.15), contrast_range=(1.05, 1.2))
    
    # Random glare center
    center_x = int(w * center[0])
    center_y = int(h * center[1])
    
    # Create radial mask
    Y, X = np.ogrid[:h, :w]
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    max_dist = np.sqrt(w**2 + h**2)
    
    mask = (1 - dist_from_center / max_dist)**spread # => exponent 
    mask = np.clip(mask, 0, 1)
    mask = mask * intensity
    
    glare = img.astype(np.float32)
    
    if len(img.shape) == 2: # grayscale
        glare = glare + 255*mask
    else: # color
        for c in range(3):
            glare[:, :, c] = glare[:, :, c] + 255*mask
    
    glare = np.clip(glare, 0, 255).astype(np.uint8)
    return glare


def random_glare(img):
    """
    Add a glare effect with random intensity and center position.
    
    :param img: Input image as a numpy array (typically read with cv2.imread).
    :return numpy.ndarray: The image with the added random glare effect, with the same data type as the input.
    """
    intensity = random.uniform(0.2, 0.55)
    center = (random.uniform(0.0, 1.0), random.uniform(0.0, 1.0))
    spread = random.uniform(2, 4)
    return add_glare(img, intensity=intensity, center=center, spread=spread)


def generate_random_glares(img, num_glares=3):
    """
    Generate multiple random glare effects on an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param num_glares: Number of random glares to add to the image, default is 3.
    :return numpy.ndarray: The image with the added random glares, with the same data type as the input.
    """
    augmented_images = []
    for _ in range(num_glares):
        augmented_images.append(random_glare(img))
    return augmented_images

# --------------------------------------------------------------------------------

# shadow
def add_random_shadow(img, intensity_range=(0.4, 0.65), sharpness_range=(0.06, 0.09)):
    """
    Add a random shadow to an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param intensity_range: Range of intensity values for the shadow effect (0 to 1), default is (0.4, 0.65).
    :param sharpness_range: Range of sharpness values for the shadow effect, default is (0.06, 0.09). Greater values create less sharp shadows.
    :return numpy.ndarray: The image with the added random shadow, with the same data type as the input.
    """
    h, w = img.shape[:2]
    # if image is already bright, it might already have some shadows, so skip adding shadows
    brightness = np.mean(img)
    # put red dot on the image to indicate brightness level for testing
    if brightness > BRIGHTNESS_HIGH_THRESHOLD:
        # print("Image is too bright, skipping shadow augmentation")
        return img
    
    if brightness < BRIGHTNESS_LOW_THRESHOLD:
        # print("Image is too dark, increasing brightness and contrast")
        min_brightness_increase = ((BRIGHTNESS_LOW_THRESHOLD + BRIGHTNESS_HIGH_THRESHOLD) / 2) / brightness
        img = random_brightness_contrast(img, brightness_range=(min_brightness_increase, min_brightness_increase + 0.15), contrast_range=(1.05, 1.2))
        brightness = np.mean(img)
        
    shadow_intensity = random.uniform(*intensity_range)
    sharpness = random.uniform(*sharpness_range) * np.sqrt(h**2 + w**2) # convert to pixels based on image size

    # make image brighter to make shadow more visible, bias towards brighter images
    img = brightness_contrast(img, contrast=1.0 + (shadow_intensity / 4), brightness=random.randint(10, int(brightness*shadow_intensity/2)))

    # Randomly choose 2 points to define the shadow line
    x1, y1 = random.randint(0, w), random.randint(0, h)
    x2, y2 = random.randint(0, w), random.randint(0, h)

    # determine a, b, c for the line equation ax + by + c = 0
    a, b, c = get_line_parameters(x1, y1, x2, y2)

    # create a mask on every pixel above the line
    mask = get_distance_from_line_map(a, b, c, h, w, absolute=False)

    # clip mask to 0-1
    mask = np.clip(mask, 0, sharpness) / sharpness
    mask = mask.astype(np.float32) * shadow_intensity

    shadowed_img = img.astype(np.float32)

    if len(img.shape) == 2: # grayscale
        shadowed_img = shadowed_img * (1 - mask)
    else: # color
        for c in range(3):
            shadowed_img[:, :, c] = shadowed_img[:, :, c] * (1 - mask)

    shadowed_img = np.clip(shadowed_img, 0, 255).astype(np.uint8)
    return shadowed_img


def add_random_shadow_line(img, intensity_range=(0.4, 0.65), sharpness_range=(0.06, 0.09), width_range=(0.15, 0.4)):
    """
    Add a random shadow line to an image. Line connects random point on the edge to the random point on the image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :param intensity_range: Range of intensity values for the shadow effect (0 to 1), default is (0.4, 0.65).
    :param sharpness_range: Range of sharpness values for the shadow effect, default is (0.06, 0.09).
    :param width_range: Range of width values for the shadow line as a fraction of the image diagonal, default is (0.15, 0.4).
    :return numpy.ndarray: The image with the added random shadow line, with the same data type as the input.
    """
    h, w = img.shape[:2]
    # if image is already bright, it might already have some shadows, so skip adding shadows
    brightness = np.mean(img)
    # put red dot on the image to indicate brightness level for testing
    if brightness > BRIGHTNESS_HIGH_THRESHOLD:
        # print("Image is too bright, skipping shadow augmentation")
        return img
    
    if brightness < BRIGHTNESS_LOW_THRESHOLD:
        # print("Image is too dark, increasing brightness and contrast")
        min_brightness_increase = ((BRIGHTNESS_LOW_THRESHOLD + BRIGHTNESS_HIGH_THRESHOLD) / 2) / brightness
        img = random_brightness_contrast(img, brightness_range=(min_brightness_increase, min_brightness_increase + 0.15), contrast_range=(1.05, 1.2))
    
    shadow_intensity = random.uniform(*intensity_range)
    sharpness = random.uniform(*sharpness_range) * np.sqrt(h**2 + w**2) # convert to pixels based on image size
    width = random.uniform(*width_range) * np.sqrt(h**2 + w**2)

    # make image brighter to make shadow more visible, bias towards brighter images
    img = brightness_contrast(img, contrast=1.0 + (shadow_intensity / 4), brightness=random.randint(10, int(brightness*shadow_intensity/2)))

    # Randomly choose a point 
    x1,y1 = random.randint(0, w), random.randint(0, h)
    # Randomly choose a direction of the line
    angle = random.uniform(0, 2*np.pi)

    # determine a, b, c for the line equation ax + by + c = 0
    a, b, c = get_line_parameters(x1, y1, x1 + np.cos(angle), y1 + np.sin(angle))

    # create a mask based on distance from the line
    mask1 = get_distance_from_line_map(a, b, c, h, w, absolute=True)
    # mask1 = width/2 - mask1 # invert to create a band around the line

    # get the parameters for the perpendicular line to create a band around the line
    a_perp, b_perp, c_perp = get_line_parameters(x1, y1, x1 + np.cos(angle + np.pi/2), y1 + np.sin(angle + np.pi/2))
    mask2 = get_distance_from_line_map(a_perp, b_perp, c_perp, h, w, absolute=False)
    # mask2 = width/2 - mask2 # invert to create a band around the line

    mask = np.max([mask1, mask2], axis=0) # combine the two masks to create a band around the line
    mask = width/2 - mask

    # create a band around the line based on width and sharpness
    mask = np.clip(mask, 0, sharpness) / sharpness
    mask = mask.astype(np.float32) * shadow_intensity

    shadowed_img = img.astype(np.float32)

    if len(img.shape) == 2: # grayscale
        shadowed_img = shadowed_img * (1 - mask)
    else: # color
        for c in range(3):
            shadowed_img[:, :, c] = shadowed_img[:, :, c] * (1 - mask)

    shadowed_img = np.clip(shadowed_img, 0, 255).astype(np.uint8)
    return shadowed_img

# --------------------------------------------------------------------------------

# all augmentations
def apply_all_augmentations_separetly(img):
    """
    Apply all augmentations separately to an image.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :return list: List of augmented images.
    """
    augmented_images = []
    
    # Apply rotation
    rotated_images = rotate_image_all_angles(img)
    augmented_images.extend(rotated_images)
    
    # Apply brightness and contrast adjustments
    augmented_images.append(random_brightness_contrast(img, brightness_range=(0.6, 1.0), contrast_range=(1.0, 1.0)))
    augmented_images.append(random_brightness_contrast(img, brightness_range=(1.0, 1.4), contrast_range=(1.0, 1.0)))
    augmented_images.append(random_brightness_contrast(img, brightness_range=(1.0, 1.0), contrast_range=(1.1, 1.5)))
    augmented_images.append(random_brightness_contrast(img, brightness_range=(1.0, 1.0), contrast_range=(0.5, 0.9)))
    
    # Apply Gaussian blur
    augmented_images.append(apply_gaussian_blur(img))
    
    # Apply glare effects
    augmented_images.append(random_glare(img))

    # Apply random shadow
    augmented_images.append(add_random_shadow(img))

    # Apply random shadow line
    augmented_images.append(add_random_shadow_line(img))
    
    return augmented_images


# TODO: add logic
def augment_image(img):
    """
    Apply a combination of random augmentations to an image, including 90-degree rotation, brightness/contrast adjustment, Gaussian blur, and glare effect.

    :param img: Input image as a numpy array (typically read with cv2.imread).
    :return numpy.ndarray: The augmented image with the same data type as the input.
    """
    augmented_img = img.copy()
    # 75% chance to apply random rotation
    if random.random() < 0.75:
        augmented_img = random_rotate_image(img)

    # 40% chance to apply random glare
    if random.random() < 0.4:
        augmented_img = random_glare(augmented_img)

        # 40% chance to apply random brightness and contrast adjustment
        # bias towards darker images
        # if random.random() < 0.4:
        #     augmented_img = random_brightness_contrast(augmented_img, brightness_range=(0.8, 1.1), contrast_range=(0.85, 1.1))
    # else 40% chance to apply default brightness and contrast adjustment
    elif random.random() < 0.4:
        augmented_img = random_brightness_contrast(augmented_img)
    # else 60% chance to apply random shadow
    elif random.random() < 0.60:
        if random.random() < 0.5:
            augmented_img = add_random_shadow(augmented_img)
        else:
            augmented_img = add_random_shadow_line(augmented_img)

    # 25% chance to apply Gaussian blur
    if random.random() < 0.25:
        augmented_img = apply_gaussian_blur(augmented_img)
    return augmented_img