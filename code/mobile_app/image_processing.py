import sys
import cv2
import numpy as np
import os

current_dir = os.path.dirname(os.path.abspath(__file__)) # dataset_framework directory
project_root = os.path.dirname(current_dir) # diplomski directory
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from board.board_detection import detect_board
from board.board_rectification import rectify_board
from board.grid_model import GridModel


def rectify_image(img):
    # resize if too large
    height, width = img.shape[:2]
    scale = 1.0
    if max(height, width) > 1000:
        scale = 1000 / max(height, width)
        img = cv2.resize(img, (int(width * scale), int(height * scale)))

    corners = detect_board(img)
    rectified = rectify_board(img, corners, save_path=None)

    return rectified


class BoardModel:
    def __init__(self, path_to_models=None):
        if path_to_models is None:
            app_dir = os.path.dirname(os.path.abspath(__file__))
            path_to_models = os.path.join(app_dir, "onnx_models")
        self.models = ModelService(path_to_models)


    def crop_cells_from_image(self, rectified_img):
        grid = GridModel(rows=5, cols=6, board_width=rectified_img.shape[1], board_height=rectified_img.shape[0])
        cells = grid.crop_cells(rectified_img, margin=0.1)
        return cells


    def generate_board_model(self, rectified_img) -> list[list[str|int]]:
        cells = self.crop_cells_from_image(rectified_img)
        board_model = [[]]
        for cell in cells:
            row = cell["row"]
            col = cell["col"]
            image = cell["image"]

            while row >= len(board_model):
                board_model.append([])

            while col >= len(board_model[row]):
                board_model[row].append("?")

            prediction = self.process_one_cell(image)
            board_model[row][col] = prediction

        return board_model


    def process_one_cell(self, cell_image) -> str|int:
        # Match training preprocessing as closely as possible:
        # BGR -> RGB, resize to 100x100, scale to [0, 1], NCHW float32
        cell_image = cv2.cvtColor(cell_image, cv2.COLOR_BGR2RGB)
        cell_image = cv2.resize(cell_image, (100, 100), interpolation=cv2.INTER_LINEAR)
        cell_image = cell_image.astype(np.float32) / 255.0
        cell_image = cell_image.transpose(2, 0, 1)
        cell_image = np.expand_dims(cell_image, axis=0)

        prediction = self.models.predict("card_castle_model", cell_image)

        if prediction == 0: # card
            prediction = self.models.predict("number_special_card_model", cell_image)

            if prediction == 0: # number card
                prediction = self.models.predict("number_card_model", cell_image)
                if prediction <= 5:
                    return int(prediction) - 6
                else:
                    return int(prediction) - 5
                
            else: # special card
                prediction = self.models.predict("special_card_model", cell_image)
                if prediction == 0:
                    return "d"
                elif prediction == 1:
                    return "gm"
                elif prediction == 2:
                    return "m"
                else:
                    return "w"
                
        elif prediction == 1: # castle
            color = self.models.predict("castle_color_model", cell_image)
            rank = self.models.predict("castle_rank_model", cell_image)
            rank += 1
            if color == 0:
                return f"r{rank}"
            elif color == 1:
                return f"g{rank}"
            elif color == 2:
                return f"b{rank}"
            else:
                return f"y{rank}"
        
        else: # empty
            return "e"
    


class ModelService:
    def __init__(self, model_dir="mobile_app/onnx_models"):
        self.sessions = {}
        self.input_names = {}
        self.output_names = {}

        self._load_models(model_dir)


    def _load_models(self, model_dir):
        try:
            import onnxruntime as ort
        except Exception as exc:
            raise RuntimeError(f"onnxruntime is not available: {exc}") from exc

        if not os.path.isdir(model_dir):
            raise FileNotFoundError(f"Model directory not found: {model_dir}")

        for file in os.listdir(model_dir):
            if file.endswith(".onnx"):
                model_path = os.path.join(model_dir, file)

                session = ort.InferenceSession(
                    model_path,
                    providers=["CPUExecutionProvider"]
                )

                model_name = file.replace(".onnx", "")

                self.sessions[model_name] = session
                self.input_names[model_name] = session.get_inputs()[0].name
                self.output_names[model_name] = session.get_outputs()[0].name

                print(f"Loaded model: {model_name}")


    def predict(self, model_name, input_data):
        session = self.sessions[model_name]
        input_name = self.input_names[model_name]

        # Ensure correct format
        if not isinstance(input_data, np.ndarray):
            input_data = np.array(input_data, dtype=np.float32)

        outputs = session.run(
            None,
            {input_name: input_data}
        )
        # argmax
        prediction = np.argmax(outputs[0], axis=1)
        return prediction[0]


if __name__ == "__main__":
    model_service = ModelService()
    # Example usage:
    input_data = np.random.rand(1, 3, 100, 100).astype(np.float32)
    output = model_service.predict("card_castle_model", input_data)
    print("Prediction output:", output)