import json
from collections import defaultdict

from variables import OBJECT_LABELS, GROUND_TRUTH_LABELS, TRAIN_SET_LABELS, VALIDATION_SET_LABELS, TEST_SET_LABELS


def check_labels_completness(labels_file=GROUND_TRUTH_LABELS):
    """
    Checks if all combinations of labels are present in the dataset and counts the number of occurrences of each label. 
    Prints out any missing combinations and the total number of labeled cells.
    """
    print(f"\nChecking labels in {labels_file}...")
        # load labels
    with open(labels_file, "r") as f:
        labels = json.load(f)
    
    label_counts = defaultdict(int)
    
    # iterate over loaded labels and check if all combinations of object type, attribute name and attribute value exist in the labels, print missing ones
    for _, label in labels.items():
        obj_type = label["cell_type"]
        
        if obj_type not in OBJECT_LABELS:
            print(f"Unknown object type: {obj_type}")
            continue

        formatted_label = f"{obj_type}"
        if obj_type != "empty":
            obj_detailed_labels = label[obj_type]        
            for _, value in obj_detailed_labels.items():
                formatted_label += f"_{value}"

        label_counts[formatted_label] += 1

    # check if all combinations of labels exist and count each type
    total_sum = 0
    for obj_type, attributes in OBJECT_LABELS.items():
        if obj_type == "castle":
            # for castles, we want to check if all combinations of color and rank exist
            for color in attributes["color"]:
                for rank in attributes["rank"]:
                    label = f"{obj_type}_{color}_{rank}"
                    count = label_counts[label]
                    print(f"{label}: {count}{' (MISSING)' if count == 0 else ''}")
                    total_sum += count
                    
        elif obj_type == "card":
            for attr_name, attr_values in attributes.items():
                for value in attr_values:
                    label = f"{obj_type}_{attr_name}_{value}"
                    count = label_counts[label]
                    print(f"{label}: {count}{' (MISSING)' if count == 0 else ''}")
                    total_sum += count

        elif obj_type == "empty":
            label = f"{obj_type}"
            count = label_counts[label]
            print(f"{label}: {count}{' (MISSING)' if count == 0 else ''}")
            total_sum += count

    print(f"\nTotal labeled cells: {len(labels)}")
    print(f"Total correct labels: {total_sum}")

    if total_sum != len(labels):
        print(f"Invalid labels found: {len(labels) - total_sum}")


if __name__ == "__main__":
    check_labels_completness(GROUND_TRUTH_LABELS)
    check_labels_completness(TRAIN_SET_LABELS)
    check_labels_completness(VALIDATION_SET_LABELS)
    check_labels_completness(TEST_SET_LABELS)