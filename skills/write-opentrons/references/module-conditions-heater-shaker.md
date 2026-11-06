# Heater-Shaker

[模块索引](api-modules.md) · [API与加载](api-module-heater-shaker.md) · [本设备经验](module-practices-heater-shaker.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

热震荡模块把平台加热和震荡集成在一起，由可开合的锁扣固定耗材。可按实验需要单独加热、单独震荡或同时进行。

### 易混淆点

- **加热与震荡状态。** 两项分别控制。停止其中一项时，另一项可按原设定继续运行。
- **设置低温与主动制冷。** 模块主动加热，降温依靠环境散热。低于环境温度的目标无法由该模块达到。
- **达到设定值与完成处理。** 到温、到速表示模块达到对应设定值，孵育和震荡时长仍按实验安排计时。

### 条件约束

- 搬入/移出耗材须锁扣打开且停止震荡；上方移液前锁扣关闭、震荡停止。启动震荡前必须由close_labware_latch完成已知关闭，不以人工关闭的外观代替API确认。
- 开锁扣时不能正在震荡。idle_unknown是复位后的未知状态，不等于已知关闭；opening/closing为过渡状态，不等于完成。邻近移液/开锁扣避碰按API和安装关系核对，仅采用已核对的Flex邻位限制。
- 速度API范围200–3000rpm（含边界）；停止用deactivate_shaker，不用set_shake_speed(0)。
- 温度：官方产品额定37–95℃；API<2.25校验37≤T≤95；API≥2.25的现有校验代码接受0≤T≤95。25℃不是统一API下限，室温也不是固定25℃。请求低于环境或无法确认能否达到时说明边界，不改写为能制冷的模块、不等待一个已知不可达目标。
- set_and_wait_for_temperature、set_and_wait_for_shake_speed阻塞到目标，随后仍维持温控/震荡；set_target_temperature和set_shake_speed在2.27+返回Task，需在依赖目标到达的步骤前等待。
- 源码open_labware_latch在需要避碰时会归位相关轴；不得假定重复调用没有运动代价。停温控仅停止加热，不能当作已冷却到室温。
