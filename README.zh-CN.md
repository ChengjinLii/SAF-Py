<div align="center">

# SAF-Py

**原生扩散空间的短联合纤维筛选 Python 独立包**

[原论文](https://doi.org/10.1016/j.neuroimage.2022.119423) | [原始代码](https://github.com/dmitrishastin/SAF) | [English](README.md) | [移植说明](docs/PORTING.md) | [测试范围](docs/VALIDATION.md)

</div>

这是 **Dmitri Shastin 等人 SAF 框架的非官方 Python 移植与独立打包**，不是新的
纤维追踪算法，也不代表原作者官方发布。请引用原论文并注明原始代码：

Shastin D., Genc S., Parker G.D., Koller K., Tax C.M.W., Evans J., Hamandi K.,
Gray W.P., Jones D.K., Chamberland M. *Surface-based tracking for short
association fibre tractography*. NeuroImage 260, 119423 (2022).
[DOI](https://doi.org/10.1016/j.neuroimage.2022.119423)。
BibTeX 见 [英文 README](README.md#original-paper)，机器可读引用见 [CITATION.cff](CITATION.cff)。

无需 SlicerDSpace 源码目录、3D Slicer 或 MATLAB。仓库不包含 MATLAB 源码、真实受试者
数据、模型权重或论文材料。

---

## 工作流程

`准备好的原生 dMRI 表面 → 初始轨迹 → GG/HH → 可选 PG → 长度筛选 → GWG → SAF 与表面投影`

保留原实现的 `Class_files / Filters / Pipe_modules / Data_modules / Support` 布局，
仅对独立包导入、外部进程调用及包装层作适配。已有移植修正、上游版本和科学边界见
[PORTING.md](docs/PORTING.md)。

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
完整执行优先使用 Linux/WSL；原生 Windows 只有命令处理单元测试覆盖，未完成全流程验证。

MRtrix3 需单独安装。通过 `PATH`、`MRTRIX_BIN` 或 `--mrtrix-bin` 指定工具目录：

```bash
saf-py --check --mrtrix-bin /path/to/mrtrix/bin
```

- `mrconvert`：转换兼容目录中的 `brain.mgz`。
- `tckgen`：生成初始轨迹；提供 `--tracks` 时不需要。
- `tckstats`、`tckconvert`：长度、数量检查与必需的 VTK 导出，已有轨迹路线也需要。
- `tcksample`：仅 `--fa`、`--scalar` 投影需要。

`--check` 检查默认生成路线；具体运行的 manifest 记录实际路线依赖。
仅生成计划允许缺少 MRtrix，真实执行会检查并报错。输入准备完成后无需调用 FreeSurfer
可执行程序；本包不会自动安装外部应用或下载数据。

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
  不可混用未配准的 T1 表面、体素索引、tkRAS、scanner RAS 或 LPS。
- FOD 是提前计算的、MRtrix 兼容的白质纤维方向分布，不是原始 DWI、FA 或张量图像。
  使用已有轨迹时仍需提供 FOD 路径，以满足继承的接口，但不会用它生成新轨迹。
- 双侧 `cortex.label` 必需，用于指定皮层顶点并排除内侧壁。标签索引必须对应当前网格。
  本包不会伪造缺失标签、从不匹配网格复制标签或默认全部顶点为皮层。
- `mri/brain.mgz` 是继承目录接口所需的兼容体积，需与表面导出方案一致；中间文件名
  `brain_T1.nii.gz` 不代表本包重建 T1 或执行配准。
- 双侧 inflated 是表面结果可视化伴随文件，不用于 GWG 边界筛选。

### DDSurfer 与 Postprocess

使用 [DDSurfer](https://github.com/ChengjinLii/DDSurfer) 时，请先完成 native-space 导出和
适当的表面 **postprocess**，检查网格完整性、white/pial 对应、标签与体积几何元信息，
并叠加到 dMRI 参考图上确认对齐。单独的网络表面预测不一定构成完整输入目录。

SAF-Py 不执行 DDSurfer、postprocess、拓扑修复、标签生成、FOD 估计、DWI 预处理、
自动 ANTs 配准或 recon-all。也可使用其他来源的合规 native dMRI 表面。
包装层只核查文件存在，不能证明坐标或解剖有效。

## 使用示例

先生成计划，不加 `--execute` 不会运行追踪：

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --output outputs/demo --surface-seeding \
  --tckgen-options='-algorithm iFOD2 -select 10000 -nthreads 0' --maxlen 40
```

确认 `saf_manifest.json` 与 `saf_qc.json` 后，在同一命令末尾加 `--execute` 执行。
示例参数仅演示小规模调用，不是经验证的研究方案。

`--surface-seeding` 显式使用白质表面顶点播种；不加时，必须在 `--tckgen-options` 中提供
适当播种方式。原解析器默认关闭表面播种，本包没有更改这一算法默认值。

筛选已有轨迹：

```bash
saf-py --subject demo --fs-dir prepared/demo --fod fod/demo/wmfod.mif \
  --tracks initial/demo.tck --output outputs/demo-filtered --maxlen 40 --execute
```

已有轨迹与表面必须同空间；不能同时传入 `--tracks` 和 `--tckgen-options`。
权重可用 `--weights initial/demo.wts`，顺序须对应原始轨迹。硬分割后复制的权重不是
重新估计的 SIFT2 权重。Python API 见 [英文示例](README.md#python-api)。

常用参数：`--complete-intersection` 完整求交、`--gwg-hard` 硬 GWG、`--pialfilter`
可选 pial 筛选、`--notrunc` 不截断、`--remesh-seeds MM` 细化播种网格边、
`--no-length-limit` 关闭长度限制、`--fa`/可重复 `--scalar` 表面投影、
`--force` 强制重算、`--diagnostics` 保留诊断产物。完整说明见 `saf-py --help`。

`--tckgen-options` 是供可信本地用户使用的 shell 参数串，不应接收不可信请求。
独立 facade 不支持任意 `mrtrix_prefix` 容器包装，请统一指定 MRtrix 工具目录。
运行会临时修改进程目录和环境；并行处理应使用独立进程和独立输出目录，不要用线程。

## 输出与检查

最终输出为 `SAF.tck`、`SAF.vtk`、可选 `SAF.wts`、`log.txt`、manifest 和 QC JSON。
非诊断模式会将中间状态与表面投影移至 `cache/`。`cache/surf_data/` 中包括端点密度
`rh.t.t`/`lh.t.t` 和平均长度 `rh.l.t`/`lh.l.t` 等 FreeSurfer morphometry 文件。

请使用专用输出目录，不要把输入放进输出或 cache。原实现可能复用已有中间文件，
**不是校验和验证的恢复机制**；更换输入或参数后请用新目录或 `--force`。
运行日志与 JSON 会记录本地输入路径，分享前需自行检查。

完成状态仅核查轨迹数量、有限坐标、物理长度和 VTK 导出，不代表解剖学验证。
结果是 SAF 候选轨迹，不保证每条都是相邻脑回 U 纤维。soft GWG 保留外侧交点，
并不要求轨迹内部每一点均位于白质；继承的 90 mm 默认值不是通用短纤维解剖定义。
请记录实际长度、播种、筛选参数并人工检查。

`--random-seed` 默认 12345，通过 `MRTRIX_RNG_SEED` 传递；多线程不能仅凭固定种子
保证逐比特复现。需要控制单线程时使用 `-nthreads 0`，并记录软件版本。
scikit-learn 与 MATLAB 聚类不保证一致，也不宣称完整 MATLAB 等价。
本包仅供研究，不用于临床诊断。

## 测试与许可

```bash
python -m unittest discover -s tests -v
SAF_PY_TEST_MRTRIX_BIN=/path/to/mrtrix/bin \
  python -m unittest tests.test_mrtrix_smoke -v
```

默认测试只用合成数据；可选 MRtrix smoke 在两种求交模式下执行真实后端及 MRtrix
长度、计数和格式转换命令，不使用真实影像。它不验证真实 FOD 的 `tckgen` 或解剖正确性。
详情见 [VALIDATION.md](docs/VALIDATION.md)。

原 SAF 的 MIT 许可原样保留；来自 SlicerDSpace 的包装与集成贡献保留 BSD-3-Clause。
参见 [NOTICE.md](NOTICE.md) 与 [licenses/](licenses/)。
