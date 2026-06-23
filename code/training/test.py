import os
import sys
from torchvision import transforms
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, confusion_matrix, precision_score, recall_score, f1_score
import matplotlib.pyplot as plt
from tensorboard import program
import webbrowser


current_dir = os.path.dirname(os.path.abspath(__file__)) # training directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from dataset_framework.variables import IMAGE_DIR, TEST_SET_VIEW_LABEL_TEMPLATE
from image_dataset import ImageDataset
from utils import MODEL_VIEW_DICT, RUNS_DIR_PATH_TEMPLATE, SAVED_MODEL_PATH_TEMPLATE, CONF_FILE_PATH_TEMPLATE
from utils import load_configuration, get_next_run_num, get_transform, get_model


device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

print(device) # !

config = load_configuration(CONF_FILE_PATH_TEMPLATE.format(model_name="special_card_model")) # TODO path argument?
model_name = config['model']
normalize = config.get("normalize", False)

# Load test dataset
transform = get_transform(model_name, normalize)

# transform = transforms.Compose([
#         transforms.Resize((100,100)),
#         transforms.ToTensor(),
#         transforms.Grayscale(num_output_channels=3)
#         # transforms.RandomAffine(degrees=0, scale=(0.85, 1.15))
#     ])

test_dataset = ImageDataset(
    IMAGE_DIR,
    TEST_SET_VIEW_LABEL_TEMPLATE.format(view=MODEL_VIEW_DICT.get(config.get("model"), "all")),
    config["label_dict"],
    transform,
    rgb=config.get("rgb", True)
)
test_loader = DataLoader(test_dataset, batch_size=config["batch_size"], shuffle=False)

# Load model
run_num = 5 # get_next_run_num(model_name)-1
epoch = 47 # config["epochs"]-1 # !
model_params = torch.load(SAVED_MODEL_PATH_TEMPLATE.format(model_name=model_name, run_num=run_num, epoch=epoch), weights_only=True, map_location=device)
model = get_model(model_name)
model.load_state_dict(model_params)
model.eval()
model.to(device)

# Evaluate
all_preds = []
all_labels = []
failed_images = []

with torch.no_grad():
    for images, labels in test_loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        preds = outputs.argmax(dim=1)
        
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        
        # Store failed classifications
        failures = preds != labels
        for i, failed in enumerate(failures):
            if failed:
                failed_images.append({
                    'image': images[i].cpu(),
                    'true': labels[i].item(),
                    'pred': preds[i].item()
                })

print(f"Testing model {model_name} from run {run_num}, saved on epoch {epoch}")
print(f"Total test samples: {len(all_labels)}\n")
# Calculate metrics for each class
for class_label, class_index in config["label_dict"].items():
    class_preds = [1 if pred == class_index else 0 for pred in all_preds]
    class_labels = [1 if label == class_index else 0 for label in all_labels]
    
    accuracy = accuracy_score(class_labels, class_preds)
    precision = precision_score(class_labels, class_preds, zero_division=0)
    recall = recall_score(class_labels, class_preds, zero_division=0)
    f1 = f1_score(class_labels, class_preds, zero_division=0)
    
    print(f"Class '{class_label}' (index {class_index}):")
    print(f'  Accuracy: {accuracy:.4f}')
    print(f'  Precision: {precision:.4f}')
    print(f'  Recall: {recall:.4f}')
    print(f'  F1 Score: {f1:.4f}')
    print()

# Calculate metrics
conf_matrix = confusion_matrix(all_labels, all_preds)
accuracy = accuracy_score(all_labels, all_preds)
precision = precision_score(all_labels, all_preds, average='micro')
recall = recall_score(all_labels, all_preds, average='micro')
f1 = f1_score(all_labels, all_preds, average='micro')

print("Overall metrics:")
print(f"  Accuracy: {accuracy:.4f}")
print(f"  Precision: {precision:.4f}")
print(f"  Recall: {recall:.4f}")
print(f"  F1 Score: {f1:.4f}")
print("  Confusion Matrix (rows are true labels, columns are predicted labels):")
print(conf_matrix)
print()
print(f"Number of failed classifications: {len(failed_images)}")

# Display failed classifications
n = len(failed_images)
if n > 0:
    n_x = int(n**0.5) + 1
    n_y = (n - 1) // n_x + 1
    fig, axes = plt.subplots(n_y, n_x, figsize=(8, 8))
    for idx, (ax, failure) in enumerate(zip(axes.flat, failed_images[:n])):
        img = failure['image'].squeeze().numpy()
        # show rgb image if model is rgb, otherwise show grayscale
        if config.get("rgb", True):
            img = img.transpose(1, 2, 0) # CxHxW to HxWxC
            ax.imshow(img)
        else:
            ax.imshow(img, cmap='gray')
        ax.set_title(f"True: {failure['true']}, Pred: {failure['pred']}")
        ax.axis('off')
    plt.tight_layout()
    plt.show()

# run tensorboard with: tensorboard --logdir=training/experiments/{model_name}
tb = program.TensorBoard()
tb.configure(argv=[None, '--logdir', RUNS_DIR_PATH_TEMPLATE.format(model_name=config['model'])])
url = tb.launch()

print(f"TensorBoard running at {url}")
webbrowser.open(url)
input("Press Enter to exit...")