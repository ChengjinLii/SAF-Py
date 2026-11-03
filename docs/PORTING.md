# Porting Notes

## Provenance

The original method and MATLAB implementation are Shastin et al.'s SAF:
https://github.com/dmitrishastin/SAF, baseline commit
`7e2a9d152caf1cf3e6bface64e7e176faac0c14f`.
Original paper: https://doi.org/10.1016/j.neuroimage.2022.119423.
MIT terms and original copyright are retained verbatim.

This release extracts the existing Python SAF translation and facade from the
SlicerDSpace software component at revision
`57b044f54411b84230564fdcef18c469742569c7`. The inherited scientific identity is
`python-native-20261013`; it is not a claim that MATLAB-to-Python translation
or the standalone package constitutes a new SAF algorithm.
The source-file hashes before packaging are recorded in
[source-inventory.json](source-inventory.json).

## Package-Only Changes

- Keep `Class_files`, `Data_modules`, `Filters`, `Pipe_modules`, `Support` and
  `SAF_pipeline.py` in their original relative layout under `safpy.saf_backend`.
- Replace absolute legacy backend imports with package-relative imports.
  No `sys.path` injection, global `Filters`/`Support` packages, parent checkout,
  or `shared` dependency is needed.
- Replace `shared.external_process` with a small standard-library environment,
  executable-discovery and text-decoding adapter. Retain the backend's command
  construction, failure propagation and seed forwarding.
- Remove the host cohort scheduler and subject-discovery requirement. The
  facade uses explicit paths; `input_root` only organizes default output as
  `<input_root>/<subject_id>/SAF_output` (or `<input_root>/SAF_output` when the
  root is already named for the subject).
- Provide `saf-py` / `python -m safpy`, installation metadata, local tests and
  bilingual documentation. The CLI plans by default. No GitHub Actions workflows
  are added or used.
- Expose the existing `surfseed` backend option as `surface_seeding` /
  `--surface-seeding`, off by default as in the inherited parser.
- Validate required prepared inputs, FA, finite positive limits, a safe run
  label, and incompatible generation/pregenerated settings before output work.
- Represent disabled `maxlen` as `None` rather than an empty string to avoid
  numeric/string comparisons in the inherited generation route.
- Preflight `tckstats` and `tckconvert` because final count/QC/VTK export require
  them on every successful facade route. Persist nonzero failure return codes
  for post-execution QC failures as well as backend failures.
- Use `MRTRIX_BIN`, an explicit binary directory, or `PATH`. Arbitrary shell
  prefixes are not supported by `run_saf`, avoiding a mismatch between backend
  commands and wrapper QC commands. The inherited inspection-only prefix
  reporting remains available for compatibility, not executable validation.

Algorithm functions are not rewritten. Outside import statements and the
`sys_exec` integration helper, backend source is unchanged except the package
docstring and removal of UTF-8 BOM markers. The original MATLAB `doc/` material
is not copied, since it describes a different runtime/API. Consult it upstream
for historical method details, not standalone installation instructions.

## Corrections Already Present in the Python Source

These changes predate standalone packaging:

- Pair endpoint coordinates with their own crossed faces during projection.
- Preserve original tractogram indices for rejected one-/two-point tracks.
- Map hard-split weights through original rather than filtered indices.
- Retain complete-mode edge/vertex intersections and deduplicate shared-point
  crossings. The published MATLAB routine clears its boundary flags.
- Use deterministic scikit-learn KMeans (`random_state=0`, `n_init=10`), which
  is not guaranteed to match MATLAB k-means clusters.

These are documented port differences, not algorithmic novelty or full MATLAB
equivalence. Do not reuse old projection outputs across implementation revisions.
The legacy clustering routine requests 60 clusters for small runs, so synthetic
pipeline fixtures need at least 60 eligible mesh vertices in total; this
packaging does not change that inherited behavior.

## Execution Boundaries

Only pre-aligned native-dMRI surfaces are supported by the public facade. It
does not execute ANTs registration or recon-all on a T1 file. Some internal
legacy parser branches remain for layout fidelity; they are not standalone
CLI/API support promises.

The reader applies only the embedded `cras` translation to surface vertices,
not a general voxel-to-world transformation. Users must prepare compatible
geometry rather than expect the wrapper to infer coordinate conventions.

The backend temporarily changes CWD and the facade temporarily sets
`MRTRIX_RNG_SEED`; restoration is tested, but the API is not thread-safe. Use
isolated processes and output directories. Raw trusted `tckgen` options still
reach a POSIX shell. Do not expose them as untrusted web-service parameters.

No checksum-based resume, anatomical validation, true-FOD generation validation,
or automatic input repair is claimed. Native Windows command handling is
unit-tested only. See [VALIDATION.md](VALIDATION.md) for tested boundaries.
