import os
import sys
from torch.utils.data import DataLoader
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__)) # training directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from dataset_framework.variables import IMAGE_DIR, TRAIN_SET_VIEW_LABEL_TEMPLATE, TRAIN_SET_VIEW_STATISTICS_TEMPLATE
from training.image_dataset import ImageDataset
from training.utils import CONF_FILE_PATH_TEMPLATE, MODEL_VIEW_DICT, apply_custom_augmentation, get_transform, load_configuration


def compute_mean_std(loader):
    """
    Compute the mean and standard deviation of a dataset given a DataLoader.
    
    :param loader: DataLoader for the dataset to compute mean and std for.
    :return tuple: A tuple containing the mean and standard deviation tensors.
    """
    mean = 0.0
    std = 0.0
    n_total_samples = 0

    for images, _ in loader:
        n_batch_samples = images.size(0)
        images = images.view(n_batch_samples, images.size(1), -1)
        mean += images.mean(2).sum(0)
        std += images.std(2).sum(0)
        n_total_samples += n_batch_samples

    mean /= n_total_samples
    std /= n_total_samples

    return mean, std


def get_train_dataset_loader_for_model(config, transform):
    """
    Get the appropriate dataset for a given model based on the configuration.
    
    :param model_name: The name of the model to get the dataset for.
    :param template: The template for the dataset view.
    :param config: The configuration dictionary containing dataset information.
    :param transform: The transformation to apply to the dataset images.
    :return ImageDataset: An instance of ImageDataset for the specified model.
    """
    train_dataset = ImageDataset(
        IMAGE_DIR,
        TRAIN_SET_VIEW_LABEL_TEMPLATE.format(view=MODEL_VIEW_DICT.get(config.get("model"), "all")),
        config["label_dict"],
        transform,
        rgb=config.get("rgb", True),
        augment_fn=apply_custom_augmentation,
        num_augments_per_image=config.get("augments_per_image", 9),
    )
    train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True)
    return train_loader


if __name__ == "__main__":
    for model_name in MODEL_VIEW_DICT.keys():
        config = load_configuration(CONF_FILE_PATH_TEMPLATE.format(model_name=model_name))
        train_loader = get_train_dataset_loader_for_model(config, get_transform())
        mean, std = compute_mean_std(train_loader)
        print(f"\nModel: {model_name}\n  Mean: {mean}\n  Std: {std}")
        path = TRAIN_SET_VIEW_STATISTICS_TEMPLATE.format(view=MODEL_VIEW_DICT.get(model_name, "all"))
        print(f"  Saved to: {path}")
        # save to .yaml file
        with open(path, "w") as f:
            yaml.dump({"mean": mean.tolist(), "std": std.tolist()}, f)