# Attribution and License Scope

## Original SAF Method and Implementation

The surface-based short association fibre method and original implementation
are by Dmitri Shastin and collaborators, not the maintainers of this port.

- Original repository: https://github.com/dmitrishastin/SAF
- Source baseline: `7e2a9d152caf1cf3e6bface64e7e176faac0c14f`
- Paper: Shastin et al., NeuroImage 260 (2022), 119423,
  https://doi.org/10.1016/j.neuroimage.2022.119423
- Original MIT notice: [licenses/SAF-MIT.md](licenses/SAF-MIT.md), also retained
  alongside the translated backend as `src/safpy/saf_backend/LICENSE.md`.

This repository is an unofficial port, not an official author release, a new
algorithm, or a claim of author endorsement. No MATLAB source is distributed.
Please acknowledge the original code as well as citing the paper.

## Python Port and Standalone Integration

The Python translation, geometry corrections, workflow facade and tests were
extracted from the SlicerDSpace SAF component, source revision
`57b044f54411b84230564fdcef18c469742569c7`.
Original component paths: `tractography/saf_backend`, `tractography/saf.py`, and
the related Python tests. No parent-application code is imported at runtime.

SlicerDSpace-derived additions, facade, tests, and standalone packaging are
subject to BSD-3-Clause. The source notice is retained in
[licenses/SlicerDSpace-BSD-3-Clause.txt](licenses/SlicerDSpace-BSD-3-Clause.txt).
The original SAF MIT obligations continue to apply to the translated algorithm.
Package metadata uses `MIT AND BSD-3-Clause`; it does not relicense the original
author's work or imply that all files are solely BSD-licensed.

Import namespaces and subprocess helpers were adapted for independent use;
upstream-style class and algorithm module layout was preserved. See
[docs/PORTING.md](docs/PORTING.md) for the specific changes and limitations.

Third-party Python packages and external MRtrix/FreeSurfer installations retain
their own licenses. They are dependencies, not vendored code or binaries.
No private imaging data, model weights, paper figures, PDFs, or manuscript files
are included. Synthetic test fixtures are generated from the Python tests.
