"""Small analytic fixture extracted from the source Python acceptance tests.

No reference MATLAB source or real-subject data is bundled.
"""

import numpy as np


def fixture() -> dict:
    rng = np.random.default_rng(20261013)
    triangles = rng.normal(size=(1200, 3, 3))
    tetra = np.array([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]])
    faces = np.array([[1, 2, 3], [0, 1, 3], [0, 2, 1], [0, 3, 2]])
    vertices = np.vstack([tetra, tetra + [2., 0., 0.]])
    faces = np.vstack([faces, faces + 4])
    # Different y/z values force distinct nearest vertices at both ends.
    x = np.array([-.5, -.1, .1, .25, .4, .55, .7, .9, 1.2, 1.8, 1.9, 2.1, 2.25, 2.4, 2.55, 2.7, 2.9, 3.2])
    tracks = np.empty((1, 3), dtype=object)
    tracks[0, 0] = np.column_stack([x, np.full_like(x, .1), np.full_like(x, .1)])
    tracks[0, 1] = np.column_stack([x, np.full_like(x, .1), np.full_like(x, .6)])
    tracks[0, 2] = np.column_stack([x, np.full_like(x, .6), np.full_like(x, .1)])
    return {
        'P1': triangles[:, 0], 'P2': triangles[:, 1], 'P3': triangles[:, 2],
        'Q1': rng.normal(size=(1200, 3)), 'Q2': rng.normal(size=(1200, 3)),
        'triangle_vertices': np.arange(3600).reshape(1200, 3) + 1,
        'face_ids': np.arange(1200)[:, None] + 1,
        'segment_ids': (2 * np.arange(1200))[:, None] + 1,
        'vertices': vertices, 'faces': faces + 1, 'tracks': tracks,
        'inside': False, 'outer_intersection': False,
    }
