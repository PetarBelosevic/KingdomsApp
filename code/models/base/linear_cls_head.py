from torch import nn


class LinearClsHead(nn.Module):
    """
    Implements a linear classification head consisting of a sequence of fully connected layers. 
    The architecture can be customized by specifying the number of output dimensions for each linear layer.
    ReLU activation is applied after each linear layer except the final classification layer.
    
    :param num_classes: The number of output classes for classification. Default is 2.
    :param in_dim: The input dimension to the first linear layer. Default is 64.
    :param linear_layers: A list of parameters for each linear layer. 
        Each element can be either an integer (number of output dimensions) or a tuple (out_dim, dropout).
        If an integer is provided, it is interpreted as the number of output dimensions with no dropout. 
        If a tuple is provided, it specifies the number of output dimensions and the dropout rate for that layer after the activation function.
    """
    def __init__(self, num_classes:int=2, in_dim:int=64, linear_layers:list[int|tuple[int,float]]=[128]):
        super(LinearClsHead, self).__init__()
        self.linear_head = nn.Sequential()
        last_dim = in_dim
        for param in linear_layers:
            use_dropout = False
            if isinstance(param, tuple):
                out_dim, dropout = param
                use_dropout = True
            else:
                out_dim = param
            self.linear_head.append(nn.Linear(last_dim, out_dim))
            self.linear_head.append(nn.ReLU())
            if use_dropout:
                self.linear_head.append(nn.Dropout(dropout))
            last_dim = out_dim
        self.linear_head.append(nn.Linear(last_dim, num_classes))
        self.in_dim = in_dim
        self.out_dim = num_classes

    
    def forward(self, x):
        x = self.linear_head(x)
        return x