import os
from PIL import Image
import torch
from torchvision import transforms
import yaml
import numpy as np

from dataset_framework.augmentation.cell_augmentation import augment_image
from dataset_framework.variables import TRAIN_SET_VIEW_STATISTICS_TEMPLATE
from models.number_card_model import NumberCardModel
from models.number_special_card_model import NumberSpecialCardModel
from models.card_castle_model import CardCastleModel
from models.castle_color_model import CastleColorModel
from models.castle_rank_model import CastleRankModel
from models.special_card_model import SpecialCardModel


MODEL_VIEW_DICT = {
    "card_castle_model": "all",
    "castle_color_model": "castles_color",
    "castle_rank_model": "castles_rank",
    "number_special_card_model": "cards",
    "number_card_model": "number_cards",
    "special_card_model": "special_cards"
}

MODEL_NAMES = list(MODEL_VIEW_DICT.keys())

RUNS_DIR_PATH_TEMPLATE = "training/experiments/{model_name}"
CONF_FILE_PATH_TEMPLATE = RUNS_DIR_PATH_TEMPLATE + "/config.yaml"
RUN_DIR_PATH_TEMPLATE = RUNS_DIR_PATH_TEMPLATE + "/run_{run_num}"
SAVED_MODEL_PATH_TEMPLATE = RUN_DIR_PATH_TEMPLATE + "/model_{epoch}.pt"


def load_configuration(path):
    """
    Load YAML configuration from a file.
    
    :param path: Path to the YAML configuration file.
    :return dict: The loaded configuration as a dictionary.
    """
    with open(path) as f:
        config = yaml.safe_load(f)
    return config


def get_next_run_num(model_name):
    return len(os.listdir(RUNS_DIR_PATH_TEMPLATE.format(model_name=model_name)))


def get_transform(model_name=None, normalize=False):
    if normalize and model_name:
        mean, std = load_mean_std_from_yaml(TRAIN_SET_VIEW_STATISTICS_TEMPLATE.format(view=MODEL_VIEW_DICT.get(model_name, "all")))
        return transforms.Compose([
            transforms.Resize((100,100)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std)
        ])
    else:
        return transforms.Compose([
            transforms.Resize((100,100)),
            transforms.ToTensor()
        ])


def get_model(name):
    if name == "card_castle_model":
        return CardCastleModel()

    elif name == "castle_color_model":
        return CastleColorModel()

    elif name == "castle_rank_model":
        return CastleRankModel()

    elif name == "special_card_model":
        return SpecialCardModel()

    elif name == "number_special_card_model":
        return NumberSpecialCardModel()
    
    elif name == "number_card_model":
        return NumberCardModel()
    

    # if name == "resnet18":
    #     model = models.resnet18(pretrained=True)
    #     model.fc = torch.nn.Linear(model.fc.in_features, num_classes)

    # elif name == "resnet50":
    #     model = models.resnet50(pretrained=True)
    #     model.fc = torch.nn.Linear(model.fc.in_features, num_classes)

    else:
        raise ValueError("Unknown model")
    

def apply_custom_augmentation(image):
    """
    Bridge PIL image input to numpy augmentation and back to PIL.
    
    :param image: Input image as a PIL Image.
    :return PIL.Image: The augmented image as a PIL Image.
    """
    image_np = np.array(image)
    augmented_np = augment_image(image_np)
    return Image.fromarray(augmented_np)


def load_mean_std_from_yaml(path):
    """
    Load mean and standard deviation values from a YAML file.
    
    :param path: Path to the YAML file containing mean and std.
    :return tuple: A tuple containing the mean and standard deviation tensors.
    """
    with open(path) as f:
        stats = yaml.safe_load(f)
    mean = torch.tensor(stats["mean"])
    std = torch.tensor(stats["std"])
    return mean, std