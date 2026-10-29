# 模块机制与条件约束

按设备定位：[热震荡](#heater-shaker) · [温控](#temperature-module) · [热循环](#thermocycler) · [磁力架](#magnetic-block) · [读板机](#absorbance-plate-reader) · [Stacker](#flex-stacker)

按[模块索引](api-modules.md)只读本次设备的“硬件与机制”和“条件约束”；即使只核对布局，涉及模块承载位、内部库存或状态含义时也适用。各模块使用相同分类；没有额外条目时保留明确入口，不推断设备缺少能力。名称/型号查catalog，台面安装及已收录适配关系唯一查installation；API签名/版本查对应api-module文件，操作经验查module-practices。本文件不另建槽位或夹具表。

既有非Stacker条目保持API 2.30范围，来源为2026-10-16核对的官方公开API及固定源码05b494ba81636978fb79f08bbc20468f94464d5c；本次只重新分类。Stacker增补依据见该节，未升级API基线。

## Heater-Shaker

### 硬件与机制

具有加热、震荡和耗材锁扣；加热与震荡独立，停一个不自动停另一个。没有主动制冷能力，低于环境温度不可达。

### 条件约束

- 搬入/移出耗材须锁扣打开且停止震荡；上方移液前锁扣关闭、震荡停止。启动震荡前必须由close_labware_latch完成已知关闭，不以人工关闭的外观代替API确认。
- 开锁扣时不能正在震荡。idle_unknown是复位后的未知状态，不等于已知关闭；opening/closing为过渡状态，不等于完成。邻近移液/开锁扣避碰按API和安装关系核对，仅采用已核对的Flex邻位限制。
- 速度API范围200–3000rpm（含边界）；停止用deactivate_shaker，不用set_shake_speed(0)。
- 温度：官方产品额定37–95℃；API<2.25校验37≤T≤95；API≥2.25的现有校验代码接受0≤T≤95。25℃不是统一API下限，室温也不是固定25℃。请求低于环境或无法确认能否达到时说明边界，不改写为能制冷的模块、不等待一个已知不可达目标。
- set_and_wait_for_temperature、set_and_wait_for_shake_speed阻塞到目标，随后仍维持温控/震荡；set_target_temperature和set_shake_speed在2.27+返回Task，需在依赖目标到达的步骤前等待。到速不等于已完成所需振荡时长，到温不等于已完成孵育。
- 源码open_labware_latch在需要避碰时会归位相关轴；不得假定重复调用没有运动代价。停温控仅停止加热，不能当作已冷却到室温。

## Temperature Module

### 硬件与机制

具有加热/制冷功能及风扇；没有模块盖或耗材锁扣API，不套用热循环或热震荡的开关流程。

### 条件约束

目标4–95℃；set_temperature阻塞到目标；start_set_temperature在2.27+返回Task并发运行。deactivate停止加热/制冷并关闭风扇，但实际温度不会瞬时回室温。

## Thermocycler

### 硬件与机制

块和盖温控分别管理；模块盖与耗材自带板盖是两个对象，不混用open_lid与move_lid。

### 条件约束

- 模块盖打开后才能装卸板或从上方操作。关闭前确认无枪头/抓手留在盖的运动区域，不把开盖后的未知枪尖位置仍记为原孔。
- 块温4–99℃；盖温37–110℃。升降温速率、hold及block_max_volume见对应API条目；block_max_volume是单孔最大液量，不是整板总量。API2.27+部分温度方法可从液量跟踪取值，缺失回退25µL；诊断时核对具体方法，不将回退25视为实际样品量。
- deactivate_block只停块，deactivate_lid只停盖，deactivate同时停二者。开盖不等于停温控，停温控不等于温度已降到可接触范围。
- 同步方法等待目标/程序完成；start_*返回Task，在依赖其结果或收尾前处理完成条件，不以发出任务当完成循环。
- 固定源码thermocycler/open_lid.py执行开盖前先home X/Y及挂载轴，不归位活塞轴，并清除移液器位置缓存。重复open_lid因此可能反复引发实际运动；不能删除必要的避碰步骤，而应避免没有状态变化需求的重复开盖命令。

## Magnetic Block

### 硬件与机制

Flex MagneticBlock为被动磁体，无engage/disengage；本类没有专属控制方法，仍可使用共享加载及属性接口。

### 条件约束

不得生成主动磁力模块控制API；磁吸时间按实验条件核对，不猜补。模块本体与适用孔板的搬运身份按installation及搬运API区分。

## Absorbance Plate Reader

### 硬件与机制

用于吸光度读取，模块盖由抓手开关；模拟读数为0且不写CSV，不能当实测结果。

### 条件约束

初始化前要求在协议中显式close_lid，即使开局外观已闭合也不能当冗余删除。initialize区分single/multi和波长列表；参考波长仅single，常规LED波长/定制硬件范围见API。读取前满足初始化和闭盖条件。

## Flex Stacker

### 硬件与机制

- 分别记录仓内（hopper）的同质库存与shuttle穿梭托盘上的当前耗材；声明仓内类型不等于托盘上已经有该耗材，托盘占用也不自动计入仓内库存。用户说“A4装Stacker，A4放枪头盒”时，按该模块托盘承载枪头盒理解并核对，而非两个独立台面对象争位；明确说“仓内”时按库存理解。此语义属于模块，台面安装仍查installation。
- 仓内一次配置一种主耗材及相应盖/适配器组合。shuttle可临时承载与仓内不同类型的适用labware；“同质库存”限制不能直接套到临时承载，但这不表示任意尺寸、定义或抓手组合均兼容，也不表示它可存入当前仓内。使用模块对象表达其承载位置，不新建一个普通A4槽位或虚构shuttle加载API。
- 装料门允许人工直接预装仓内耗材。set_stored_labware/set_stored_labware_items声明初始库存；这些调用不等于抓手已逐件搬入或设备已识别实物。retrieve把仓内最底层一件移到托盘；store把托盘上的匹配组合存到仓内底部。库存列表首项为下一次取出对象。

### 条件约束

- 本节仓内存取/库存专属接口最低API2.25；模块加载及继承的共享成员按各自契约核对，不将2.25概括成全部加载能力的统一下限。库存声明的型号、数量、盖/适配器组合必须与实物一致。实际同质性按定义身份及完整组合核对，不能只凭“都是枪头盒/孔板”视为同类。
- 配置仓内库存前移走原先当普通承载位加载在托盘上的耗材，按官方指南组织顺序；重新配置类型前，仓内须已知为空，不能用重新声明掩盖原有库存。未配置库存不妨碍按共享API使用适用的托盘承载能力，但不能retrieve/store。
- retrieve前须已配置、有至少一件仓内库存且托盘为空；取出后仓内减一、托盘被占用，搬离后才清空托盘。即使托盘上的耗材与库存同型，也不能在仍占用时继续取出。
- store前须已配置、有剩余仓内容量，且托盘上的主耗材、盖/适配器整套组合与声明一致；缺盖、缺适配器或类型/定义不匹配均不能按该配置存入。存入成功后仓内加一、托盘清空；仅把物品移到托盘不代表已经存入。
- Flex枪头盒进入仓内堆叠存储时，按官方正确装载要求配置并实物带上兼容盖子，包括拟存回的空盒；交互时可简短提醒备盖、带盖装仓，后续取头前按搬运/板盖API处理。此条件不泛化为“所有临时放在shuttle的耗材必须带盖”。官方指南要求带盖；本次核对v10.0.0源码未发现一律拒绝无盖声明的校验，不将该要求表述为所有API版本必报错。
- 容量按实际主耗材/盖/适配器高度与堆叠重叠量核对，不统一写死最大件数。fill/empty是暂停后的人工补入/移出，不是store/retrieve的自动动作替代；变更后按实际结果更新库存，已有无关状态不凭空清除。具体参数与count含义继续查API。
- 仓内可双向存取；不得将“供料常用取出”推成只能取不能存。完整搬运、抓手/盖、当前托盘占用和后续动作仍按各自条件核对，不把安装可放等同于立即可执行存取。

Stacker增补来源（2026-10-29核对；API范围≤2.30）：官方v10.0.0，commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af：
- docs/python-api/docs/modules/flex-stacker.md，blob 17608d7e6128ce5c2d9dc8d351f22daef801742a：结构、声明、托盘临时使用、带盖及示例。
- api/src/opentrons/protocol_api/module_contexts.py，blob 62aa59d03ad57ab9fb7b71a47cd15e0608b21b0f：共享继承、set/store/retrieve/get_stored_labware契约；接口签名仍唯一维护于api-module-flex-stacker/common。
- api/src/opentrons/protocol_engine/commands/flex_stacker/retrieve.py（2cb205d984955b720fd76fddd5dfb634337f58b8）、store.py（69092dc839aac9f2ad2f22dd247547096fb44cc7）、set_stored_labware.py（229b5b6d682b038e1a907b6b028d7157175318ff）：取出为空托盘、存入整套匹配及重新声明前仓内为空。
- api/src/opentrons/protocol_engine/commands/load_labware.py（c580faffadc5e6adafe6bf92401c9e9eb7905d7c）、move_labware.py（cbbe632ccca1e6ef7eff6f4a7bb586d4ac8af27d）、state/geometry.py（68357e61b45daf79d956d0c13f41ea7bea0584bc）：模块承载与占用校验不等同于仓内存入校验；异类临时承载仍查实际定义及动作条件。
- api/src/opentrons/protocol_engine/state/labware.py（dedeee6786ddde009280527ccdc6c969bf633d16）raise_if_stacker_labware_pool_is_not_valid与commands/flex_stacker/common.py（c2cdd567e5445cc002ac225f9bfa35698fb0304b）：未发现无盖一律报错校验，不据此取消官方带盖装仓要求。
- 官方装载说明 https://docs.opentrons.com/stacker/loading-labware/ （在线核对，未固定内容版本）：装料门人工装入、堆叠与人工取出；不固定门的方向。不将源码阅读当SDK模拟或实机验证。

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
