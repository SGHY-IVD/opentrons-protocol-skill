# Magnetic Block

[模块索引](api-modules.md) · [API与加载](api-module-magnetic-block.md) · [本设备经验](module-practices-magnetic-block.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

Flex磁力架通过固定磁体吸附兼容孔板内的磁珠，用于磁珠分离。

磁体固定于弹簧支撑底座（spring-loaded bed），官方说明其用于帮助保持磁力架与移液器之间的公差配合。来源：2026-11-04核对官方[磁体结构说明](https://docs.opentrons.com/flex/modules/magnetic-block/#magnetic-components)；仅记录硬件机制，不据此给出允许下压量或最低吸液高度。

### 易混淆点

**磁吸由孔板位置决定。** Flex磁力架是被动磁体。协议通过搬入、搬出孔板安排磁吸阶段，模块对象可用共享加载及属性接口。

### 条件约束

不得生成engage()、disengage()等主动磁力模块控制API；磁吸时间按实验条件核对，不猜补。磁力架本体不当作普通可抓手搬运耗材；模块本体与适用孔板的搬运身份分别按安装关系及搬运API核对。
