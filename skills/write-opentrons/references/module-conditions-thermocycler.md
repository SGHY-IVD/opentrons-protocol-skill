# Thermocycler

[模块索引](api-modules.md) · [API与加载](api-module-thermocycler.md) · [本设备经验](module-practices-thermocycler.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

块和盖温控分别管理；profile只控制块温，不代替热盖温度设置。热盖没有主动制冷，仅被动降温。模块盖与耗材自带板盖是两个对象，不混用open_lid与move_lid。

### 条件约束

- 模块盖打开后才能装卸板或从上方操作。关闭前确认无枪头/抓手留在盖的运动区域，不把开盖后的未知枪尖位置仍记为原孔。
- 块温4–99℃；盖温37–110℃。升降温速率、hold及block_max_volume见对应API条目；block_max_volume是单孔最大液量，不是整板总量。API2.27+部分温度方法可从液量跟踪取值，缺失回退25µL；诊断时核对具体方法，不将回退25视为实际样品量。
- deactivate_block只停块，deactivate_lid只停盖，deactivate同时停二者。开盖不等于停温控，停温控不等于温度已降到可接触范围。
- 官方要求样品块回到idle temperature后再开盖取样；须按本次实验安排冷却并确认取板条件，不能只凭deactivate或温控状态idle判定已经冷却。官方未给统一的安全触摸温度或等待时长，热盖密封处打开后仍可能有余热。
- 板温低于当前环境温度时不得持续超过2小时，以免冷凝影响性能或损坏模块。此限制同样适用于PCR后保持及pause等待用户的方案；pause本身不提供自动超时或停用保证。
- GEN2密封方案须与实物匹配：Opentrons Tough PCR Auto-sealing Lid与模块热盖上的可重复橡胶密封垫不得同时使用，采用一次性盖前取下该橡胶垫。可重复密封垫装在模块盖上而非孔板上，每次使用前按官方说明清洁消毒；不能仅设置热盖温度就当作已完成实物密封。
- 同步方法等待目标/程序完成；start_*返回Task，在依赖其结果或收尾前处理完成条件，不以发出任务当完成循环。
- 固定源码thermocycler/open_lid.py执行开盖前先home X/Y及挂载轴，不归位活塞轴，并清除移液器位置缓存。重复open_lid因此可能反复引发实际运动；不能删除必要的避碰步骤，而应避免没有状态变化需求的重复开盖命令。

热循环增补来源：2026-11-04在线核对官方[Python用法](https://docs.opentrons.com/python-api/modules/thermocycler/#thermocycler-profiles)、[低温与取板条件](https://docs.opentrons.com/thermocycler/compliance/)、[GEN2密封方案](https://docs.opentrons.com/thermocycler/lid-seals/)及[Flex密封垫使用要求](https://docs.opentrons.com/flex/modules/thermocycler/#thermocycler-lids-and-seals)。在线内容未固定修订，仅补上述机制与使用条件，不升级API、添加耗材加载名或自动搬运方案。
