import sys
import os
import time
import torch
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from tensorboard import program
import webbrowser

current_dir = os.path.dirname(os.path.abspath(__file__)) # training directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from image_dataset import ImageDataset
from dataset_framework.variables import IMAGE_DIR, TRAIN_SET_VIEW_LABEL_TEMPLATE, VALIDATION_SET_VIEW_LABEL_TEMPLATE
from utils import MODEL_VIEW_DICT, CONF_FILE_PATH_TEMPLATE, SAVED_MODEL_PATH_TEMPLATE, RUNS_DIR_PATH_TEMPLATE, RUN_DIR_PATH_TEMPLATE
from utils import load_configuration, get_next_run_num, get_transform, get_model, apply_custom_augmentation


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def train_epoch(model, loader, optimizer, criterion):
    """
    Train the model for one epoch, iterating over the training DataLoader and updating model weights.
    
    :param model: The PyTorch model to be trained.
    :param loader: DataLoader for the training dataset.
    :param optimizer: The optimizer for training.
    :param criterion: The loss function to calculate training loss.
    :return float: The average training loss for the epoch.
    """
    model.train()
    total_loss = 0

    for images, labels in loader:
        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        outputs = model(images)
        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(loader)


def validate(model, loader, criterion):
    """
    Evaluate the model on the validation set, calculating average loss and accuracy.
    
    :param model: The PyTorch model to be evaluated.
    :param loader: DataLoader for the validation dataset.
    :param criterion: The loss function to calculate validation loss.
    :return tuple: A tuple containing the average validation loss and accuracy.
    """
    model.eval()
    total_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            outputs = model(images)

            loss = criterion(outputs, labels)
            total_loss += loss.item()

            preds = outputs.argmax(dim=1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

    accuracy = correct / total
    return total_loss / len(loader), accuracy


def train(model, train_loader, val_loader, optimizer, criterion, epochs, writer, run_num, model_name):
    """
    Train the model for a specified number of epochs, logging training and validation metrics to TensorBoard.
    Model is saved after each epoch in a directory named according to the model type and run number.
    Elapsed time for each epoch and total training time are printed to the console.

    :param model: The PyTorch model to be trained.
    :param train_loader: DataLoader for the training dataset.
    :param val_loader: DataLoader for the validation dataset.
    :param optimizer: The optimizer for training.
    :param criterion: The loss function.
    :param epochs: The number of epochs to train for.
    :param writer: The TensorBoard writer.
    :param run_num: The run number for saving checkpoints.
    """
    total_start_time = time.perf_counter()

    for epoch in range(epochs):
        epoch_start_time = time.perf_counter()
        train_loss = train_epoch(model, train_loader, optimizer, criterion)
        val_loss, val_acc = validate(model, val_loader, criterion)
        epoch_elapsed = time.perf_counter() - epoch_start_time

        print(
            f"Epoch {epoch} | "
            f"train_loss={train_loss:.4f} "
            f"val_loss={val_loss:.4f} "
            f"val_acc={val_acc:.4f} "
            f"elapsed={epoch_elapsed:.2f}s"
        )

        writer.add_scalar("Loss/train", train_loss, epoch)
        writer.add_scalar("Loss/val", val_loss, epoch)
        writer.add_scalar("Accuracy/val", val_acc, epoch)

        torch.save(
            model.state_dict(),
            SAVED_MODEL_PATH_TEMPLATE.format(model_name=model_name, run_num=run_num, epoch=epoch)
        )

    total_elapsed = time.perf_counter() - total_start_time
    print(f"Total training elapsed time: {total_elapsed:.2f}s")


if __name__ == "__main__":
    config = load_configuration(CONF_FILE_PATH_TEMPLATE.format(model_name="special_card_model")) # TODO path argument?
    transform = get_transform(config.get("model"), config.get("normalize", False))

    train_dataset = ImageDataset(
        IMAGE_DIR,
        TRAIN_SET_VIEW_LABEL_TEMPLATE.format(view=MODEL_VIEW_DICT.get(config.get("model"), "all")),
        config["label_dict"],
        transform,
        rgb=config.get("rgb", True),
        augment_fn=apply_custom_augmentation,
        num_augments_per_image=config.get("augments_per_image", 9),
    )
    val_dataset = ImageDataset(
        IMAGE_DIR,
        VALIDATION_SET_VIEW_LABEL_TEMPLATE.format(view=MODEL_VIEW_DICT.get(config.get("model"), "all")),
        config["label_dict"],
        transform,
        rgb=config.get("rgb", True)
    )

    train_loader = DataLoader(train_dataset, batch_size=config["batch_size"], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=config["batch_size"])

    model = get_model(config.get("model")).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=config["lr"], weight_decay=config.get("weight_decay", 0))
    criterion = torch.nn.CrossEntropyLoss()
    epochs = config["epochs"]

    # determine how many files are in the checkpoints directory and use that as the run number
    run_num = get_next_run_num(config['model'])
    writer = SummaryWriter(RUN_DIR_PATH_TEMPLATE.format(model_name=config['model'], run_num=run_num))

    print(f"Train set size: {len(train_dataset)}")
    print(f"Validation set size: {len(val_dataset)}")
    # write down model architecture in tensorboard text
    writer.add_text("Model/Architecture", str(model))

    train(model, train_loader, val_loader, optimizer, criterion, epochs, writer, run_num, config['model'])

    # run tensorboard with: tensorboard --logdir=diplomski/training/experiments/{model_name}
    tb = program.TensorBoard()
    tb.configure(argv=[None, '--logdir', RUNS_DIR_PATH_TEMPLATE.format(model_name=config['model'])])
    url = tb.launch()

    print(f"TensorBoard running at {url}")
    webbrowser.open(url)
    input("Press Enter to exit...")