# 模块API索引

基线API 2.30；2026-10-16同步。先按设备定位，只读所用成员及其共享类型，不一次读取所有模块。覆盖官方参考页公开的方法与属性，包括加载、运行、状态读取、停用及并发接口；已弃用参数保留标记，不能继续生成。

## 模块资料契约与入口

六类模块统一提供：硬件身份/安装入口、硬件与机制、条件约束、操作经验、API及加载示例。硬件名称查catalog、静态安装/适配查installation；各模块的物理能力/状态和约束分别在module-conditions同名节，经验在module-practices同名节。沿用已有唯一来源，不在每个模块下再复制槽位表或API。未维护的分类明确“待补充/无额外条目”，不补造事实，也不把空经验入口当作设备不可用。

触发：涉及模块装载、承载位/库存/内部状态含义、能力判断或实际操作时，读取该模块相关机制/条件和API；只讨论布局时也不跳过必要模块语义。经验按场景查用，不默认展开全部模块或插入建议动作。

|模块|本类条目数与API|硬件/机制及条件约束|经验入口|
|---|---|---|---|
|Heater-Shaker|17；[API](api-module-heater-shaker.md)|[机制/条件](module-conditions.md#heater-shaker)|[经验](module-practices.md#heater-shaker)|
|Temperature Module|7；[API](api-module-temperature-module.md)|[机制/条件](module-conditions.md#temperature-module)|[经验](module-practices.md#temperature-module)|
|Thermocycler|19；[API](api-module-thermocycler.md)|[机制/条件](module-conditions.md#thermocycler)|[经验](module-practices.md#thermocycler)|
|Magnetic Block|0专属控制方法；[共享用法](api-module-magnetic-block.md)|[机制/条件](module-conditions.md#magnetic-block)|[待补充入口](module-practices.md#magnetic-block)|
|Absorbance Plate Reader|6；[API](api-module-absorbance-plate-reader.md)|[机制/条件](module-conditions.md#absorbance-plate-reader)|[待补充入口](module-practices.md#absorbance-plate-reader)|
|Flex Stacker|13；[API](api-module-flex-stacker.md)|[机制/条件](module-conditions.md#flex-stacker)|[经验/示例](module-practices.md#flex-stacker)|

## 加载示例

以下各行是独立示例，只展示返回对应模块对象；不是默认装机、联合布局或完整协议。实际位置须由本次授权布局和installation核验，版本按目标API核对；适配器/耗材加载继续查共享API和实际安装关系。模块对象变量名可按任务调整。

|模块|示例|
|---|---|
|Heater-Shaker|`hs = protocol.load_module("heaterShakerModuleV1", "C1")`|
|Temperature Module|`temp = protocol.load_module("temperature module gen2", "D1")`|
|Thermocycler|`tc = protocol.load_module("thermocycler module gen2", "B1")`|
|Magnetic Block|`mag = protocol.load_module("magneticBlockV1", "B2")`|
|Absorbance Plate Reader|`reader = protocol.load_module("absorbanceReaderV1", "C3")`|
|Flex Stacker|`stacker = protocol.load_module("flexStackerModuleV1", "A4")`|

共享加载/模型/位置/耗材属性见[共享API](api-module-common.md)。`load_module`仍查api-layout.md；`Task`、等待任务与计时器见api-module-tasks.md。操作硬条件见module-conditions.md；用户装载/收尾经验见module-practices.md；安装占位继续只查installation.txt。

同步范围仅含Flex六类公开模块。当前edge源码另有API 2.31 VacuumModuleContext，超出本技能2.30基线，未收录为可用接口；HEPA/UV不在此六类Python模块上下文中，不凭名称杜撰控制方法。未收录设备仍反馈缺失。

官方说明与源码存在差异时：热震荡set_and_wait_for_shake_speed实际返回None并阻塞，不按旧说明当Task；set_shake_speed返回Task。热震荡温度范围区分API校验与物理可达，见module-conditions.md。

固定来源：https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_api/module_contexts.py

正文覆盖71个不重复的公开成员（共享9个、本类62个），另附8个源码补充成员并标明不可用/仅参考状态。并发配套另收录wait_for_tasks、create_timer及Task四个属性。原始源码成员说明保留英文以避免参数细节被摘要丢失；硬条件和经验路由用中文。
