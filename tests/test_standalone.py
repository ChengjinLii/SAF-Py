"""Standalone contracts; no real imaging data or external tools are required."""

import importlib
import json
import os
from pathlib import Path
import pkgutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import nibabel as nib
import numpy as np

from safpy import SAFConfig, run_saf
from safpy import saf as facade


def prepared_config(root, **kwargs):
    fs_dir = root / "surfaces"
    for name in ("mri/brain.mgz", "surf/lh.white", "surf/rh.white", "surf/lh.pial", "surf/rh.pial",
                 "surf/lh.inflated", "surf/rh.inflated", "label/lh.cortex.label", "label/rh.cortex.label"):
        path = fs_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic validation placeholder", encoding="utf-8")
    fod = root / "fod.nii.gz"
    fod.write_text("placeholder", encoding="utf-8")
    values = dict(subject_id="demo", input_root=root, fs_dir=fs_dir, fod_path=fod, output_dir=root / "output")
    values.update(kwargs)
    return SAFConfig(**values)


class StandaloneTest(unittest.TestCase):
    def test_all_backend_modules_import_without_host_paths(self):
        import safpy.saf_backend as backend

        before = list(sys.path)
        for info in pkgutil.walk_packages(backend.__path__, backend.__name__ + "."):
            importlib.import_module(info.name)
        self.assertEqual(sys.path, before)
        self.assertFalse(any(name == "shared" or name.startswith("shared.") for name in sys.modules))

    def test_surface_inputs_are_required_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            config = prepared_config(Path(directory))
            (config.fs_dir / "label/lh.cortex.label").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "cortex.label"):
                run_saf(config)
            self.assertFalse(config.output_dir.exists())

    def test_nonfinite_length_and_unsafe_label_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for values in ({"maxlen": float("nan")}, {"maxlen": float("inf")}, {"subject_id": "../escape"}):
                with self.subTest(values=values):
                    with self.assertRaises(ValueError):
                        run_saf(prepared_config(Path(directory), **values))

    def test_generation_and_input_tracks_are_mutually_exclusive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tracks = root / "input.tck"
            tracks.touch()
            config = prepared_config(root, pregenerated_tractogram=tracks, tckgen_options="-select 10")
            with self.assertRaisesRegex(ValueError, "mutually exclusive"):
                run_saf(config)

    def test_no_length_limit_is_forwarded_as_none(self):
        with tempfile.TemporaryDirectory() as directory:
            config = prepared_config(Path(directory), maxlen=None, surface_seeding=True)
            args = facade._build_saf_args(config, config.output_dir)
            self.assertIsNone(args[args.index("maxlen") + 1])
            self.assertIn("surfseed", args)

    def test_seed_and_working_directory_restore_on_backend_error(self):
        with tempfile.TemporaryDirectory() as directory:
            config = prepared_config(Path(directory), random_seed=424242, execute=True)
            before = Path.cwd()

            def backend(args):
                self.assertEqual(os.environ["MRTRIX_RNG_SEED"], "424242")
                os.chdir(config.output_dir)
                raise ValueError("synthetic backend failure")

            with mock.patch.dict(os.environ, {"MRTRIX_RNG_SEED": "previous"}), \
                 mock.patch.object(facade, "inspect_saf_backend", return_value={"available": True}), \
                 mock.patch.object(facade, "_execute_backend", side_effect=backend):
                with self.assertRaisesRegex(RuntimeError, "synthetic backend failure"):
                    run_saf(config)
                self.assertEqual(os.environ["MRTRIX_RNG_SEED"], "previous")
            self.assertEqual(Path.cwd(), before)
            for name in ("saf_manifest.json", "saf_qc.json"):
                record = json.loads((config.output_dir / name).read_text())
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["return_code"], 1)

    def test_sys_exec_receives_seed(self):
        from safpy.saf_backend.Support.sys_exec import sys_exec

        with mock.patch.dict(os.environ, {"MRTRIX_RNG_SEED": "424242"}), \
             mock.patch("safpy.saf_backend.Support.sys_exec.subprocess.run") as run:
            sys_exec("seed-probe", SimpleNamespace(dgn=False))
        self.assertEqual(run.call_args.kwargs["env"]["MRTRIX_RNG_SEED"], "424242")

    def test_decoded_qc_and_failure_return_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = prepared_config(root, maxlen=4.0, execute=True)

            def backend(args):
                tractogram = nib.streamlines.Tractogram([np.array([[0., 0., 0.], [5., 0., 0.]])], affine_to_rasmm=np.eye(4))
                nib.streamlines.save(tractogram, str(config.output_dir / "SAF.tck"))

            def export(source, destination, **kwargs):
                destination.write_text("mock VTK output")
                return True, None

            with mock.patch.object(facade, "inspect_saf_backend", return_value={"available": True}), \
                 mock.patch.object(facade, "_execute_backend", side_effect=backend), \
                 mock.patch.object(facade, "_count_tck_streamlines", return_value=(1, None)), \
                 mock.patch.object(facade, "_export_tck_to_vtk", side_effect=export):
                with self.assertRaisesRegex(RuntimeError, "longer than"):
                    run_saf(config)
            qc = json.loads((config.output_dir / "saf_qc.json").read_text())
            self.assertEqual(qc["return_code"], 1)
            self.assertEqual(qc["scientific_output_summary"]["streamline_count"], 1)
            self.assertEqual(qc["scientific_output_summary"]["length_mm"]["max"], 5.)

    def test_cli_help_and_dry_run(self):
        result = subprocess.run([sys.executable, "-m", "safpy", "--help"], check=True, text=True, capture_output=True)
        self.assertIn("--surface-seeding", result.stdout)
        with tempfile.TemporaryDirectory() as directory:
            config = prepared_config(Path(directory))
            result = subprocess.run([sys.executable, "-m", "safpy", "--subject", "demo", "--fs-dir", str(config.fs_dir),
                                     "--fod", str(config.fod_path), "--output", str(config.output_dir)], check=True, text=True, capture_output=True)
            self.assertEqual(json.loads(result.stdout)["status"], "planned")
            self.assertFalse((config.output_dir / "SAF.tck").exists())
