# 模块条件的来源与范围

按需查证来源与覆盖边界；实际动作条件从[设备索引](module-conditions.md)直达，不要求各模块任务通读本文件。

既有官方条目保持API 2.30范围，来源为2026-10-16核对的官方公开API及固定源码05b494ba81636978fb79f08bbc20468f94464d5c；各模块后续增补依据在对应节注明，未升级API基线。

## 来源与边界

接口及原始说明：各api-module-*.md固定源码与官方参考链接。
- https://docs.opentrons.com/heater-shaker/product-specs/
- https://docs.opentrons.com/python-api/reference/heater-shaker/
- https://docs.opentrons.com/python-api/reference/temperature-module/
- https://docs.opentrons.com/python-api/reference/thermocycler/
- https://docs.opentrons.com/python-api/modules/thermocycler/
- https://docs.opentrons.com/python-api/reference/absorbance-plate-reader/
- 固定源码api/src/opentrons/protocol_api/module_validation_and_errors.py：热震荡温度及转速边界。
- 固定源码api/src/opentrons/protocol_engine/commands/thermocycler/open_lid.py、heater_shaker/open_labware_latch.py：避碰归位及位置缓存。

这不是对所有固件互锁的穷尽清单；缺少条件或设备版本不符时报告具体缺口，不声称框架覆盖了官方全部底层校验。
