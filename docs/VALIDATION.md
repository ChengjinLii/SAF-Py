# Validation Scope

The repository contains no real-subject imaging data or MATLAB source. Unit
tests and opt-in MRtrix integration tests generate tiny synthetic inputs at
runtime. These are software/geometry checks, not scientific validation on a
cohort or a claim of exact MATLAB equivalence.

## Reproduce

```bash
python -m pip install .
python -m unittest discover -s tests -v
SAF_PY_TEST_MRTRIX_BIN=/path/to/mrtrix/bin \
  python -m unittest tests.test_mrtrix_smoke -v
```

The normal suite skips the real-MRtrix smoke unless its environment variable is
set. No pytest dependency is required. Tests are local only; no GitHub Actions
workflows are included or triggered.

## Coverage

- Analytic face/edge/vertex intersections, ordered crossings, de-duplication,
  asymmetric endpoint vertex pairing and missing-crossing bookkeeping.
- Rejected short-track indices, optional pial-filter empty cases and hard-split
  weight mapping through the original input track indices.
- Shell quoting for spaces and metacharacters, subprocess failures, RNG seed
  forwarding, and Windows command decoding/rejection (mocked, not native E2E).
- Every packaged backend module imports without parent checkout paths or
  `shared`; package import does not alter `sys.path`.
- CLI help/planning, explicit/environment MRtrix discovery, mandatory surface
  inputs, invalid limits and incompatible options.
- Backend failure records, CWD/environment restoration, actual NiBabel TCK
  decoding and nonzero return codes on length/QC failure.
- Stable replacement of cached intermediates on forced reruns.

The opt-in smoke runs the real Python SAF backend with MRtrix `mrconvert`,
`tckstats` and `tckconvert`, synthetic cortical meshes/labels and two generated
pregenerated tracks. Both fast and complete intersection modes must produce
decodable two-streamline SAF files, VTK files, surface projections and completed
QC records. It does not run `tckgen` with a real FOD or test `tcksample` on real
scalar maps; its zero-valued FOD placeholder is only for the non-generation
interface route and is not a scientific FOD example.

## Not Established

- Whole-pipeline MATLAB equivalence or identical MATLAB/scikit-learn clusters.
- Biological validity, adjacent-gyri U-fibre ground truth, or clinical utility.
- Input coordinate alignment/topology correctness from file-presence checks.
- Full real-data generation, performance/scalability, or native-Windows E2E.
- Cross-version/platform execution beyond the local environment recorded below.

Run manifests/QC records identify the inherited scientific implementation and
actual filter parameters. A `completed` status is a computational contract,
not an anatomical judgment. Review the tractogram on its native dMRI reference.

## Local Release Verification

Run on 2026-11-04, Linux, in a freshly created virtual environment without
system site-packages. No host-application source directory was on `PYTHONPATH`.

| Component | Tested version |
| --- | --- |
| Python | 3.13.5 |
| NumPy | 2.5.4 |
| SciPy | 1.18.1 |
| scikit-learn | 1.9.1 |
| NiBabel | 5.4.2 |
| MRtrix3 | 3.0.8 |

`python -m unittest discover -s tests -v` with
`SAF_PY_TEST_MRTRIX_BIN` set: **43 tests passed**, including the real-MRtrix
smoke in both fast and complete modes. Each mode retained the expected two
synthetic tracks and wrote decodable TCK, VTK, surface data and successful QC.

`python -m pip check`: no broken requirements. Wheel and source distribution
builds succeeded. Importing the installed wheel from a separate working
directory using `python -I` loaded its installed `safpy` package and full
backend without `shared`, the host checkout, or source-path injection.

A source audit compared non-import ASTs for **55 backend modules** against the
extraction baseline: all unchanged. The package docstring and the subprocess
integration helper are the documented exceptions, not algorithm rewrites.

The inherited SciPy MAT-state export emits non-fatal `MatWriteWarning` messages
for private NiBabel header keys `_dtype` and `_offset_data`. These warnings did
not prevent either synthetic pipeline from completing or affect the checked
TCK/VTK/surface outputs; lossless MAT-header round-tripping is not established.

All checks were local. No GitHub Actions workflow is shipped or used.
