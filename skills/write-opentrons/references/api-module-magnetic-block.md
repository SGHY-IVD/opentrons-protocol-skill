# MagneticBlockContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/magnetic-block/

本类成员：。

共享成员（签名及参数见api-module-common.md）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

Flex磁力架为被动磁体，无engage/disengage/停止磁力命令；效果由耗材搬入/搬出决定。

