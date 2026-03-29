import json
import random

from variables import GROUND_TRUTH_LABELS, TEST_SET_LABELS, TRAIN_SET_LABELS, VALIDATION_SET_LABELS, OBJECT_LABELS
from generate_views import filter_labels


def filter_castles(labels, rank, color) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "castle" and label["castle"]["rank"] == rank and label["castle"]["color"] == color, labels)


def filter_numeric_cards(labels, value) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "card" and label["card"]["card_type"] == "number" and label["card"]["value"] == value, labels)


def filter_special_cards(labels, card_type) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "card" and label["card"]["card_type"] == "special" and label["card"]["special_type"] == card_type, labels)


def split_labels_by_classes(labels) -> list:
    classes = []

    classes.append(filter_labels(lambda label: label["cell_type"] == "empty", labels))
    for value in OBJECT_LABELS["card"]["number"]:
        classes.append(filter_numeric_cards(labels, value))
    for card_type in OBJECT_LABELS["card"]["special"]:
        classes.append(filter_special_cards(labels, card_type))
    for rank in OBJECT_LABELS["castle"]["rank"]:
        for color in OBJECT_LABELS["castle"]["color"]:
            classes.append(filter_castles(labels, rank, color))
    
    return classes


def split_dataset_by_classes(source, train_dest, validation_dest, test_dest, train_valid_test_ratios=(0.65, 0.2, 0.15)):
    source_labels = None
    with open(source, "r") as f:
        source_labels = json.load(f)

    classes = split_labels_by_classes(source_labels)
    splitted_labels = []

    for dataset_class in classes:
        total_labels = len(dataset_class)
        train_count = int(total_labels * train_valid_test_ratios[0])
        validation_count = int(total_labels * train_valid_test_ratios[1])
        # shuffle labels
        label_items = list(dataset_class.items()) # convert to list of tuples for shuffling
        random.shuffle(label_items)
        
        # split labels
        train_labels = dict(label_items[:train_count])
        validation_labels = dict(label_items[train_count:train_count + validation_count])
        test_labels = dict(label_items[train_count + validation_count:])

        splitted_labels.append((train_labels, validation_labels, test_labels))

    # merge splitted classes and save labels
    train_labels = {}
    validation_labels = {}
    test_labels = {}
    for train_class, validation_class, test_class in splitted_labels:
        train_labels.update(train_class)
        validation_labels.update(validation_class)
        test_labels.update(test_class)

    with open(train_dest, "w") as f:
        json.dump(train_labels, f, indent=2)
    print("Train set created!")

    with open(validation_dest, "w") as f:
        json.dump(validation_labels, f, indent=2)
    print("Validation set created!")

    with open(test_dest, "w") as f:
        json.dump(test_labels, f, indent=2)
    print("Test set created!")


def split_dataset(source, train_dest, validation_dest, test_dest, train_valid_test_ratios=(0.65, 0.2, 0.15)):
    source_labels = None
    with open(source, "r") as f:
        source_labels = json.load(f)
    total_labels = len(source_labels)
    train_count = int(total_labels * train_valid_test_ratios[0])
    validation_count = int(total_labels * train_valid_test_ratios[1])
    # shuffle labels
    label_items = list(source_labels.items()) # convert to list of tuples for shuffling
    random.shuffle(label_items)
    
    # split labels
    train_labels = dict(label_items[:train_count])
    validation_labels = dict(label_items[train_count:train_count + validation_count])
    test_labels = dict(label_items[train_count + validation_count:])
    # save labels
    with open(train_dest, "w") as f:
        json.dump(train_labels, f, indent=2)
    print("Train set created!")

    with open(validation_dest, "w") as f:
        json.dump(validation_labels, f, indent=2)
    print("Validation set created!")

    with open(test_dest, "w") as f:
        json.dump(test_labels, f, indent=2)
    print("Test set created!")


if __name__ == "__main__":
    # split_dataset(GROUND_TRUTH_LABELS, TRAIN_SET_LABELS, VALIDATION_SET_LABELS, TEST_SET_LABELS)
    split_dataset_by_classes(GROUND_TRUTH_LABELS, TRAIN_SET_LABELS, VALIDATION_SET_LABELS, TEST_SET_LABELS)