# Temperature Module

[模块索引](api-modules.md) · [API与加载](api-module-temperature-module.md) · [本设备经验](module-practices-temperature-module.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

具有加热/制冷功能及风扇，制冷时需要向外排热；没有模块盖或耗材锁扣API，不套用热循环或热震荡的开关流程。目标与API当前温度对应模块平台，铝块、耗材和液量会影响实际样品温度，不能把模块到温等同于液体实测到温。
低于环境温度的冷表面可能出现冷凝，是否发生与室温、相对湿度及露点有关，不设一个统一的必然冷凝温度或时长。

### 条件约束

目标4–95℃；set_temperature阻塞到目标；start_set_temperature在2.27+返回Task并发运行。deactivate停止加热/制冷并关闭风扇，但实际温度不会瞬时回室温。
保持排风通畅；安装位置与朝向唯一查installation的温控条目，制冷前侧盖准备及低温暂存建议见[温控经验](module-practices-temperature-module.md)。
安装和运行环境保持低振动及温湿度稳定，避开直射阳光，以及可能造成显著温度或湿度变化的空调气流。

温控补充来源：2026-11-04查证官方[温度特性](https://docs.opentrons.com/temperature-module/product-specs/#temperature-profile)及[低温冷凝说明](https://docs.opentrons.com/temperature-module/compliance/#environmental-conditions)；在线手册未固定发布修订，仅补上述硬件机制，不据其改变API基线。安装朝向的固定v10.0.0来源在installation维护。
