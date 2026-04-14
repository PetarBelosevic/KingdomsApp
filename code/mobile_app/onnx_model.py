"""
Inference of .onnx models for kivy android apps using native Java APIs.
Made by aicelen 2025 released under MIT license.
"""

from jnius import autoclass
import numpy as np
# from time import perf_counter

# Import Java classes
OrtSession = autoclass('ai.onnxruntime.OrtSession')
OrtSessionOptions = autoclass('ai.onnxruntime.OrtSession$SessionOptions')
OrtEnvironment = autoclass('ai.onnxruntime.OrtEnvironment')
OnnxTensor = autoclass('ai.onnxruntime.OnnxTensor')
ByteBuffer = autoclass('java.nio.ByteBuffer')
FloatBuffer = autoclass('java.nio.FloatBuffer')
HashMap = autoclass('java.util.HashMap')
OnnxJavaType = autoclass('ai.onnxruntime.OnnxJavaType')
Array = autoclass('java.util.Arrays')
ByteOrder = autoclass('java.nio.ByteOrder')

class OnnxModel:
    def __init__(
            self, 
            model_path: str, 
            num_threads: int = None, 
            use_nnapi: bool = False, 
            use_xnnpack: bool = False
        ):
        """
        Inference class of .onnx models for kivy apps on android using native Java APIs.

        Parameters
        ----------
        model_path: str
            Path to the .onnx model you want to run inference on.
        num_threads: int = None
            How many threads the model inference should use. Usually best performance 
            is achieved by using all big cores of the SOC. Defaults to 1.
        use_nnapi: bool = False
            Neural Networks API can provide significant speed ups although it is 
            often not compatible with the models and is not further developed.
        use_xnnpack: bool = False
            Should speed up inference time for some models.
        """
        self.env = OrtEnvironment.getEnvironment()
        so = OrtSessionOptions()

        if use_nnapi:
            so.addNnapi()

        if use_xnnpack:
            xnnpack_map = HashMap()
            xnnpack_map.put("intra_op_num_threads", str(num_threads or 2))
            so.addXnnpack(xnnpack_map)

        elif num_threads is not None:
            so.setIntraOpNumThreads(num_threads)
            so.setInterOpNumThreads(1)
       
        self.session = self.env.createSession(model_path, so)

        # !
        # Try to get output shapes, but handle different API versions gracefully
        self.output_shapes = {}
        try:
            output_info = self.session.getOutputInfo()
            for entry in output_info.entrySet():
                name = entry.getKey()
                info = entry.getValue()
                try:
                    # Try different ways to access shape depending on ONNX Runtime version
                    if hasattr(info, 'getInfo'):
                        tensor_info = info.getInfo()
                        if hasattr(tensor_info, 'getShape'):
                            shape = tensor_info.getShape()
                            self.output_shapes[name] = shape
                        elif hasattr(tensor_info, 'shape'):
                            self.output_shapes[name] = tensor_info.shape
                    elif hasattr(info, 'getShape'):
                        self.output_shapes[name] = info.getShape()
                    elif hasattr(info, 'shape'):
                        self.output_shapes[name] = info.shape
                except Exception as e:
                    print(f"Warning: Could not determine shape for output '{name}': {e}")
                    # Shape will be inferred from actual tensor output
                    self.output_shapes[name] = None
        except Exception as e:
            print(f"Warning: Could not get output info: {e}")
            # Shapes will be inferred from actual tensor outputs
        # !


    # def run(self, inputs: dict, outputs: dict) -> dict:
    def run(self, inputs: dict) -> dict:
        """
        Run inference on a given set of inputs.

        Parameters
        ----------
        inputs : dict
            Dictionary representing your input data with the format {your_input_name: np.array(your_data)}
        outputs: dict
            Dictionary for the output shape with the format {your_output_name: [shape]}

        Returns
        -------
        dict
            Outputs of the model
        """
        jmap = HashMap()
        for name, value in inputs.items():
            arr = np.ascontiguousarray(value)
            shape = list(arr.shape)

            if arr.dtype == np.float32:
                flat = arr.ravel()
                buffer_bytes = flat.tobytes()
                java_byte_buffer = ByteBuffer.wrap(buffer_bytes)
                java_byte_buffer.order(ByteOrder.nativeOrder())
                float_buffer = java_byte_buffer.asFloatBuffer()
                tensor = OnnxTensor.createTensor(self.env, float_buffer, shape)

            elif arr.dtype == np.int64:
                flat = arr.ravel().astype(np.int64)
                buffer_bytes = flat.tobytes()
                java_byte_buffer = ByteBuffer.wrap(buffer_bytes)
                java_byte_buffer.order(ByteOrder.nativeOrder())
                long_buffer = java_byte_buffer.asLongBuffer()
                tensor = OnnxTensor.createTensor(self.env, long_buffer, shape)

            else:
                raise TypeError(f"Unsupported dtype of input array: {arr.dtype}")
            jmap.put(name, tensor)

        # t0 = perf_counter()
        results = self.session.run(jmap)
        # print(f"Raw inference time: {perf_counter() - t0:.4f}s")

        output_dict = {}
        # !
        # Get output names from results object if output_shapes is empty
        output_names = list(self.output_shapes.keys()) if self.output_shapes else None
        
        if output_names is None:
            # Fallback: try to get names from results object
            try:
                # results might be a Java Map-like object
                output_names = list(results.keySet()) if hasattr(results, 'keySet') else []
            except:
                output_names = []
        
        if not output_names:
            # Last resort: assume single output named "output"
            output_names = ["output"]
        
        for out_name in output_names:
            try:
                tensor_obj = results.get(out_name).get()
            except Exception as e:
                print(f"Warning: Could not get output '{out_name}': {e}")
                continue
        # !
            bytebuffer = bytes(tensor_obj.getByteBuffer().array())
            numpy_array = np.frombuffer(bytebuffer, dtype=np.float32)

        # !
            shape = self.output_shapes.get(out_name) if self.output_shapes else None
            
            # If we have shape info, use it; otherwise infer from array data
            if shape is not None:
                # Handle dynamic dimensions (represented as -1)
                actual_shape = list(shape)
                if -1 in actual_shape:
                    # Replace -1 with calculated dimension
                    static_size = 1
                    dynamic_dims = 0
                    for dim in shape:
                        if dim == -1:
                            dynamic_dims += 1
                        else:
                            static_size *= dim
                    
                    if dynamic_dims == 1:
                        dynamic_size = numpy_array.size // static_size
                        actual_shape = [dynamic_size if d == -1 else d for d in actual_shape]
                
                output_dict[out_name] = numpy_array.reshape(*actual_shape)
            else:
                # No shape info, try to infer from array size
                # For classification models, typically output is (batch_size, num_classes)
                # Assume batch_size = 1 for now
                try:
                    if numpy_array.size > 1:
                        output_dict[out_name] = numpy_array.reshape(1, -1)
                    else:
                        output_dict[out_name] = numpy_array
                except Exception as e:
                    print(f"Warning: Could not reshape output '{out_name}': {e}")
                    output_dict[out_name] = numpy_array
            # !
            
            tensor_obj.close()

        results.close()
        return output_dict


    def close_session(self):
        """
        Frees up memory. Should be called when a model isn't used anymore
        """
        self.session.close()