from models.base.conv_feature_extraction import ConvFeatureExtraction
from models.base.linear_cls_head import LinearClsHead
from models.base.modular_model import ModularModel


class CardCastleModel(ModularModel):
    """
    Implements a specific modular model architecture for distingishing between cards, castles and empty cells.
    It consists of a convolutional feature extraction module with three convolutional layers (12, 24, and 36 output channels)
    followed by a linear classification head with one hidden layer (48 output dimensions) and an output layer with 3 classes.
    The model applies global average pooling to the output of the feature extraction module before passing it to the classification head.
    
    :param rgb: Whether the input images are RGB (3 channels) or grayscale (1 channel). Default is True (RGB).
    """
    def __init__(self, rgb:bool=True):
        feature_extraction_model = ConvFeatureExtraction(rgb=rgb, conv_modules=[12, 24, 36])
        cls_head = LinearClsHead(num_classes=3, in_dim=36, linear_layers=[(48, 0.1)])
        super(CardCastleModel, self).__init__(feature_extraction_model, cls_head)