"""
Validate ONNX export accuracy by comparing PyTorch and ONNX model outputs on test images.
Tests a single model to detect if ONNX export introduces accuracy degradation.
"""
import os
import sys
import torch
import numpy as np
import onnxruntime as ort
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, confusion_matrix

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from dataset_framework.variables import (
    IMAGE_DIR,
    TRAIN_SET_VIEW_LABEL_TEMPLATE,
    VALIDATION_SET_VIEW_LABEL_TEMPLATE,
    TEST_SET_VIEW_LABEL_TEMPLATE,
)
from image_dataset import ImageDataset
from utils import MODEL_VIEW_DICT, SAVED_MODEL_PATH_TEMPLATE, CONF_FILE_PATH_TEMPLATE
from utils import load_configuration, get_transform, get_model
from model_exporting import BEST_MODEL_RUN_EPOCH

def validate_onnx_export(model_name="card_castle_model", run_num=15, epoch=98, dataset_split="test"):
    """
    Compare PyTorch model predictions vs ONNX model predictions on test set.
    
    :param model_name: Name of the model to validate
    :param run_num: Run number of the saved model
    :param epoch: Epoch of the saved model
    :param dataset_split: Which split to evaluate: train, validation, or test
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}\n")
    
    # Load configuration
    config = load_configuration(CONF_FILE_PATH_TEMPLATE.format(model_name=model_name))
    normalize = config.get("normalize", False)
    
    # Load requested split dataset
    split_label_templates = {
        "train": TRAIN_SET_VIEW_LABEL_TEMPLATE,
        "validation": VALIDATION_SET_VIEW_LABEL_TEMPLATE,
        "test": TEST_SET_VIEW_LABEL_TEMPLATE,
    }
    if dataset_split not in split_label_templates:
        raise ValueError("dataset_split must be one of: train, validation, test")

    transform = get_transform(model_name, normalize)
    split_dataset = ImageDataset(
        IMAGE_DIR,
        split_label_templates[dataset_split].format(view=MODEL_VIEW_DICT.get(model_name, "all")),
        config["label_dict"],
        transform,
        rgb=config.get("rgb", True)
    )
    split_loader = DataLoader(split_dataset, batch_size=config["batch_size"], shuffle=False)
    
    # Load PyTorch model
    weights_path = SAVED_MODEL_PATH_TEMPLATE.format(model_name=model_name, run_num=run_num, epoch=epoch)
    pytorch_model = get_model(model_name)
    pytorch_model.load_state_dict(torch.load(weights_path, weights_only=True, map_location=device))
    pytorch_model.eval()
    pytorch_model.to(device)
    
    # Load ONNX model
    onnx_path = f"mobile_app/onnx_models/{model_name}.onnx"
    onnx_session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    onnx_input_name = onnx_session.get_inputs()[0].name
    
    # Run predictions
    pytorch_preds = []
    onnx_preds = []
    all_labels = []
    mismatches = []
    
    print(f"Validating {model_name} (run {run_num}, epoch {epoch}) on {dataset_split} split...")
    print(f"Split size: {len(split_dataset)}\n")
    
    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(split_loader):
            # PyTorch predictions
            images_device = images.to(device)
            pytorch_outputs = pytorch_model(images_device)
            pytorch_batch_preds = pytorch_outputs.argmax(dim=1).cpu().numpy()
            
            # ONNX predictions
            images_np = images.numpy().astype(np.float32)
            onnx_outputs = onnx_session.run(None, {onnx_input_name: images_np})
            onnx_batch_preds = np.argmax(onnx_outputs[0], axis=1)
            
            pytorch_preds.extend(pytorch_batch_preds)
            onnx_preds.extend(onnx_batch_preds)
            all_labels.extend(labels.numpy())
            
            # Track mismatches between PyTorch and ONNX
            for i, (pt_pred, onnx_pred, label) in enumerate(
                zip(pytorch_batch_preds, onnx_batch_preds, labels.numpy())
            ):
                if pt_pred != onnx_pred:
                    mismatches.append({
                        'batch': batch_idx,
                        'index': i,
                        'pytorch_pred': int(pt_pred),
                        'onnx_pred': int(onnx_pred),
                        'true_label': int(label),
                        'pytorch_correct': pt_pred == label,
                        'onnx_correct': onnx_pred == label
                    })
    
    # Calculate metrics
    pytorch_accuracy = accuracy_score(all_labels, pytorch_preds)
    onnx_accuracy = accuracy_score(all_labels, onnx_preds)
    agreement = accuracy_score(pytorch_preds, onnx_preds)
    
    print("=" * 70)
    print("COMPARISON RESULTS")
    print("=" * 70)
    print(f"PyTorch Model Accuracy: {pytorch_accuracy:.4f}")
    print(f"ONNX Model Accuracy:    {onnx_accuracy:.4f}")
    print(f"Model Agreement:        {agreement:.4f} (how often they predict the same class)")
    print()
    
    # Detailed mismatch analysis
    if mismatches:
        print(f"Found {len(mismatches)} prediction MISMATCHES between PyTorch and ONNX:")
        print()
        
        # Count types of mismatches
        both_correct = sum(1 for m in mismatches if m['pytorch_correct'] and m['onnx_correct'])
        both_wrong = sum(1 for m in mismatches if not m['pytorch_correct'] and not m['onnx_correct'])
        pytorch_only_correct = sum(1 for m in mismatches if m['pytorch_correct'] and not m['onnx_correct'])
        onnx_only_correct = sum(1 for m in mismatches if not m['pytorch_correct'] and m['onnx_correct'])
        
        print(f"  Both models correct:        {both_correct}")
        print(f"  Both models wrong:          {both_wrong}")
        print(f"  PyTorch correct, ONNX wrong: {pytorch_only_correct} ❌ EXPORT ISSUE")
        print(f"  ONNX correct, PyTorch wrong: {onnx_only_correct} (unusual)")
        print()
        
        if pytorch_only_correct > 0:
            print("Cases where PyTorch is correct but ONNX is wrong (ACCURACY LOSS):")
            for i, m in enumerate([x for x in mismatches if x['pytorch_correct'] and not x['onnx_correct']][:5]):
                print(f"  [{i+1}] PyTorch→{m['pytorch_pred']}, ONNX→{m['onnx_pred']}, True={m['true_label']}")
            print()
    else:
        print("✓ No mismatches found! PyTorch and ONNX models produce identical predictions.")
        print()
    
    # Confusion matrices
    print("=" * 70)
    print("CONFUSION MATRICES")
    print("=" * 70)
    print("\nPyTorch Model:")
    print(confusion_matrix(all_labels, pytorch_preds))
    print("\nONNX Model:")
    print(confusion_matrix(all_labels, onnx_preds))
    print()
    
    return {
        'dataset_split': dataset_split,
        'pytorch_accuracy': pytorch_accuracy,
        'onnx_accuracy': onnx_accuracy,
        'agreement': agreement,
        'num_mismatches': len(mismatches),
        'mismatches': mismatches
    }


if __name__ == "__main__":
    # Test all models
    MODELS_TO_TEST = BEST_MODEL_RUN_EPOCH
    
    splits_to_test = ["train", "validation", "test"]
    results = {}
    for model_name, (run_num, epoch) in MODELS_TO_TEST.items():
        results[model_name] = {}
        for split in splits_to_test:
            print("\n" + "=" * 70)
            result = validate_onnx_export(model_name, run_num, epoch, dataset_split=split)
            results[model_name][split] = result

            if result['num_mismatches'] > 0:
                print(
                    f"\n[WARN] {model_name} ({split}): "
                    f"Found {result['num_mismatches']} mismatches!"
                )
            else:
                print(f"\n[OK] {model_name} ({split}): Perfect agreement (no mismatch)")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    for model_name, split_results in results.items():
        for split, result in split_results.items():
            status = "[OK]" if result['num_mismatches'] == 0 else "[WARN]"
            print(
                f"{status} {model_name:30} | split: {split:10} "
                f"| PT: {result['pytorch_accuracy']:.4f} "
                f"| ONNX: {result['onnx_accuracy']:.4f} "
                f"| Mismatches: {result['num_mismatches']}"
            )
