"""Opt-in real MRtrix + Python backend smoke on tiny, generated data only."""

import json
import os
from pathlib import Path
import tempfile
import unittest

import nibabel as nib
import numpy as np
from scipy.spatial import ConvexHull

from safpy import SAFConfig, run_saf


@unittest.skipUnless(os.environ.get("SAF_PY_TEST_MRTRIX_BIN"), "Set SAF_PY_TEST_MRTRIX_BIN to enable real MRtrix smoke")
class MRtrixSmokeTest(unittest.TestCase):
    def test_full_backend_on_synthetic_surfaces_and_tracks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fs_dir = root / "surfaces"
            for name in ("surf", "label", "mri"):
                (fs_dir / name).mkdir(parents=True)
            rng = np.random.default_rng(17)
            directions = np.vstack([np.eye(3), -np.eye(3), rng.normal(size=(90, 3))])
            directions /= np.linalg.norm(directions, axis=1)[:, None]
            faces = ConvexHull(directions).simplices
            info = dict(head=np.array([2, 0, 20]), valid="1", filename="synthetic",
                        volume=np.array([16, 16, 16]), voxelsize=np.ones(3), xras=np.array([1., 0., 0.]),
                        yras=np.array([0., 1., 0.]), zras=np.array([0., 0., 1.]), cras=np.zeros(3))
            for hemi, offset in (("rh", np.zeros(3)), ("lh", np.array([10., 0., 0.]))):
                for kind, radius in (("white", 2.), ("pial", 3.), ("inflated", 3.)):
                    nib.freesurfer.write_geometry(str(fs_dir / "surf" / f"{hemi}.{kind}"),
                                                 radius * directions + offset, faces, volume_info=info)
                label = "#!ascii synthetic cortex\n96\n" + "".join(f"{i} 0 0 0 0\n" for i in range(96))
                (fs_dir / "label" / f"{hemi}.cortex.label").write_text(label)
            nib.save(nib.MGHImage(np.ones((16, 16, 16), dtype=np.float32), np.eye(4)), str(fs_dir / "mri/brain.mgz"))
            fod = root / "fod.nii.gz"
            nib.save(nib.Nifti1Image(np.zeros((4, 4, 4, 6), dtype=np.float32), np.eye(4)), str(fod))
            # Curved, asymmetric tracks avoid ambiguous exact edge/vertex hits.
            x = np.linspace(-2.45, 2.45, 49)
            track = np.column_stack([x, .11 * np.cos(x), .08 * np.sin(x)])
            tracks = [track, track + [10., 0., 0.]]
            tracks_path = root / "initial.tck"
            nib.streamlines.save(nib.streamlines.Tractogram(tracks, affine_to_rasmm=np.eye(4)), str(tracks_path))
            for fast in (True, False):
                with self.subTest(fast=fast):
                    output = root / ("fast" if fast else "complete")
                    result = run_saf(SAFConfig(subject_id="synthetic", input_root=root, fs_dir=fs_dir, fod_path=fod,
                                              output_dir=output, pregenerated_tractogram=tracks_path,
                                              mrtrix_bin_dir=Path(os.environ["SAF_PY_TEST_MRTRIX_BIN"]),
                                              fast_intersection=fast, maxlen=10., execute=True))
                    self.assertEqual(result.streamline_count, 2)
                    self.assertEqual(len(nib.streamlines.load(str(result.saf_tractogram)).streamlines), 2)
                    self.assertIn("vtk", result.saf_vtk_path.read_text()[:100].lower())
                    qc = json.loads(result.qc_path.read_text())
                    self.assertEqual(qc["status"], "completed")
                    self.assertEqual(qc["return_code"], 0)
                    self.assertTrue((output / "cache/surf_data/rh.t.t").is_file())
