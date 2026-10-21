# 模块机制与硬性条件

只在使用对应设备时读其章节。接口签名/全部参数见api-modules索引；安装位置/堆叠关系仍唯一见installation.txt。用户操作习惯见module-practices。基线2.30，2026-10-16核对官方公开API及固定源码05b494ba81636978fb79f08bbc20468f94464d5c。

## Heater-Shaker

- 搬入/移出耗材须锁扣打开且停止震荡；上方移液前锁扣关闭、震荡停止。启动震荡前必须由close_labware_latch完成已知关闭，不以人工关闭的外观代替API确认。
- 开锁扣时不能正在震荡。idle_unknown是复位后的未知状态，不等于已知关闭；opening/closing为过渡状态，不等于完成。邻近移液/开锁扣避碰按API和安装关系核对，不把OT-2的邻位限制无差别推广到Flex。
- 速度API范围200–3000rpm（含边界）；停止用deactivate_shaker，不用set_shake_speed(0)。加热和震荡独立，停一个不会自动停另一个。
- 温度：官方产品额定37–95℃；API<2.25校验37≤T≤95；API≥2.25的现有校验代码接受0≤T≤95。它没有主动制冷，低于环境温度不可达；25℃不是统一API下限，室温也不是固定25℃。请求低于环境或无法确认能否达到时说明边界，不改写为能制冷的模块、不等待一个已知不可达目标。
- set_and_wait_for_temperature、set_and_wait_for_shake_speed阻塞到目标，随后仍维持温控/震荡；set_target_temperature和set_shake_speed在2.27+返回Task，需在依赖目标到达的步骤前等待。到速不等于已完成所需振荡时长，到温不等于已完成孵育。
- 源码open_labware_latch在需要避碰时会归位相关轴；不得假定重复调用没有运动代价。停温控仅停止加热，不能当作已冷却到室温。

## Temperature Module

目标4–95℃；set_temperature阻塞到目标；start_set_temperature在2.27+返回Task并发运行。deactivate停止加热/制冷并关闭风扇，但实际温度不会瞬时回室温。无模块盖/耗材锁扣API，不为它套热循环或热震荡的开关流程。

## Thermocycler

- 模块盖打开后才能装卸板或从上方操作；盖和耗材自带板盖是两个对象，不混用open_lid与move_lid。关闭前确认无枪头/抓手留在盖的运动区域，不把开盖后的未知枪尖位置仍记为原孔。
- 块温4–99℃；盖温37–110℃。升降温速率、hold及block_max_volume见对应API条目；block_max_volume是单孔最大液量，不是整板总量。API2.27+部分温度方法可从液量跟踪取值，缺失回退25µL；诊断时核对具体方法，不将回退25视为实际样品量。
- 块和盖温控分别管理；deactivate_block只停块，deactivate_lid只停盖，deactivate同时停二者。开盖不等于停温控，停温控不等于温度已降到可接触范围。
- 同步方法等待目标/程序完成；start_*返回Task，在依赖其结果或收尾前处理完成条件，不以发出任务当完成循环。
- 固定源码thermocycler/open_lid.py执行开盖前先home X/Y及挂载轴，不归位活塞轴，并清除移液器位置缓存。重复open_lid因此可能反复引发实际运动；不能删除必要的避碰步骤，而应避免没有状态变化需求的重复开盖命令。

## 其他模块的操作边界

- Flex MagneticBlock为被动磁体，无engage/disengage；主动MagneticModule用于OT-2，不允许借其API控制Flex磁力架。主动模块高度参数及被移除height用法见其API，不猜磁吸时间。
- AbsorbanceReader使用抓手开关盖；初始化前要求在协议中显式close_lid，即使开局外观已闭合也不能当冗余删除。initialize区分single/multi和波长列表；参考波长仅single，常规LED波长/定制硬件范围见API。读取前满足初始化和闭盖条件。模拟读数为0且不写CSV，不能当实测结果。
- FlexStacker库存声明必须与实物相符；store/retrieve前核对当前取放位、库存及容量，具体同质耗材/盖/适配器限制见set_stored_labware_items等条目。人工fill/empty后按实际结果更新，不将先前库存继续当真。此处不自动新增模块经验流程。

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
