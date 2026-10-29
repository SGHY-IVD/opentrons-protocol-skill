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
