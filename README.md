<div align="center">

# SAF-Py

**Native-diffusion-space short association fibre filtering in Python**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#installation)
[![NumPy](https://img.shields.io/badge/Numerics-NumPy-013243?logo=numpy&logoColor=white)](#dependencies)
[![MRtrix3](https://img.shields.io/badge/Tractography-MRtrix3-247F79)](#dependencies)

[Original Paper](#original-paper) | [Overview](#overview) | [Installation](#installation) | [Inputs](#inputs) | [Run SAF](#run-saf) | [Tests](#tests) | [中文](README.zh-CN.md)

</div>

SAF-Py is a **Python implementation of
[Shastin et al.'s SAF framework](https://github.com/dmitrishastin/SAF)**.
It provides a standalone package and CLI for short association fibre filtering
and surface projection.

**Prepared native-dMRI cortical surfaces + FOD + optional initial tractogram in.
Surface-constrained SAF tractography candidates out.**

Install the Python package and MRtrix3, then supply the prepared inputs below.

---

## Original Paper

Shastin D., Genc S., Parker G.D., Koller K., Tax C.M.W., Evans J., Hamandi K.,
Gray W.P., Jones D.K., Chamberland M. **Surface-based tracking for short
association fibre tractography.** *NeuroImage* 260, 119423 (2022).
[doi:10.1016/j.neuroimage.2022.119423](https://doi.org/10.1016/j.neuroimage.2022.119423).

Please cite the original paper and acknowledge the
[original code](https://github.com/dmitrishastin/SAF/tree/7e2a9d152caf1cf3e6bface64e7e176faac0c14f)
when using SAF-Py. Machine-readable citation: [CITATION.cff](CITATION.cff).

```bibtex
@article{Shastin2022SAF,
  author = {Shastin, Dmitri and Genc, Sila and Parker, Greg D. and
            Koller, Kristin and Tax, Chantal M. W. and Evans, John and
            Hamandi, Khalid and Gray, William P. and Jones, Derek K. and
            Chamberland, Maxime},
  title = {Surface-based tracking for short association fibre tractography},
  journal = {NeuroImage},
  volume = {260},
  pages = {119423},
  year = {2022},
  doi = {10.1016/j.neuroimage.2022.119423}
}
```

---

## Overview

`Prepared surfaces -> initial tracks -> GG/HH -> optional PG -> length -> GWG -> SAF + surface projections`

The implementation retains the upstream `Class_files`, `Filters`,
`Pipe_modules`, `Data_modules`, and `Support` layout under
[`src/safpy/saf_backend`](src/safpy/saf_backend). The wrapper supplies dependency
checks, explicit plan/execute modes, manifest/QC files, and optional seeding
controls. See [Porting Notes](docs/PORTING.md) for provenance and differences.

Prepare surfaces, FOD and any initial tracks in matching native diffusion
physical coordinates. Complete DWI preprocessing, FOD estimation, surface
reconstruction and postprocessing before running SAF.

---

## Installation

```bash
git clone https://github.com/ChengjinLii/SAF-Py.git
cd SAF-Py
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
saf-py --help
```

For development, use `python -m pip install -e .` instead. You can run
`python -m safpy` as an alternative to `saf-py`. Python 3.10+ is required;
Linux/WSL with MRtrix3 is the primary execution route. The tested environment
and platform coverage are recorded in [Validation](docs/VALIDATION.md).

## Dependencies

| Component | Purpose |
| --- | --- |
| NumPy, SciPy, scikit-learn, NiBabel | Installed with the Python package; arrays, geometry, clustering, neuroimaging I/O. |
| MRtrix3 `mrconvert` | Convert the prepared `mri/brain.mgz` compatibility volume. |
| MRtrix3 `tckgen` | Generate initial tracks; use `--tracks` to filter existing tracks instead. |
| MRtrix3 `tckstats`, `tckconvert` | Length/count checks and required VTK export, including the pregenerated route. |
| MRtrix3 `tcksample` | Needed only for `--fa` or `--scalar` projections. |

Install [MRtrix3](https://www.mrtrix.org/) separately and put its executables on
`PATH`, set `MRTRIX_BIN`, or pass `--mrtrix-bin /path/to/mrtrix/bin`.

```bash
saf-py --check --mrtrix-bin /path/to/mrtrix/bin
```

`--check` reports the default generation route. A run's manifest records the
actual route-specific checks. Plans can be written during environment setup;
execution requires the commands for the selected route. Supply the prepared
FreeSurfer-format files listed below.

---

## Inputs

```text
prepared/demo/
  mri/brain.mgz
  surf/lh.white
  surf/rh.white
  surf/lh.pial
  surf/rh.pial
  surf/lh.inflated
  surf/rh.inflated
  label/lh.cortex.label
  label/rh.cortex.label
fod/demo/wmfod.mif
```

- **Surfaces:** FreeSurfer-format white/pial meshes in native dMRI space, with
  matched vertex ordering and topology within each hemisphere. Embedded volume
  geometry must be valid. The inherited reader adds the embedded `cras`
  translation to vertices; the result must align with MRtrix track coordinates.
  Verify physical-coordinate alignment by overlaying the surfaces on the dMRI
  reference before running SAF.
- **FOD:** a pre-estimated MRtrix-compatible white-matter FOD in the same physical
  space. Provide the FOD path for both execution routes; the generation route
  uses it to create initial tracks.
- **`cortex.label`:** both hemisphere files are required, indexed against the
  supplied meshes. They identify eligible cortical vertices and exclude the
  medial wall. Prepare labels alongside the surface export using the supplied
  meshes' vertex indices.
- **Compatibility volume:** `mri/brain.mgz` is used by the inherited directory
  interface and must be prepared consistently with your surface export. Its
  converted volume is saved under the historical name `brain_T1.nii.gz`.
- **Inflated meshes:** both are required by the inherited surface projection
  export for visualization; white meshes define the GWG boundary.

### DDSurfer and Postprocess

If using [DDSurfer](https://github.com/ChengjinLii/DDSurfer), complete its
native-space export and appropriate surface **postprocess** first. Confirm mesh
integrity, white/pial correspondence, labels, metadata and alignment overlaid on
the dMRI reference. Export the complete FreeSurfer-format directory shown above,
including `brain.mgz`, inflated meshes and matching `cortex.label` files.

The native interface can also accept appropriately prepared surfaces from other
tools using the same input requirements.

---

## Run SAF

### Plan First

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' --maxlen 40
```

By default, the command writes `saf_manifest.json` and `saf_qc.json` for review.
The example uses 10,000 initial tracks and a 40 mm length limit.
`--subject` labels the run and organizes its default output directory.

### Generate and Filter

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' \
  --maxlen 40 --execute
```

`--surface-seeding` explicitly enables the upstream surface-vertex seed route.
Otherwise supply appropriate seeding in the trusted `--tckgen-options` string.
Surface seeding is off by default; choose a seeding strategy for each generation
run.

### Filter Existing Tracks

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --tracks initial/demo.tck --output outputs/demo-filtered --maxlen 40 --execute
```

The input `.tck` must share surface coordinates. Choose either `--tracks` for
existing tracks or `--tckgen-options` for generation. Add
`--weights initial/demo.wts` with weights in the original input streamline
order. Hard-split tracks inherit their corresponding source weights.

### Python API

```python
from pathlib import Path
from safpy import SAFConfig, run_saf

result = run_saf(SAFConfig(
    subject_id="demo", input_root=Path("."),
    fs_dir=Path("prepared/demo"), fod_path=Path("fod/demo/wmfod.mif"),
    output_dir=Path("outputs/demo"),
    pregenerated_tractogram=Path("initial/demo.tck"),
    maxlen=40.0, execute=True,
))
print(result.saf_tractogram, result.qc_path)
```

### Common Options

| Option | Effect |
| --- | --- |
| `--maxlen MM` | Maximum length of initial and decoded final tracks; inherited default: 90 mm. |
| `--no-length-limit` | Disable length filtering. |
| `--complete-intersection` | Use the complete, rather than default fast, mesh-intersection branch. |
| `--gwg-hard` | Split using the hard GWG rule. |
| `--pialfilter` | Enable optional pial filtering. |
| `--notrunc` | Do not truncate streamlines at the white-surface boundary. |
| `--remesh-seeds MM` | Refine long seed-mesh edges. |
| `--fa FILE`, `--scalar FILE` | Optional surface scalar projections; requires `tcksample`. |
| `--random-seed N` | Export `MRTRIX_RNG_SEED`; default 12345. |
| `--force` | Recompute in a dedicated output directory. |
| `--diagnostics` | Retain diagnostic products in the output root. |

`tckgen-options` is a shell option string for trusted local use. Configure a
consistent MRtrix executable directory through `--mrtrix-bin`, `MRTRIX_BIN` or
`PATH`. For parallel subjects, use separate **processes** and output directories.

## Outputs and Review

`SAF.tck`, `SAF.vtk`, optional `SAF.wts`, `log.txt`, `saf_manifest.json` and
`saf_qc.json` are final products. Intermediate state and surface projections
are moved to `cache/` unless `--diagnostics` is used. Surface measures include
endpoint density (`rh.t.t`, `lh.t.t`) and mean streamline length (`rh.l.t`,
`lh.l.t`) in FreeSurfer morphometry format under `cache/surf_data/`.

Use a dedicated output directory, separate from the inputs. The backend can
reuse existing intermediate files; use a new directory or `--force` after
changing inputs or parameters. Keep failed outputs for diagnosis.

Completed QC checks decoded streamline count, finite coordinates, physical
length and VTK export. Review the resulting candidates on the native dMRI
reference. The manifest/logs record local input paths.

---

## Tests

After installation, from the repository root:

```bash
python -m unittest discover -s tests -v
# Optional: real MRtrix calls, still using generated tiny data only
SAF_PY_TEST_MRTRIX_BIN=/path/to/mrtrix/bin \
  python -m unittest tests.test_mrtrix_smoke -v
```

Unit tests cover analytic intersections, endpoint indexing, rejected short
tracks, hard-split weight mapping, shell quoting, imports, CLI planning, dependency
checks and failure/QC records. Tests run locally. The opt-in smoke executes the
Python backend
and MRtrix conversion/count/length/VTK commands on synthetic surfaces and two
pregenerated tracks, in both intersection modes. The local release suite passed
all **43 tests**; environment details and coverage are recorded in
[Validation](docs/VALIDATION.md).

## Provenance and License

The Python translation and workflow integration were adapted from SlicerDSpace.
Standalone changes cover package imports, subprocess utilities and the CLI.
Implementation history, method details and reproducibility guidance are in
[Porting Notes](docs/PORTING.md).

The original SAF MIT notice is retained verbatim. SlicerDSpace-derived wrapper
and port-integration contributions retain BSD-3-Clause terms. See
[NOTICE.md](NOTICE.md), [licenses](licenses/) and [Porting Notes](docs/PORTING.md).
