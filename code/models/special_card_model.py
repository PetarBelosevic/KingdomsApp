from models.base.conv_feature_extraction import ConvFeatureExtraction
from models.base.linear_cls_head import LinearClsHead
from models.base.modular_model import ModularModel


class SpecialCardModel(ModularModel):
    """
    Implements a specific modular model architecture for distinguishing between special cards.
    It consists of a convolutional feature extraction module with two convolutional layers (12 and 24 output channels) 
    followed by a linear classification head with one hidden layer (48 output dimensions) and an output layer with 4 classes. 
    The model applies global average pooling to the output of the feature extraction module before passing it to the classification head.
    Model expects RGB input images (3 channels).
    """
    def __init__(self):
        feature_extraction_model = ConvFeatureExtraction(rgb=True, conv_modules=[32, 24])
        cls_head = LinearClsHead(num_classes=4, in_dim=24, linear_layers=[(48, 0.2)])
        super(SpecialCardModel, self).__init__(feature_extraction_model, cls_head)