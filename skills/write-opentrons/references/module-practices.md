# 模块操作经验与使用示例

按[模块索引](api-modules.md)定位当前设备。机制和条件唯一查module-conditions，API签名/参数查对应API文件，静态安装唯一查installation。经验应写明场景、来源、条件及验证程度；建议不自动升格为硬性约束，没有额外经验也不阻止合法用法。

|本次设备|经验与完整示例|
|---|---|
|热震荡|[Heater-Shaker](module-practices-heater-shaker.md)|
|温控|[Temperature Module](module-practices-temperature-module.md)|
|热循环|[Thermocycler](module-practices-thermocycler.md)|
|磁力架|[Magnetic Block](module-practices-magnetic-block.md)|
|读板机|[Absorbance Plate Reader](module-practices-absorbance-plate-reader.md)|
|Stacker|[Flex Stacker](module-practices-flex-stacker.md)|
|第三方倾斜模块|[第三方倾斜模块](module-practices-tilt.md)|
|第三方正压模块|[第三方正压模块](module-practices-positive-pressure.md)|

热震荡、温控和热循环的共用经验仅在相应场景触发时读取：[开始装载](module-practices-common.md#开始装载) · [状态组织](module-practices-common.md#运行中按已知状态组织) · [并发选择](module-practices-common.md#按等待对象选择并发) · [正常结束与持续保温](module-practices-common.md#正常结束与持续保温)。各设备页已提供对应直达，不要求其他设备读取共用文件。
