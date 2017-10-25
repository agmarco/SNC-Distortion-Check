import math
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
# - The `grid_spacing` is the spacing between grid-intersections (for all current
# phantoms it is the same along each dimension).
# - The `keras_model` is the CNN model used to reject FPs.  Each phantom model
# has its own CNN.
# - The `brute_search_slices` is a series of 6 slices outlining which phantom
# orientations should be searched.  Some phantoms can be oriented in multiple
# ways, and this parameter allows us to indicate the minimal number of
# variations that we need to search through during our registration algorithm.

deg = math.radians(1)

paramaters = {
    '603A': {
        'points_file': 'data/points/603A.mat',
        'grid_radius': 1.5,
        'grid_spacing': 15,
        'keras_model': 'data/keras_models/603/weights.h5',
        'brute_search_slices': [
            slice(-12, 12, 5j),
            slice(-12, 12, 5j),
            slice(-12, 12, 5j),
            slice(-2*deg, 2*deg, 3j),
            slice(-2*deg, 2*deg, 3j),
            slice(-2*deg, 2*deg, 3j),
        ],
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
        'grid_spacing': 20,
        'brute_search_slices': [
            slice(0, 0, 1j),
            slice(0, 0, 1j),
            slice(0, 0, 1j),
            slice(0, 0, 1j),
            slice(0, 0, 1j),
            slice(0, 0, 1j),
        ],
        'keras_model': 'data/keras_models/604/weights.h5',
        'description': "The phantom is comprised of a leak-proof PMMA cylinder and measures 330 mm in diameter by 300 "
            "mm long. The entire volume is filled with a unique orthogonal 3D grid of 3 mm diameter rods spaced 20 mm "
            "apart to provide complete geometric data throughout the imaging volume.  The phantom is marked for ease of "
            "alignment to positioning lasers and is designed for use with both curved and flat gantry tables.",
    },
}
