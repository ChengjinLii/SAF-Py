<div align="center">

# SAF-Py

**Native-diffusion-space short association fibre filtering in Python**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](#installation)
[![NumPy](https://img.shields.io/badge/Numerics-NumPy-013243?logo=numpy&logoColor=white)](#dependencies)
[![MRtrix3](https://img.shields.io/badge/Tractography-MRtrix3-247F79)](#dependencies)

[Original Paper](#original-paper) | [Overview](#overview) | [Installation](#installation) | [Inputs](#inputs) | [Run SAF](#run-saf) | [Tests](#tests) | [中文](README.zh-CN.md)

</div>

SAF-Py is an **unofficial Python port and standalone packaging** of
[Dmitri Shastin's SAF framework](https://github.com/dmitrishastin/SAF).
The SAF method belongs to Shastin et al.; this repository does **not** introduce
a new tractography algorithm or claim official author endorsement.

**Prepared native-dMRI cortical surfaces + FOD + optional initial tractogram in.
Surface-constrained SAF tractography candidates out.**

No SlicerDSpace checkout, 3D Slicer runtime, MATLAB runtime, model weights,
private data, or paper assets are needed by this package.

---

## Original Paper

Shastin D., Genc S., Parker G.D., Koller K., Tax C.M.W., Evans J., Hamandi K.,
Gray W.P., Jones D.K., Chamberland M. **Surface-based tracking for short
association fibre tractography.** *NeuroImage* 260, 119423 (2022).
[doi:10.1016/j.neuroimage.2022.119423](https://doi.org/10.1016/j.neuroimage.2022.119423).

Please cite the original paper and acknowledge the
[original code](https://github.com/dmitrishastin/SAF/tree/7e2a9d152caf1cf3e6bface64e7e176faac0c14f)
when using this port. Machine-readable citation: [CITATION.cff](CITATION.cff).

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

The translated implementation retains the upstream `Class_files`, `Filters`,
`Pipe_modules`, `Data_modules`, and `Support` layout under
[`src/safpy/saf_backend`](src/safpy/saf_backend). The wrapper supplies dependency
checks, explicit plan/execute modes, manifest/QC files, and optional seeding
controls. See [Porting Notes](docs/PORTING.md) for provenance and differences.

**Scope:** surfaces and tracks must already share native diffusion physical
coordinates. There is no automatic ANTs registration, recon-all, FOD estimation,
DWI preprocessing, or surface reconstruction/postprocessing in the public API.

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
Linux/WSL with MRtrix3 is the primary execution route. Native Windows shell
handling has unit coverage, not a validated full native-Windows pipeline.

## Dependencies

| Component | Purpose |
| --- | --- |
| NumPy, SciPy, scikit-learn, NiBabel | Installed with the Python package; arrays, geometry, clustering, neuroimaging I/O. |
| MRtrix3 `mrconvert` | Convert the prepared `mri/brain.mgz` compatibility volume. |
| MRtrix3 `tckgen` | Generate initial tracks; not needed when `--tracks` is supplied. |
| MRtrix3 `tckstats`, `tckconvert` | Length/count checks and required VTK export, including the pregenerated route. |
| MRtrix3 `tcksample` | Needed only for `--fa` or `--scalar` projections. |

Install [MRtrix3](https://www.mrtrix.org/) separately and put its executables on
`PATH`, set `MRTRIX_BIN`, or pass `--mrtrix-bin /path/to/mrtrix/bin`.
The package never installs MRtrix3, FreeSurfer, or downloads datasets.

```bash
saf-py --check --mrtrix-bin /path/to/mrtrix/bin
```

`--check` reports the default generation route. A run's manifest records the
actual route-specific checks. Missing commands fail execution, but a plan can
still be written without MRtrix. Native execution does not require FreeSurfer
executables once all inputs below have been prepared.

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
  Do not pass untransformed T1-space surfaces or confuse voxel indices, tkRAS,
  scanner RAS and LPS. The wrapper checks file presence, not anatomical alignment.
- **FOD:** a pre-estimated MRtrix-compatible white-matter FOD in the same physical
  space. A raw DWI, FA map, or tensor image is not a FOD. The inherited interface
  still requires the FOD path when using pregenerated tracks; it is not used to
  generate new tracks in that route.
- **`cortex.label`:** both hemisphere files are required, indexed against the
  supplied meshes. They identify eligible cortical vertices and exclude the
  medial wall. An all-vertex replacement changes the method; this package does
  not generate labels, copy labels from mismatched meshes, or silently use all
  vertices.
- **Compatibility volume:** `mri/brain.mgz` is used by the inherited directory
  interface and must be prepared consistently with your surface export. Its
  historical output name is `brain_T1.nii.gz`; this does not perform registration
  or imply that this port reconstructs a T1 image.
- **Inflated meshes:** both are required by the inherited surface projection
  export. They are visualization companions, not the GWG boundary.

### DDSurfer and Postprocess

If using [DDSurfer](https://github.com/ChengjinLii/DDSurfer), complete its
native-space export and appropriate surface **postprocess** first. Confirm mesh
integrity, white/pial correspondence, labels, metadata and alignment overlaid on
the dMRI reference. DDSurfer prediction alone is not necessarily the complete
FreeSurfer-format directory shown above. SAF-Py does not run DDSurfer or its
postprocess, repair topology, or invent a missing `cortex.label`.

The native interface can also accept appropriately prepared surfaces from other
tools. Generating `brain.mgz`, inflated meshes and cortex labels is an upstream
preparation task, not an operation provided here.

---

## Run SAF

### Plan First

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' --maxlen 40
```

Without `--execute`, only `saf_manifest.json` and `saf_qc.json` are written.
The values above are an illustrative small run, not a validated study protocol.
`--subject` is a run label, not a request to locate or preprocess raw DWI.

### Generate and Filter

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' \
  --maxlen 40 --execute
```

`--surface-seeding` explicitly enables the upstream surface-vertex seed route.
Otherwise supply appropriate seeding in the trusted `--tckgen-options` string.
The inherited parser defaults surface seeding to off; this port does not change
that algorithm default. Do not run without a seeding strategy.

### Filter Existing Tracks

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --tracks initial/demo.tck --output outputs/demo-filtered --maxlen 40 --execute
```

The input `.tck` must share surface coordinates. Do not combine `--tracks` and
`--tckgen-options`. Add `--weights initial/demo.wts` only when weights match the
original input streamline order. Hard-split weights are copied from the source,
not re-estimated SIFT2 weights.

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
| `--no-length-limit` | Disable length filtering; not a short-fibre guarantee. |
| `--complete-intersection` | Use the complete, rather than default fast, mesh-intersection branch. |
| `--gwg-hard` | Split using the hard GWG rule. |
| `--pialfilter` | Enable optional pial filtering. |
| `--notrunc` | Do not truncate streamlines at the white-surface boundary. |
| `--remesh-seeds MM` | Refine long seed-mesh edges, not cortical postprocessing. |
| `--fa FILE`, `--scalar FILE` | Optional surface scalar projections; requires `tcksample`. |
| `--random-seed N` | Export `MRTRIX_RNG_SEED`; default 12345. |
| `--force` | Recompute in a dedicated output directory. |
| `--diagnostics` | Retain diagnostic products in the output root. |

`tckgen-options` is a trusted local shell string inherited from SAF, not an
untrusted request field. The standalone facade does not support arbitrary
`mrtrix_prefix` container/shell wrappers; use a consistent executable directory.
Runs change process CWD and environment temporarily: use separate **processes**,
not threads, for parallel subjects, with a separate output directory per run.

## Outputs and Review

`SAF.tck`, `SAF.vtk`, optional `SAF.wts`, `log.txt`, `saf_manifest.json` and
`saf_qc.json` are final products. Intermediate state and surface projections
are moved to `cache/` unless `--diagnostics` is used. Surface measures include
endpoint density (`rh.t.t`, `lh.t.t`) and mean streamline length (`rh.l.t`,
`lh.l.t`) in FreeSurfer morphometry format under `cache/surf_data/`.

Use a dedicated output directory. Existing intermediate files may be reused by
the inherited backend; this is **not checksum-validated resume**. Use a new
directory or `--force` after changing inputs or parameters. Do not place inputs
inside an output/cache directory, and keep failed outputs for diagnosis.

Completed QC checks decoded streamline count, finite coordinates, physical
length and VTK export. It does **not** validate cortical geometry or anatomy.
The manifest/logs contain local input paths; review them before sharing.

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
checks and failure/QC records. Tests run locally; no GitHub Actions workflows are
included. The opt-in smoke executes the real Python backend
and MRtrix conversion/count/length/VTK commands on synthetic surfaces and two
pregenerated tracks, in both intersection modes. It does not test FOD fitting,
real-data `tckgen`, or anatomical validity. [Validation scope](docs/VALIDATION.md).

## Limitations and Attribution

The products are SAF tractography **candidates**, not guaranteed U-fibres or
adjacent-gyri ground truth. Soft GWG retains outer crossings and does not require
every interior point to remain in white matter. The inherited 90 mm threshold
is not a universal anatomical definition of a short fibre.

scikit-learn and MATLAB clustering need not agree. The translated source already
contains documented endpoint/index/complete-intersection corrections; full
MATLAB equivalence and whole-pipeline bitwise reproducibility are not claimed.
A fixed seed alone does not make multi-threaded MRtrix tracking reproducible;
pin versions and use `-nthreads 0` when controlling single-thread execution.
This is research software, not a clinical diagnostic tool.

The original SAF MIT notice is retained verbatim. SlicerDSpace-derived wrapper
and port-integration contributions retain BSD-3-Clause terms. See
[NOTICE.md](NOTICE.md), [licenses](licenses/) and [Porting Notes](docs/PORTING.md).
No MATLAB source, private imaging data, model assets, or paper materials are
distributed here.
