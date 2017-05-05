# TODO: Deduplicate this data

# Some of the information in this file is duplicated in
#
#   server.common.models.PhantmoModel
#
# We should probably only have one source of truth, and probably it should be
# the database.  We will likely include Keras models for each phantom model,
# and these model files are too large to store directly in the repository
# long-term; hence, long term we probably want to keep phantom models in the
# database.

paramaters = {
    '603A': {
        'points_file': 'data/points/603A.mat',
        'grid_radius': 1.5,
        'grid_spacing': 15,
        'keras_model': 'data/keras_models/model.h5',
    },
    '604': {
        'points_file': 'TBD',
        'grid_radius': 1.5,
        'grid_spacing': 20,
        # TODO: add a model for the 604 phantom
    },
    '1540': {
        'points_file': 'data/points/1540.mat',
        'grid_radius': 1.5,
        'grid_spacing': 15,
    }
}
