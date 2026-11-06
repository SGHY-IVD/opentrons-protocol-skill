# Absorbance Plate Reader

[模块索引](api-modules.md) · [API与加载](api-module-absorbance-plate-reader.md) · [本设备经验](module-practices-absorbance-plate-reader.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

吸光度读板机测量兼容孔板各孔的吸光度。模块盖的开合由Flex抓手执行，使用读板机须配备抓手。

### 易混淆点

- **初始化与读板。** 初始化针对空腔，测量在装板后进行。各阶段的盖状态按下面的操作条件核对。
- **模拟与实测。** 模拟读数为0且不生成CSV。实测值由设备读取，CSV文件按实际导出配置生成。

### 条件约束

不在协议中或协议外手动搬动模块盖。初始化时模块内须无孔板，并在协议中显式close_lid，即使开局外观已闭合也不能当冗余删除；先空腔闭盖→initialize→开盖搬入孔板→闭盖→read。初始化后按此顺序开盖装板不需要重新初始化；初始化配置用于后续read。initialize区分single/multi，参考波长仅single；本业务标准波长范围唯一见API。读取前满足初始化和闭盖条件，板型及安装高度边界查installation，选板建议见[读板机经验](module-practices-absorbance-plate-reader.md#默认选板与其他品牌)。

读板流程增补来源：官方v10.0.0 commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af，docs/python-api/docs/modules/absorbance-plate-reader.md；2026-11-04核对空腔初始化、盖控制及装板读数示例。未新增API。
