""" this module is used as a template for generating sub class of Network
"""


class MyNet(object):
    ### automatically generated by caffe2fluid ###
    inputs_info = "INPUTS_INFO"
    custom_layers_path = "_CAFFE2FLUID_CUSTOM_LAYERS_"

    def custom_layer_factory(self):
        import os

        pk_paths = []
        default = os.path.dirname(os.path.abspath(__file__))
        location = os.environ.get('CAFFE2FLUID_CUSTOM_LAYERS', default)
        pk_name = 'custom_layers'
        pk_dir = os.path.join(location, pk_name)
        pk_paths.append((location, pk_dir))

        location = MyNet.custom_layers_path
        pk_dir = os.path.join(MyNet.custom_layers_path, pk_name)
        pk_paths.append((location, pk_dir))

        for loc, pk_dir in pk_paths:
            if os.path.exists(pk_dir):
                if loc not in sys.path:
                    sys.path.insert(0, loc)
                    break

        try:
            from custom_layers import make_custom_layer
            return make_custom_layer
        except Exception as e:
            print('maybe you should set $CAFFE2FLUID_CUSTOM_LAYERS first')
            raise e

    @classmethod
    def input_shapes(cls):
        return cls.inputs_info

    @classmethod
    def convert(cls, npy_model, fluid_path, outputs=None):
        fluid = import_fluid()
        shapes = cls.input_shapes()
        input_name = list(shapes.keys())[0]
        feed_data = {}
        for name, shape in shapes.items():
            data_layer = fluid.layers.data(
                name=name, shape=shape, dtype="float32")
            feed_data[name] = data_layer

        net = cls(feed_data)
        place = fluid.CPUPlace()
        exe = fluid.Executor(place)
        exe.run(fluid.default_startup_program())
        net.load(data_path=npy_model, exe=exe, place=place)
        output_vars = []

        model_filename = 'model'
        params_filename = 'params'
        if outputs is None:
            output_vars.append(net.get_output())
        else:
            if outputs[0] == 'dump_all':
                model_filename = None
                params_filename = None
                output_vars.append(net.get_output())
            else:
                if type(outputs) is list:
                    for n in outputs:
                        assert n in net.layers, 'not found layer with this name[%s]' % (
                            n)
                        output_vars.append(net.layers[n])

        fluid.io.save_inference_model(
            fluid_path, [input_name],
            output_vars,
            exe,
            main_program=None,
            model_filename=model_filename,
            params_filename=params_filename)
        return 0


def main():
    """ a tool used to convert caffe model to fluid
    """

    import sys
    import os
    import argparse
    filename = os.path.splitext(os.path.basename(sys.argv[0]))[0]    
    parser = argparse.ArgumentParser()
    parser.add_argument('--npy_path', help='Model\'s parameters  (.npy) path')
    parser.add_argument('--model-param-path', help='The path of model and param which are convertd by .npy',
                       default='./fluid')
    parser.add_argument(
        '--need-layers-name', help='The layers need to save (split by ,)')
    args = parser.parse_args()
    npy_weight = args.npy_path
    fluid_model = args.model_param_path
    outputs = None
    if args.need_layers_name:
        outputs = args.need_layers_name.split(',')

    ret = MyNet.convert(npy_weight, fluid_model, outputs)
    if ret == 0:
        outputs = 'last output layer' if outputs is None else outputs
        print('succeed to convert to fluid format with output layers[%s]'
              ' in directory[%s]' % (outputs, fluid_model))
    else:
        print('failed to convert model to fluid format')

    return ret


def generate_net_code(net_name, inputs_info):
    """ generate framework of a custom net code which represent a subclass of Network

    Args:
        @net_name (str): class name for this net
        @inputs_info (str): a str which represents a dict,  eg: '{"data": [3, 32, 32]}'
    Returns:
        net_codes (str): codes for this subclass
    """
    import os
    import inspect

    net_codes = str(inspect.getsource(MyNet))
    net_codes = net_codes.replace('MyNet(object)', '%s(Network)' % net_name)
    net_codes = net_codes.replace('MyNet', net_name)
    net_codes = net_codes.replace('"INPUTS_INFO"', inputs_info)

    custom_layer_dir = os.path.dirname(os.path.abspath(__file__))
    net_codes = net_codes.replace('_CAFFE2FLUID_CUSTOM_LAYERS_',
                                  custom_layer_dir)
    return net_codes


def generate_main_code(net_name):
    """ generate a piece of code for 'main' function

    Args:
        @net_name (str): class name for this net

    Returns:
        main_codes (str): codes for this main function
    """
    import inspect

    main_codes = str(inspect.getsource(main))
    main_codes = main_codes.replace('MyNet', net_name)
    return main_codes


if __name__ == "__main__":
    """ just for testing
    """
    print(generate_net_code('Attribute', "{'data': [3, 277, 277]}"))
    print(generate_main_code('Attribute'))
