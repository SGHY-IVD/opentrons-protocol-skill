# Temperature Module

[模块索引](api-modules.md) · [API与加载](api-module-temperature-module.md) · [本设备经验](module-practices-temperature-module.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

温控模块通过承载平台给耗材加热或制冷，制冷时由风扇向外排热。低于环境温度的冷表面可能出现冷凝，是否发生取决于室温、相对湿度及露点。

### 易混淆点

- **平台温度与样品温度。** API设定和读取的是平台温度。样品的实际温度还受铝块、耗材和液量影响，需按本次实验条件判断。
- **阻塞等待与并发变温。** set_temperature()等到目标温度才返回。start_set_temperature()立即返回，API 2.27起返回Task。
- **不同模块的开合操作。** 温控模块接口用于平台温控。热盖和耗材锁扣的开合分别查热循环及热震荡模块。

### 条件约束

目标4–95℃。deactivate停止加热/制冷并关闭风扇，模块温度不会瞬时回到室温。
保持排风通畅；安装位置与朝向唯一查installation的温控条目，制冷前侧盖准备及低温暂存建议见[温控经验](module-practices-temperature-module.md)。
安装和运行环境保持低振动及温湿度稳定，避开直射阳光，以及可能造成显著温度或湿度变化的空调气流。

温控补充来源：2026-11-04查证官方[温度特性](https://docs.opentrons.com/temperature-module/product-specs/#temperature-profile)及[低温冷凝说明](https://docs.opentrons.com/temperature-module/compliance/#environmental-conditions)；在线手册未固定发布修订，仅补上述硬件机制，不据其改变API基线。安装朝向的固定v10.0.0来源在installation维护。
