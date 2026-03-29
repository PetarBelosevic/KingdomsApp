from torch import nn

from models.base.conv_module import ConvModule


class ConvFeatureExtraction(nn.Module):
    """
    Implements a convolutional feature extraction module for image data, consisting of a sequence of convolutional modules (ConvModule). 
    The architecture can be customized by specifying the number of output channels for each convolutional layer.
    
    :param rgb: Whether the input images are RGB (3 channels) or grayscale (1 channel). Default is True (RGB).
    :param conv_modules: A list of parameters for each convolutional module. 
        Each element can be either an integer (number of output channels) or a tuple (out_channels, kernel_size, use_max_pool).
        If an integer is provided, it is interpreted as the number of output channels with a kernel size of 3 and max pooling enabled. 
        If a tuple is provided, it specifies the number of output channels, kernel size, and whether to use max pooling for that module.
    """
    def __init__(self, rgb:bool=True, conv_modules:list[int|tuple[int,int,bool]]=[16,32,64]):
        super(ConvFeatureExtraction, self).__init__()
        self.conv_modules = nn.Sequential()
        in_channels = 3 if rgb else 1
        self.in_channels = in_channels
        for param in conv_modules:
            if isinstance(param, tuple):
                out_channels, kernel_size, use_max_pool = param
            else:
                out_channels = param
                kernel_size = 3
                use_max_pool = True
            self.conv_modules.append(ConvModule(in_channels, out_channels, kernel_size=kernel_size, use_max_pool=use_max_pool))
            in_channels = out_channels
        self.out_channels = in_channels

    
    def forward(self, x):
        x = self.conv_modules(x)
        return x