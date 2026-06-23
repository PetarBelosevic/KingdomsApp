from torch import nn

from models.base.conv_feature_extraction import ConvFeatureExtraction
from models.base.linear_cls_head import LinearClsHead


class ModularModel(nn.Module):
    """
    Implements a modular model architecture for image classification, consisting of a convolutional feature extraction module (ConvFeatureExtraction) followed by a linear classification head (LinearClsHead).
    The model applies global average pooling to the output of the feature extraction module before passing it to the classification head. 
    The architecture can be customized by providing different configurations for the feature extraction and classification head modules.

    :param feature_extraction: An instance of ConvFeatureExtraction that defines the convolutional feature extraction part of the model.
    :param cls_head: An instance of LinearClsHead that defines the linear classification head of the model. 
        The input dimension of the classification head must match the output channels of the feature extraction module.
    """
    def __init__(self, feature_extraction:ConvFeatureExtraction, cls_head:LinearClsHead):
        super(ModularModel, self).__init__()
        assert feature_extraction.out_channels == cls_head.in_dim, "Output channels of feature extraction must match input dimension of classification head!"
        self.feature_extraction = feature_extraction
        self.cls_head = cls_head
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))


    def forward(self, x):
        x = self.feature_extraction(x)
        x = self.global_pool(x)
        x = x.view(-1, self.cls_head.in_dim)
        x = self.cls_head(x)
        return x