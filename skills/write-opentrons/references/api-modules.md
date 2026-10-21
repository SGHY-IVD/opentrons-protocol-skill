# 模块API索引

基线API 2.30；2026-10-16同步。先按设备定位，只读所用成员及其共享类型，不一次读取所有模块。覆盖官方参考页公开的方法与属性，包括加载、运行、状态读取、停用及并发接口；已弃用参数保留标记，不能继续生成。

|模块|本类条目数|参考|
|---|---:|---|
|HeaterShakerContext|17|[API](api-module-heater-shaker.md)|
|TemperatureModuleContext|7|[API](api-module-temperature-module.md)|
|ThermocyclerContext|19|[API](api-module-thermocycler.md)|
|MagneticModuleContext|4|[API](api-module-magnetic-module.md)|
|MagneticBlockContext|0|[API](api-module-magnetic-block.md)|
|AbsorbanceReaderContext|6|[API](api-module-absorbance-plate-reader.md)|
|FlexStackerContext|13|[API](api-module-flex-stacker.md)|

共享加载/模型/位置/耗材属性见[共享API](api-module-common.md)。`load_module`仍查api-layout.md；`Task`、等待任务与计时器见api-module-tasks.md。操作硬条件见module-conditions.md；用户装载/收尾经验见module-practices.md；安装占位继续只查installation.txt。

同步范围以七类公开模块为准：Flex六类加OT-2 MagneticModule兼容参考。当前edge源码另有API 2.31 VacuumModuleContext，超出本技能2.30基线，未收录为可用接口；HEPA/UV不在此七类Python模块上下文中，不凭名称杜撰控制方法。未收录设备仍反馈缺失。

官方说明与源码存在差异时：热震荡set_and_wait_for_shake_speed实际返回None并阻塞，不按旧说明当Task；set_shake_speed返回Task。热震荡温度范围区分API校验与物理可达，见module-conditions.md。

固定来源：https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_api/module_contexts.py

正文覆盖75个不重复的公开成员（共享9个、本类66个），另附8个源码补充成员并标明不可用/仅参考状态。并发配套另收录wait_for_tasks、create_timer及Task四个属性。原始源码成员说明保留英文以避免参数细节被摘要丢失；硬条件和经验路由用中文。
