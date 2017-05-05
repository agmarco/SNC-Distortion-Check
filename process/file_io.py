'''
Wrappers for file IO.

Includes some validation.
'''
import scipy.io

import process.phantoms


def load_variable(path, variable_name):
    data = scipy.io.loadmat(path)
    try:
        return data[variable_name]
    except KeyError as e:
        variables = "\n- ".join(data)
        print("Invalid variable. Variables present:\n- {}".format(variables))
        raise e


def load_voxels(path):
    data = scipy.io.loadmat(path)

    # the `savemat` automatically places strings into an array, so we need to
    # unpack it here
    data['phantom_model'] = data['phantom_model'][0]
    data['modality'] = data['modality'][0]

    return data


def save_voxels(path, data):
    phantom_model = data['phantom_model']
    valid_phantom_models = list(process.phantoms.paramaters.keys())
    if phantom_model not in valid_phantom_models:
        msg = 'Invalid phantom name "{}". Must be one of:\n- {}'
        raise ValueError(msg.format(phantom_model, '\n- '.join(valid_phantom_models)))

    modality = data['modality']
    valid_modalities = ['ct', 'mri']
    if modality not in valid_modalities:
        msg = 'Invalid modality "{}". Must be one of:\n- {}'
        raise ValueError(msg.format(modality, '\n- '.join(valid_modalities)))

    scipy.io.savemat(path, data)


def load_points(path):
    data = scipy.io.loadmat(path)
    return data


def save_points(path, data):
    scipy.io.savemat(path, data)


def load_m_s(path):
    data = scipy.io.loadmat(path)
    return data


def save_m_s(path, data):
    scipy.io.savemat(path, data)


def load_distortion(path):
    data = scipy.io.loadmat(path)
    return data


def save_distortion(path, data):
    scipy.io.savemat(path, data, do_compression=True)
