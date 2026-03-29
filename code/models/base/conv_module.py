from torch import nn


class ConvModule(nn.Module):
    """
    Implements a convolutional module consisting of a convolutional layer followed by batch normalization, ReLU activation, and max pooling.
    The convolutional layer uses padding to maintain the spatial dimensions of the input. 
    The max pooling layer reduces the spatial dimensions by a factor of 2.
    
    :param in_channels: The number of input channels for the convolutional layer.
    :param out_channels: The number of output channels for the convolutional layer.
    :param kernel_size: The size of the convolutional kernel. Default is 3.
    :param use_max_pool: Whether to use max pooling after the convolutional layer. Default is True.
    """
    def __init__(self, in_channels:int, out_channels:int, kernel_size:int=3, use_max_pool:bool=True):
        super(ConvModule, self).__init__()
        self.module = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=kernel_size//2),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(),
            nn.MaxPool2d(2, 2) if use_max_pool else nn.Identity()
        )


    def forward(self, x):
        x = self.module(x)
        return x