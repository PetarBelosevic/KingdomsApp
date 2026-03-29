from models.base.conv_feature_extraction import ConvFeatureExtraction
from models.base.linear_cls_head import LinearClsHead
from models.base.modular_model import ModularModel


class CastleRankModel(ModularModel):
    """
    Implements a specific modular model architecture for distinguishing between castle ranks (1-4).
    It consists of a convolutional feature extraction module with seven convolutional layers (48, 48, 48, 48, 48, 48, and 48 output channels) 
    followed by a linear classification head with one hidden layer (64 output dimensions) and an output layer with 4 classes. 
    The model applies global average pooling to the output of the feature extraction module before passing it to the classification head.
    Model expects RGB input images (3 channels).
    """
    def __init__(self):
        feature_extraction_model = ConvFeatureExtraction(rgb=True, conv_modules=[(80, 7, False), (80, 5, True), (72, 3, False), (72, 3, True), (72, 3, False), (72, 3, True), (72, 3, False)])
        cls_head = LinearClsHead(num_classes=4, in_dim=72, linear_layers=[(64, 0.4)])
        super(CastleRankModel, self).__init__(feature_extraction_model, cls_head)

    
    # def __init__(self):
        # feature_extraction_model = ConvFeatureExtraction(rgb=True, conv_modules=[(48, 5, False), (48, 5, True), (48, 3, False), (48, 3, True), (32, 3, False), (32, 3, True), (32, 3, False), (32, 3, True)])
        # cls_head = LinearClsHead(num_classes=4, in_dim=32, linear_layers=[(64, 0.35)])
        # super(CastleRankModel, self).__init__(feature_extraction_model, cls_head)

# next: 80, 80, 72, 72, 72, 72, 72; 64 in hidden layer; epochs: 100; augments_per_image: 40; lr: 0.0001; weight_decay: 0.0001