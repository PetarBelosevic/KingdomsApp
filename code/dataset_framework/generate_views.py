# load labels.json
# load train/val/test splits

# for each view_definition:
#     create view directory
#     for each split:
#         for each image in split:
#             cell_label = labels[image]

#             if include_condition(cell_label):
#                 ! projected_label = project_label(cell_label)
#                 add image to view split
#                 store projected_label

import json
import os

from variables import TEST_SET_LABELS, TRAIN_SET_LABELS, VALIDATION_SET_LABELS
from variables import TEST_SET_VIEW_LABEL_TEMPLATE, TRAIN_SET_VIEW_LABEL_TEMPLATE, VALIDATION_SET_VIEW_LABEL_TEMPLATE


def filter_labels(condition, labels) -> dict:
    return {k: v for k, v in labels.items() if condition(v)}


def filter_all(labels) -> dict:
    return labels

def project_cell_type(label) -> dict:
    return label["cell_type"]


def filter_only_castles(labels) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "castle", labels)

# ! remove
def project_castle_labels(label) -> dict:
    if label["cell_type"] != "castle":
        raise ValueError("Label is not a castle")
    
    return {
        "color": label["castle"]["color"],
        "rank": label["castle"]["rank"]
    }

def project_castle_color(label) -> dict:
    if label["cell_type"] != "castle":
        raise ValueError("Label is not a castle")
    
    return label["castle"]["color"]

def project_castle_rank(label) -> dict:
    if label["cell_type"] != "castle":
        raise ValueError("Label is not a castle")
    
    return label["castle"]["rank"]


def filter_only_cards(labels) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "card", labels)

def project_card_type(label) -> dict:
    if label["cell_type"] != "card":
        raise ValueError("Label is not a card")
    
    return label["card"]["card_type"]


def filter_only_special_cards(labels) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "card" and label["card"]["card_type"] == "special", labels)

def project_special_card_type(label) -> dict:
    if label["cell_type"] != "card" or label["card"]["card_type"] != "special":
        raise ValueError("Label is not a special card")
    
    return label["card"]["special_type"]


def filter_only_number_cards(labels) -> dict:
    return filter_labels(lambda label: label["cell_type"] == "card" and label["card"]["card_type"] == "number", labels)

def project_number_card_type(label) -> dict:
    if label["cell_type"] != "card" or label["card"]["card_type"] != "number":
        raise ValueError("Label is not a number card")
    
    return label["card"]["value"]


def create_view(source_label_file_path, view_dest_path, filter, projection=lambda x: x):
    with open(source_label_file_path, "r") as f:
        labels = json.load(f)
    
    filtered_labels = filter(labels)
    projected_labels = {k: projection(v) for k, v in filtered_labels.items()}
    # ensure view_dest_path is valid
    os.makedirs(os.path.dirname(view_dest_path), exist_ok=True)

    # save filtered labels to view directory
    with open(view_dest_path, "w") as f:
        json.dump(projected_labels, f, indent=2)


def create_views_from_set(source_path:str, dest_path_template:str):
    create_view(source_path, dest_path_template.format(view="all"), filter_all, project_cell_type)
    create_view(source_path, dest_path_template.format(view="castles_color"), filter_only_castles, project_castle_color)
    create_view(source_path, dest_path_template.format(view="castles_rank"), filter_only_castles, project_castle_rank)
    create_view(source_path, dest_path_template.format(view="cards"), filter_only_cards, project_card_type)
    create_view(source_path, dest_path_template.format(view="special_cards"), filter_only_special_cards, project_special_card_type)
    create_view(source_path, dest_path_template.format(view="number_cards"), filter_only_number_cards, project_number_card_type)


def create_views_for_train_set():
    print("Creating views for train set...")
    create_views_from_set(TRAIN_SET_LABELS, TRAIN_SET_VIEW_LABEL_TEMPLATE)

def create_views_for_validation_set():
    print("Creating views for validation set...")
    create_views_from_set(VALIDATION_SET_LABELS, VALIDATION_SET_VIEW_LABEL_TEMPLATE)

def create_views_for_test_set():
    print("Creating views for test set...")
    create_views_from_set(TEST_SET_LABELS, TEST_SET_VIEW_LABEL_TEMPLATE)


if __name__ == "__main__":
    create_views_for_train_set()
    create_views_for_validation_set()
    create_views_for_test_set()
    