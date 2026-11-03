<div align="center">

# SAF-Py

**原生扩散空间的短联合纤维筛选 Python 独立包**

[原论文](https://doi.org/10.1016/j.neuroimage.2022.119423) | [原始代码](https://github.com/dmitrishastin/SAF) | [English](README.md) | [移植说明](docs/PORTING.md) | [测试范围](docs/VALIDATION.md)

</div>

SAF-Py 是 [Shastin 等人 SAF 框架](https://github.com/dmitrishastin/SAF)的 **Python 实现**，
提供独立安装包与 CLI，用于短联合纤维筛选和表面投影。使用时请引用原论文并注明原始代码：

Shastin D., Genc S., Parker G.D., Koller K., Tax C.M.W., Evans J., Hamandi K.,
Gray W.P., Jones D.K., Chamberland M. *Surface-based tracking for short
association fibre tractography*. NeuroImage 260, 119423 (2022).
[DOI](https://doi.org/10.1016/j.neuroimage.2022.119423)。
BibTeX 见 [英文 README](README.md#original-paper)，机器可读引用见 [CITATION.cff](CITATION.cff)。

安装 Python 包和 MRtrix3 后，准备下方列出的输入即可运行。

---

## 工作流程

`准备好的原生 dMRI 表面 → 初始轨迹 → GG/HH → 可选 PG → 长度筛选 → GWG → SAF 与表面投影`

保留原实现的 `Class_files / Filters / Pipe_modules / Data_modules / Support` 布局，
包装层提供依赖检查、计划与执行模式、manifest/QC 和播种选项。实现来源及修改记录见
[PORTING.md](docs/PORTING.md)。

表面、FOD 和已有轨迹须位于一致的 native dMRI 物理空间；运行前完成 DWI 预处理、
FOD 估计、表面重建及 postprocess。

## 安装

```bash
git clone https://github.com/ChengjinLii/SAF-Py.git
cd SAF-Py
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
saf-py --help
```

Python 3.10+；安装时会获取 NumPy、SciPy、scikit-learn、NiBabel。
开发可改用 `python -m pip install -e .`，也可用 `python -m safpy` 调用 CLI。
主要运行环境为 Linux/WSL 与 MRtrix3，已测试环境和平台覆盖见
[VALIDATION.md](docs/VALIDATION.md)。

MRtrix3 需单独安装。通过 `PATH`、`MRTRIX_BIN` 或 `--mrtrix-bin` 指定工具目录：

```bash
saf-py --check --mrtrix-bin /path/to/mrtrix/bin
```

- `mrconvert`：转换兼容目录中的 `brain.mgz`。
- `tckgen`：生成初始轨迹；也可用 `--tracks` 选择已有轨迹路线。
- `tckstats`、`tckconvert`：长度、数量检查与必需的 VTK 导出，已有轨迹路线也需要。
- `tcksample`：仅 `--fa`、`--scalar` 投影需要。

`--check` 检查默认生成路线；具体运行的 manifest 记录实际路线依赖。
可在配置环境时先生成计划，实际执行需备齐对应工具，以及下方的 FreeSurfer 格式输入。

## 输入前提

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

- white/pial 为 FreeSurfer 格式，并已在 **native dMRI 物理空间**中；每侧表面的顶点
  顺序和拓扑必须对应。原读取器会将嵌入的 `cras` 平移加到顶点坐标，结果必须与轨迹一致。
  运行前请将表面叠加到 dMRI 参考图上，确认物理坐标对齐。
- FOD 是提前计算的、MRtrix 兼容的白质纤维方向分布，须与表面同空间。
  两条执行路线均需提供 FOD 路径，生成路线用它创建初始轨迹。
- 双侧 `cortex.label` 必需，用于指定皮层顶点并排除内侧壁。标签索引必须对应当前网格。
  请在表面导出时准备对应标签，使用当前网格的顶点索引。
- `mri/brain.mgz` 是继承目录接口所需的兼容体积，需与表面导出方案一致；中间文件名
  `brain_T1.nii.gz` 是转换后体积沿用的历史文件名。
- 双侧 inflated 用于表面结果可视化，white 网格用于 GWG 边界筛选。

### DDSurfer 与 Postprocess

使用 [DDSurfer](https://github.com/ChengjinLii/DDSurfer) 时，请先完成 native-space 导出和
适当的表面 **postprocess**，检查网格完整性、white/pial 对应、标签与体积几何元信息，
并叠加到 dMRI 参考图上确认对齐。导出上方完整的 FreeSurfer 格式目录，包括
`brain.mgz`、inflated 网格及匹配的 `cortex.label`。

其他工具生成的 native dMRI 表面也可按相同输入要求使用。

## 使用示例

默认先生成计划：

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' --maxlen 40
```

确认 `saf_manifest.json` 与 `saf_qc.json` 后，在同一命令末尾加 `--execute` 执行。
示例使用 10,000 条初始轨迹和 40 mm 长度限制；`--subject` 用作运行标识及默认输出目录名。

`--surface-seeding` 显式使用白质表面顶点播种；不加时，必须在 `--tckgen-options` 中提供
适当播种方式。表面播种默认关闭，请为每次轨迹生成选择播种策略。

筛选已有轨迹：

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --tracks initial/demo.tck --output outputs/demo-filtered --maxlen 40 --execute
```

已有轨迹与表面必须同空间；已有轨迹路线使用 `--tracks`，生成路线使用
`--tckgen-options`，二者择一。权重可用 `--weights initial/demo.wts`，顺序须对应原始轨迹。
硬分割后的轨迹继承对应源轨迹的权重。Python API 见 [英文示例](README.md#python-api)。

常用参数：`--complete-intersection` 完整求交、`--gwg-hard` 硬 GWG、`--pialfilter`
可选 pial 筛选、`--notrunc` 不截断、`--remesh-seeds MM` 细化播种网格边、
`--no-length-limit` 关闭长度限制、`--fa`/可重复 `--scalar` 表面投影、
`--force` 强制重算、`--diagnostics` 保留诊断产物。完整说明见 `saf-py --help`。

`--tckgen-options` 是供可信本地用户使用的 shell 参数串。通过 `--mrtrix-bin`、
`MRTRIX_BIN` 或 `PATH` 统一指定 MRtrix 工具目录。并行处理请使用独立进程和独立输出目录。

## 输出与检查

最终输出为 `SAF.tck`、`SAF.vtk`、可选 `SAF.wts`、`log.txt`、manifest 和 QC JSON。
非诊断模式会将中间状态与表面投影移至 `cache/`。`cache/surf_data/` 中包括端点密度
`rh.t.t`/`lh.t.t` 和平均长度 `rh.l.t`/`lh.l.t` 等 FreeSurfer morphometry 文件。

请将专用输出目录与输入分开。后端可复用已有中间文件；更换输入或参数后请用新目录
或 `--force`，失败时保留输出以便排查。运行日志与 JSON 会记录本地输入路径。

自动 QC 检查轨迹数量、有限坐标、物理长度和 VTK 导出。请将 SAF 候选轨迹叠加到
native dMRI 参考图上检查，并记录实际长度、播种和筛选参数。

`--random-seed` 默认 12345，通过 `MRTRIX_RNG_SEED` 传递；使用 `-nthreads 0`
指定单线程执行。方法细节和复现性说明见 [PORTING.md](docs/PORTING.md)。

## 测试与许可

```bash
python -m unittest discover -s tests -v
SAF_PY_TEST_MRTRIX_BIN=/path/to/mrtrix/bin \
  python -m unittest tests.test_mrtrix_smoke -v
```

测试在本地运行。默认测试使用合成数据；可选 MRtrix smoke 在两种求交模式下执行
Python 后端及 MRtrix 长度、计数和格式转换命令。本地发布测试 **43 项全部通过**，
环境与覆盖范围见 [VALIDATION.md](docs/VALIDATION.md)。

Python 翻译与工作流集成来源于 SlicerDSpace，独立化修改包括包内导入、外部进程工具
和 CLI。来源与修改记录见 [PORTING.md](docs/PORTING.md)。

原 SAF 的 MIT 许可原样保留；来自 SlicerDSpace 的包装与集成贡献保留 BSD-3-Clause。
参见 [NOTICE.md](NOTICE.md) 与 [licenses/](licenses/)。
