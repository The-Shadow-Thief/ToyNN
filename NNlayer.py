import random
import numpy as np
import os
import pickle

def sigmoid(Z):
    A = 1/(1+np.exp(-Z))
    return A

def relu(Z):
    A = np.maximum(0,Z)
    return A

def relu_backward(dA, Z):
    dZ = np.array(dA, copy=True)
    dZ[Z <= 0] = 0
    return dZ

def zero_pad(X, pad):
    X_pad = np.pad(X, ((0,0),(pad,pad),(pad,pad),(0,0)), 'constant', constant_values = (0,0))
    return X_pad

def conv_single_step(a_slice_prev, W, b):
    s = np.multiply(a_slice_prev,W)
    Z = np.sum(s)
    Z = float(Z+b)
    return Z

def sigmoid_backward(dA,Z):
    s = 1/(1+np.exp(-Z))
    dZ = dA * s * (1-s)
    return dZ

class NNlayer():
    def __init__(self,name):
        self.name =  name
    def set_params(self,params):
        pass
    def forward(self,X):
        return X
    def backward(self,dA):
        return dA
    def update_params(self,learning_rate):
        pass
    def params(self):
        return None
    def load_params(self,params):
        pass

class dens(NNlayer):
    def __init__(self,n_in,n_out,name):
        super(dens,self).__init__(name)
        self.W = np.random.randn(n_out,n_in)*0.01
        self.b = np.zeros((n_out,1))
    def load_params(self,params):
        self.W = params[0]
        self.b = params[1]
    def forward(self,X):
        self.A = X
        return np.dot(self.W,X)+self.b
    def backward(self,dZ):
        m = self.A.shape[1]
        self.dW = 1/m*np.dot(dZ,self.A.T)
        self.db = 1/m*np.sum(dZ,axis=1,keepdims=True)
        self.dA = np.dot(self.W.T,dZ)
        return self.dA
    def update_params(self,learning_rate):
        self.W = self.W - learning_rate * self.dW
        self.b = self.b - learning_rate * self.db
    def params(self):
        return [self.W,self.b]

class activate(NNlayer):
    def __init__(self,model,name):
        super(activate,self).__init__(name)
        self.model = model
    def forward(self,X):
        self.A = X
        if self.model == 'sigmoid':
            return sigmoid(X)
        elif self.model == 'relu':
            return relu(X)
    def backward(self,dA):
        if self.model == 'sigmoid':
            return sigmoid_backward(dA,self.A)
        elif self.model == 'relu':
            return relu_backward(dA,self.A)

class NetModel():
    def __init__(self):
        self.net=[]
    def add(self,n):
        self.net.append(n)
    def forward(self,X):
        a = X
        for n in self.net:
            a = n.forward(a)
        return a
    def backward(self,dA):
        a = dA
        for i in range(1,len(self.net)+1):
            a = self.net[-i].backward(a)
        return a
    def update_params(self,lr):
        for n in self.net:
            n.update_params(lr)
    def save_params(self,name):
        f = open(name,"wb")
        for n in self.net:
            if n.params() is not None:
                pickle.dump(n.params(),f)
        f.close()
    def load_params(self,name):
        f = open(name,"rb")
        for n in self.net:
            if n.params() is not None:
                params = pickle.load(f)
                n.load_params(params)
        f.close()

class Conv2D(NNlayer):
    def __init__(self,shape,num,pad,stride,name):
        super(Conv2D,self).__init__(name)
        W = np.random.random([shape[0],shape[1],shape[2],num])
        b = np.random.random([1,1,1,num])
        self.W = W
        self.b = b
        self.pad = pad
        self.stride = stride
    def forward(self,A):
        self.A = A
        return self.conv_forward(A,self.W,self.b,self.stride,self.pad)

    def backward(self,dZ):
        
        A_prev = self.A
        W = self.W
        b = self.b
        
        # Retrieve dimensions from A_prev's shape
        (m, n_H_prev, n_W_prev, n_C_prev) = A_prev.shape

        # Retrieve dimensions from W's shape
        (f, f, n_C_prev, n_C) = W.shape

        # Retrieve information from "hparameters"
        stride = self.stride
        pad = self.stride

        # Retrieve dimensions from dZ's shape
        (m, n_H, n_W, n_C) = dZ.shape

        # Initialize dA_prev, dW, db with the correct shapes
        dA_prev = np.ones((m,n_H_prev,n_W_prev,n_C_prev))                           
        dW = np.ones((f,f,n_C_prev,n_C))
        db = np.ones((1,1,1,n_C))

        # Pad A_prev and dA_prev
        A_prev_pad = zero_pad(A_prev, pad)
        dA_prev_pad = zero_pad(dA_prev,pad)

        for i in range(m):                       # loop over the training examples

            # select ith training example from A_prev_pad and dA_prev_pad
            a_prev_pad = A_prev_pad[i]
            da_prev_pad = dA_prev_pad[i]

            for h in range(n_H):                   # loop over vertical axis of the output volume
                for w in range(n_W):               # loop over horizontal axis of the output volume
                    for c in range(n_C):           # loop over the channels of the output volume

                        # Find the corners of the current "slice"
                        vert_start = stride*h
                        vert_end = vert_start+f
                        horiz_start = stride*w
                        horiz_end = horiz_start+f

                        # Use the corners to define the slice from a_prev_pad
                        a_slice = a_prev_pad[vert_start:vert_end,horiz_start:horiz_end,:]

                        # Update gradients for the window and the filter's parameters using the code formulas given above
                        da_prev_pad[vert_start:vert_end, horiz_start:horiz_end, :] +=  W[:,:,:,c] * dZ[i, h, w, c]
                        dW[:,:,:,c] += a_slice * dZ[i, h, w, c]
                        db[:,:,:,c] += dZ[i,h,w,c]

            # Set the ith training example's dA_prev to the unpaded da_prev_pad (Hint: use X[pad:-pad, pad:-pad, :])
            dA_prev[i, :, :, :] = da_prev_pad[pad:-pad,pad:-pad,:]
        ### END CODE HERE ###

        # Making sure your output shape is correct
        assert(dA_prev.shape == (m, n_H_prev, n_W_prev, n_C_prev))
        
        self.dA = dA_prev
        self.dW = dW
        self.db = db
        
        return self.dA 

    def conv_forward(self,A_prev, W, b, stride,pad):

        (m, n_H_prev, n_W_prev, n_C_prev) = A_prev.shape

        (f, f, n_C_prev, n_C) = W.shape

        n_H = int((n_H_prev - f + 2 * pad)/stride)+1
        n_W = int((n_W_prev - f + 2 * pad)/stride)+1

        Z = np.ones((m,n_H,n_W,n_C))

        A_prev_pad = zero_pad(A_prev, pad)

        for i in range(m):                               # loop over the batch of training examples
            a_prev_pad = A_prev_pad[i]                               # Select ith training example's padded activation
            for h in range(n_H):                           # loop over vertical axis of the output volume
                for w in range(n_W):                       # loop over horizontal axis of the output volume
                    for c in range(n_C):                   # loop over channels (= #filters) of the output volume

                        # Find the corners of the current "slice" (≈4 lines)
                        vert_start = stride*h
                        vert_end = vert_start + f
                        horiz_start = stride*w
                        horiz_end = horiz_start + f

                        # Use the corners to define the (3D) slice of a_prev_pad (See Hint above the cell). (≈1 line)
                        a_slice_prev = a_prev_pad[vert_start:vert_end,horiz_start:horiz_end,:]

                        # Convolve the (3D) slice with the correct filter W and bias b, to get back one output neuron. (≈1 line)
                        Z[i, h, w, c] = conv_single_step(a_slice_prev, W[:,:,:,c], b[:,:,:,c])

        ### END CODE HERE ###

        # Making sure your output shape is correct
        assert(Z.shape == (m, n_H, n_W, n_C))
        
        self.Z = Z
        return Z
    def update_params(self,learning_rate):
        self.W = self.W - learning_rate*self.dW
        self.b = self.b - learning_rate*self.db

class Pool(NNlayer):
    def __init__(self,stride,f,mode,name):
        super(Pool,self).__init__(name)
        self.stride = stride
        self.f = f
        self.mode = mode
    def forward(self,A):
        self.A = A
        return self.pool_forward(A,self.f,self.stride,self.mode)
    def pool_forward(self,A_prev, f,stride,mode):

        # Retrieve dimensions from the input shape
        (m, n_H_prev, n_W_prev, n_C_prev) = A_prev.shape

        # Define the dimensions of the output
        n_H = int(1 + (n_H_prev - f) / stride)
        n_W = int(1 + (n_W_prev - f) / stride)
        n_C = n_C_prev

        # Initialize output matrix A
        A = np.zeros((m, n_H, n_W, n_C))              

        ### START CODE HERE ###
        for i in range(m):                         # loop over the training examples
            for h in range(n_H):                     # loop on the vertical axis of the output volume
                for w in range(n_W):                 # loop on the horizontal axis of the output volume
                    for c in range (n_C):            # loop over the channels of the output volume

                        # Find the corners of the current "slice" (≈4 lines)
                        vert_start = stride*h
                        vert_end = vert_start+f
                        horiz_start = stride*w
                        horiz_end = horiz_start+f

                        # Use the corners to define the current slice on the ith training example of A_prev, channel c. (≈1 line)
                        a_prev_slice = A_prev[i][vert_start:vert_end,horiz_start:horiz_end,c]

                        # Compute the pooling operation on the slice. Use an if statment to differentiate the modes. Use np.max/np.mean.
                        if mode == "max":
                            A[i, h, w, c] = np.max(a_prev_slice)
                        elif mode == "average":
                            A[i, h, w, c] = np.mean(a_prev_slice)

        ### END CODE HERE ###

        # Making sure your output shape is correct
        assert(A.shape == (m, n_H, n_W, n_C))

        return A
    
    
    def distribute_value(self,dz, shape):
        (n_H, n_W) = shape
        average = dz/(n_H*n_W)
        a = np.ones((n_H,n_W))*average
        return a

    def pool_backward(self,dA, mode = "max"):

        A_prev = self.A
        stride = self.stride
        f = self.f

        # Retrieve dimensions from A_prev's shape and dA's shape (≈2 lines)
        m, n_H_prev, n_W_prev, n_C_prev = A_prev.shape
        m, n_H, n_W, n_C = dA.shape

        # Initialize dA_prev with zeros (≈1 line)
        dA_prev = np.zeros((m,n_H_prev,n_W_prev,n_C_prev))

        for i in range(m):                       # loop over the training examples

            # select training example from A_prev (≈1 line)
            a_prev = A_prev[i]

            for h in range(n_H):                   # loop on the vertical axis
                for w in range(n_W):               # loop on the horizontal axis
                    for c in range(n_C):           # loop over the channels (depth)

                        # Find the corners of the current "slice" (≈4 lines)
                        vert_start = h*stride
                        vert_end = vert_start+f
                        horiz_start = w*stride
                        horiz_end = horiz_start+f

                        # Compute the backward propagation in both modes.
                        if mode == "max":

                            # Use the corners and "c" to define the current slice from a_prev (≈1 line)
                            a_prev_slice = a_prev[vert_start: vert_end, horiz_start: horiz_end, c]
                            # Create the mask from a_prev_slice (≈1 line)
                            mask = create_mask_from_window(a_prev_slice)
                            # Set dA_prev to be dA_prev + (the mask multiplied by the correct entry of dA) (≈1 line)
                            dA_prev[i, vert_start: vert_end, horiz_start: horiz_end, c] += (dA[h,w,:,:] * mask)

                        elif mode == "average":

                            # Get the value a from dA (≈1 line)
                            da = dA[h,w,:,:]
                            # Define the shape of the filter as fxf (≈1 line)
                            shape = (f,f)
                            # Distribute it to get the correct slice of dA_prev. i.e. Add the distributed value of da. (≈1 line)
                            dA_prev[i, vert_start: vert_end, horiz_start: horiz_end, c] += distribute_value(da,shape)

        ### END CODE ###

        # Making sure your output shape is correct
        assert(dA_prev.shape == A_prev.shape)

        return dA_prev

class Flatten(NNlayer):
    def __init__(self,name):
        super(Flatten,self).__init__(name)
    def forward(self,X):
        self.shape = X.shape
        Z = np.reshape(X,[self.shape[0],-1])
        return Z.T
    def backward(self,dA):
        return np.reshape(dA,self.shape)