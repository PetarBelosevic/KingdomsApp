import sys
import torch
import os
    
current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Example: replace with your actual model classes
from models.card_castle_model import CardCastleModel
from models.castle_color_model import CastleColorModel
from models.castle_rank_model import CastleRankModel
from models.number_card_model import NumberCardModel
from models.number_special_card_model import NumberSpecialCardModel
from models.special_card_model import SpecialCardModel
from training.utils import SAVED_MODEL_PATH_TEMPLATE, MODEL_NAMES, get_model

EXPORT_DIR = "mobile_app/onnx_models"
os.makedirs(EXPORT_DIR, exist_ok=True)


BEST_MODEL_RUN_EPOCH = {
    "card_castle_model": (15, 98),
    "castle_color_model": (6, 42),
    "castle_rank_model": (39, 68),
    "number_special_card_model": (1, 17),
    "number_card_model": (2, 52),
    "special_card_model": (4, 34) # (4, 46)
}


def export_model(model, weights_path, output_path, input_shape):
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    dummy_input = torch.randn(*input_shape)

    torch.onnx.export(
        model,
        dummy_input,
        output_path,
        export_params=True,
        opset_version=14,  # Explicit opset version for stability (not None, which picks default)
        do_constant_folding=True,
        input_names=["input"],
        output_names=["output"],
        dynamic_axes={
            "input": {0: "batch_size"},
            "output": {0: "batch_size"}
        }
    )

    print(f"Exported: {output_path}")


if __name__ == "__main__":
    for model_name in MODEL_NAMES:
        model = get_model(model_name)
        run_num, epoch = BEST_MODEL_RUN_EPOCH[model_name]
        weights_path = SAVED_MODEL_PATH_TEMPLATE.format(model_name=model_name, run_num=run_num, epoch=epoch)
        output_path = f"{EXPORT_DIR}/{model_name}.onnx"
        export_model(model, weights_path, output_path, (1, 3, 100, 100))




    # export_model(
    #     CardCastleModel(),
    #     "weights/card_castle_model.pth",
    #     f"{EXPORT_DIR}/card_castle_model.onnx",
    #     (1, 3, 224, 224)
    # )

    # export_model(
    #     CastleColorModel(),
    #     "weights/castle_color_model.pth",
    #     f"{EXPORT_DIR}/castle_color_model.onnx",
    #     (1, 3, 224, 224)
    # )

    # export_model(
    #     CastleRankModel(),
    #     "weights/castle_rank_model.pth",
    #     f"{EXPORT_DIR}/castle_rank_model.onnx",
    #     (1, 3, 224, 224)
    # )

    # export_model(
    #     NumberCardModel(),
    #     "weights/number_card_model.pth",
    #     f"{EXPORT_DIR}/number_card_model.onnx",
    #     (1, 3, 224, 224)
    # )

    # export_model(
    #     NumberSpecialCardModel(),
    #     "weights/number_special_card_model.pth",
    #     f"{EXPORT_DIR}/number_special_card_model.onnx",
    #     (1, 3, 224, 224)
    # )

    # export_model(
    #     SpecialCardModel(),
    #     "weights/special_card_model.pth",
    #     f"{EXPORT_DIR}/special_card_model.onnx",
    #     (1, 3, 224, 224)
    # )