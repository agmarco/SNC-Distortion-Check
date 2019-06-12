import math

import numpy as np

# TODO: Deduplicate this data

# Some of the information in this file is duplicated in
#
#   server.common.models.PhantomModel
#
# We should probably only have one source of truth, and probably it should be
# the database.  We will likely include Keras models for each phantom model,
# and these model files are too large to store directly in the repository
# long-term; hence, long term we probably want to keep phantom models in the
# database.
#
# - The `grid_radius` is the radius of the intersecting cylinders.
# - The `grid_spacing` is the spacing between grid-intersections.
# - The `keras_model` is the CNN model used to reject FPs.  Each phantom model
# has its own CNN.

deg = math.radians(1)

paramaters = {
    '603A': {
        'points_file': 'data/points/603A.mat',
        'grid_radius': 1.5,
        'grid_spacing': np.array([15, 15, 15]),
        'keras_model': 'data/keras_models/603/weights.h5',
        'description': "The skull is manufactured from a plastic-based bone substitute, and the interstitial and "
                       "surrounding soft tissues are made from a proprietary signal generating water-based polymer. The entire "
                       "phantom is encased in a clear plastic shell to protect gel from desiccation. The phantom is supplied with "
                       "specially designed pads that allow fixation with any stereotactic frame or mounting for end-to-end testing. "
                       "The phantom is also suitable for frameless SRS QA."
                       "\n"
                       "The entire inter-cranial portion of the skull volume is filled with an orthogonal 3D grid of 3mm diameter "
                       "rods spaced 15 mm apart. Five extended axis-rods intersect at the reference origin of the grid. The end of "
                       "each extended axis is fitted with CT/MR markers allowing for accurate positioning with lasers and "
                       "co-registration of CT and MR image sets."
                       "\n" 
                       "The phantom includes right and left air voids, 3 mm in diameter by 17 mm long to simulate each ear canal for "
                       "evaluation of potential distortions commonly found in clinical settings.",
    },
    '604': {
        'points_file': 'data/points/604.mat',
        'grid_radius': 1.5,
        'grid_spacing': np.array([20, 20, 20]),
        'keras_model': 'data/keras_models/604/weights.h5',
        'description': "The phantom is comprised of a leak-proof PMMA cylinder and measures 330 mm in diameter by 300 "
            "mm long. The entire volume is filled with a unique orthogonal 3D grid of 3 mm diameter rods spaced 20 mm "
            "apart to provide complete geometric data throughout the imaging volume.  The phantom is marked for ease of "
            "alignment to positioning lasers and is designed for use with both curved and flat gantry tables.",
    },
    '604-GS': {
        'points_file': 'data/points/604-GS.mat',
        'grid_radius': 1.5,
        'grid_spacing': np.array([21.5, 20.5, 20.3]),
        'keras_model': 'data/keras_models/604/weights.h5',  # TODO: retrain CNN
        'description': "",
    },
}
