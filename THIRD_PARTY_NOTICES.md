# 第三方来源 / Third-party sources

本项目的 API 摘录、硬件定义与参数数据包含从 Opentrons 官方资料提取或整理的内容。它们不是本项目原创的硬件保证。项目对资料进行了筛选、重组、中文注释，并叠加了独立的经验规则与参数覆盖；具体来源、版本和覆盖信息见各参考文件及 JSON 元数据。

API excerpts, hardware definitions, and parameter data include material extracted or adapted from official Opentrons sources. This project selects, reorganizes, and annotates that material, and adds separate experiential rules and parameter overrides. Refer to the individual files and JSON metadata for sources, versions, and modifications.

- Upstream repository / 官方仓库: https://github.com/Opentrons/opentrons
- Documentation / 官方文档: https://docs.opentrons.com/v2/
- Upstream repository license / 上游仓库许可证: [Apache License 2.0](LICENSES/Opentrons-Apache-2.0.txt)
- Upstream copyright and other applicable notices remain with their respective owners. / 上游版权及其他适用声明归各自权利人所有。

The included Apache license applies to the relevant upstream material; it does not by itself license all original content in this repository. No affiliation or endorsement by Opentrons is implied.

附带的 Apache 许可证适用于相关上游材料，不自动构成本项目全部原创内容的授权。项目不暗示 Opentrons 的隶属关系或背书。

## 可选mDNS依赖 / Optional mDNS dependency

mDNS发现可按需安装 `zeroconf==0.151.5`，其发行包元数据声明许可证为 `LGPL-2.1-or-later`。本仓库仅提供依赖声明和调用代码，不附带该包的源码或二进制；具体许可随所安装的发行包提供。该依赖不用于普通协议编写或手动地址HTTP连接。

Optional mDNS discovery uses `zeroconf==0.151.5`, whose distribution metadata declares `LGPL-2.1-or-later`. This repository includes the dependency declaration and calling code, not the package's source or binaries. Consult the installed distribution for its applicable license. It is not needed for ordinary protocol writing or HTTP connections to explicit addresses.

- Project / 项目: https://github.com/python-zeroconf/python-zeroconf
- Documentation / 文档: https://python-zeroconf.readthedocs.io

## 用户提供的扩展来源 / User-provided extension sources

第三方设备实现、耗材辅助类及示例由用户提供的程序抽取或改写；来源以原文件SHA-256追溯，具体调整及当前边界见[扩展入口](skills/write-opentrons/references/extensions.md)、对应源码与接口说明。这些来源不是新核实的厂家硬件API，收录不表示官方背书或实机验证。本说明不为这些来源指定或推定许可证，也不改变项目原创内容尚未指定许可证的状态。

Third-party device implementations, the labware helper, and examples are extracted or adapted from user-provided programs. Original-file SHA-256 fingerprints trace their sources; modifications and current limits are documented in the [extension reference](skills/write-opentrons/references/extensions.md), source files, and API references. Inclusion does not establish a newly verified vendor hardware API, official endorsement, or physical validation. These notices do not assign or infer licenses for those sources. No license has yet been selected for original project content.

| 来源 / Source | 用途 / Adaptation | 原文件SHA-256 / Original-file SHA-256 |
| --- | --- | --- |
| 用户完整洗板模板 / User-provided wash template | 倾斜设备、CH340通讯及Flex承载/几何 / Tilt device, CH340 transport, and Flex loading/geometry | `3f8af32d1f0257ef7990e3d68aecb52b16b9dd08fd7a7474b89e32ed3269b193` |
| `DDM血浆过滤正压_API_2.22.py` | 正压设备 / Positive-pressure device | `625bcbcdd06a46650d457f4eb767e0263cad52188116a63d152d5aff33cdf098` |
| `Riser.py` | 普通槽位叠板辅助 / Ordinary-slot plate-stack helper | `ed4697668b4bf98b7032dc91631d1ca9fc9b3ba8ec9afaafc9fb033592628780` |
| `stacker_test.py` | 原生Stacker连续供料示例 / Native Stacker continuous-supply example | `db036afd6a0ee3b540664f72fa695aadd42f3cdbfe48b2b4664c4fa98b6701b5` |

## 可选USB依赖 / Optional USB dependencies

真实控制倾斜或正压设备时使用[PyUSB](https://github.com/pyusb/pyusb)，并使用环境中可用的USB后端及设备访问权限。本仓库提供调用代码，不附带PyUSB或USB后端的源码、二进制及驱动；适用许可以实际安装的各发行包为准。完整设备单文件仍依赖这些运行环境，普通查询脚本与Riser不需要USB依赖。

The device implementations import [PyUSB](https://github.com/pyusb/pyusb); real tilt or positive-pressure control requires it, an available USB backend, and device permissions. This repository provides calling code, without distributing PyUSB or USB-backend sources, binaries, or drivers; consult each installed distribution for its applicable terms. Self-contained device files still require those runtime components. Ordinary query scripts and Riser do not need USB dependencies.
