# FlexStackerContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

模块硬件/机制与必要条件见[Flex Stacker](module-conditions-flex-stacker.md#flex-stacker)，经验与组合示例见[对应经验](module-practices-flex-stacker.md#flex-stacker)。本类接口契约按以下成员直达页唯一维护；共享加载签名见[共享模块API](api-module-common.md)。

|动作/任务|成员直达|
|---|---|
|库存类型与初始配置|[FlexStackerContext.set_stored_labware](api-module-flex-stacker-configuration.md#flexstackercontextset_stored_labware)|
|库存类型与初始配置|[FlexStackerContext.set_stored_labware_items](api-module-flex-stacker-configuration.md#flexstackercontextset_stored_labware_items)|
|容量与可存储列表|[FlexStackerContext.get_current_storable_labware](api-module-flex-stacker-capacity.md#flexstackercontextget_current_storable_labware)|
|容量与可存储列表|[FlexStackerContext.get_current_storable_labware_from_list](api-module-flex-stacker-capacity.md#flexstackercontextget_current_storable_labware_from_list)|
|容量与可存储列表|[FlexStackerContext.get_max_storable_labware](api-module-flex-stacker-capacity.md#flexstackercontextget_max_storable_labware)|
|容量与可存储列表|[FlexStackerContext.get_max_storable_labware_from_list](api-module-flex-stacker-capacity.md#flexstackercontextget_max_storable_labware_from_list)|
|供料、回收与库存读取|[FlexStackerContext.get_stored_labware](api-module-flex-stacker-supply.md#flexstackercontextget_stored_labware)|
|供料、回收与库存读取|[FlexStackerContext.retrieve](api-module-flex-stacker-supply.md#flexstackercontextretrieve)|
|供料、回收与库存读取|[FlexStackerContext.store](api-module-flex-stacker-supply.md#flexstackercontextstore)|
|供料、回收与库存读取|[FlexStackerContext.serial_number](api-module-flex-stacker-supply.md#flexstackercontextserial_number)|
|人工补给与清空|[FlexStackerContext.fill](api-module-flex-stacker-manual.md#flexstackercontextfill)|
|人工补给与清空|[FlexStackerContext.fill_items](api-module-flex-stacker-manual.md#flexstackercontextfill_items)|
|人工补给与清空|[FlexStackerContext.empty](api-module-flex-stacker-manual.md#flexstackercontextempty)|

共享成员（签名及参数见[api-module-common.md](api-module-common.md)）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。
