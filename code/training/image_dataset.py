import json
import os
from PIL import Image
import torch
from torch.utils.data import Dataset


class ImageDataset(Dataset):
    """
    Implements a PyTorch Dataset for loading images and their corresponding labels from a specified directory and label file.
    Supports optional data augmentation and can handle both RGB and grayscale images.

    :param image_dir: Path to the directory containing the images.
    :param label_file: Path to the JSON file containing image labels.
    :param label_dict: A dictionary mapping label names (as found in the label file) to integer class indices.
    :param transform: A function/transform to apply to the images after loading (e.g., for normalization).
    :param rgb: Whether to load images in RGB mode (True) or grayscale (False). Default is True.
    :param augment_fn: A function to apply for data augmentation. If
        None, no augmentation is applied. Default is None.
    :param num_augments_per_image: The number of augmented variants to generate per original image. Default is 0 (no augmentation).

    """
    def __init__(self, image_dir:str, label_file:str, label_dict:dict, transform=None, rgb:bool=True, augment_fn=None, num_augments_per_image:int=0):
        self.image_dir = image_dir
        self.transform = transform
        self.rgb = rgb
        self.augment_fn = augment_fn
        self.num_augments_per_image = max(0, int(num_augments_per_image))
        self.label_dict = label_dict

        if self.augment_fn is None or self.num_augments_per_image == 0:
            self.samples_per_image = 1
            self.should_augment = False
        else:
            self.samples_per_image = self.num_augments_per_image + 1
            self.should_augment = True

        with open(label_file) as f:
            self.labels = json.load(f)

        self.image_names = list(self.labels.keys())


    def __len__(self):
        return len(self.image_names) * self.samples_per_image

    def __getitem__(self, idx):
        base_idx = idx // self.samples_per_image
        variant_idx = idx % self.samples_per_image

        img_name = self.image_names[base_idx]
        img_path = os.path.join(self.image_dir, img_name)
        image = Image.open(img_path)
        image = image.convert("RGB") if self.rgb else image.convert("L") # L -> grayscale
        label = self.label_dict.get(self.labels[img_name])
        label = torch.tensor(label, dtype=torch.long)

        if self.should_augment and variant_idx > 0:
            image = self.augment_fn(image)

        if self.transform:
            image = self.transform(image)

        return image, label