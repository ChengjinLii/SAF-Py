"""Explicit plan/execute command line for native-dMRI SAF inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .saf import SAFConfig, inspect_saf_backend, run_saf


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--version", action="version", version=__version__)
    p.add_argument("--check", action="store_true", help="Inspect Python and base MRtrix dependencies; no files written")
    p.add_argument("--subject", default="subject", help="Run label, not an imaging-data lookup")
    p.add_argument("--input-root", type=Path, default=Path("."), help="Default output parent; raw DWI is not read here")
    p.add_argument("--fs-dir", type=Path, help="Prepared native-dMRI FreeSurfer-format directory")
    p.add_argument("--fod", type=Path, help="MRtrix-compatible FOD in matching native-dMRI physical space")
    p.add_argument("--output", type=Path, help="Dedicated output directory")
    p.add_argument("--tracks", type=Path, help="Pregenerated .tck instead of tckgen")
    p.add_argument("--weights", type=Path, help="Weights in original input tractogram order")
    p.add_argument("--fa", type=Path)
    p.add_argument("--scalar", type=Path, action="append", default=[])
    p.add_argument("--mrtrix-bin", type=Path, help="MRtrix executables; alternatively set MRTRIX_BIN or PATH")
    p.add_argument("--tckgen-options", default="", help="Trusted shell option string; use --tckgen-options='...' for leading dashes")
    p.add_argument("--surface-seeding", action="store_true", help="Pass the white-surface vertices to tckgen as global seeds")
    p.add_argument("--maxlen", type=float, default=90.0, help="Maximum initial/final length in mm; default 90")
    p.add_argument("--no-length-limit", action="store_true")
    p.add_argument("--random-seed", type=int, default=12345)
    p.add_argument("--complete-intersection", action="store_true")
    p.add_argument("--gwg-hard", action="store_true")
    p.add_argument("--pialfilter", action="store_true")
    p.add_argument("--notrunc", action="store_true")
    p.add_argument("--remesh-seeds", type=float, metavar="MM", help="Maximum seed-mesh edge length")
    p.add_argument("--force", action="store_true", help="Recompute in an existing dedicated output directory")
    p.add_argument("--diagnostics", action="store_true", help="Keep diagnostic products in the output root")
    p.add_argument("--execute", action="store_true", help="Run the backend; otherwise write a plan only")
    return p


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    if args.check:
        status = inspect_saf_backend(mrtrix_bin_dir=args.mrtrix_bin)
        print(json.dumps(status, indent=2))
        return 0 if status["available"] else 1
    if args.fs_dir is None or args.fod is None:
        p.error("--fs-dir and --fod are required unless --check is used")
    config = SAFConfig(
        subject_id=args.subject, input_root=args.input_root,
        fs_dir=args.fs_dir, fod_path=args.fod, output_dir=args.output,
        pregenerated_tractogram=args.tracks, streamline_weights=args.weights,
        fa_path=args.fa, scalar2surf=tuple(args.scalar), mrtrix_bin_dir=args.mrtrix_bin,
        tckgen_options=args.tckgen_options, surface_seeding=args.surface_seeding,
        maxlen=None if args.no_length_limit else args.maxlen,
        random_seed=args.random_seed, fast_intersection=not args.complete_intersection,
        gwg_hard=args.gwg_hard, pialfilter=args.pialfilter, notrunc=args.notrunc,
        remesh_seeds=args.remesh_seeds or False,
        force_recompute=args.force, diagnostics=args.diagnostics, execute=args.execute,
    )
    try:
        result = run_saf(config, log=lambda message: print(message, file=sys.stderr))
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"saf-py: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"status": "completed" if result.executed else "planned",
                      "output_dir": str(result.output_dir), "manifest": str(result.manifest_path),
                      "qc": str(result.qc_path), "streamline_count": result.streamline_count}, indent=2))
    return 0
