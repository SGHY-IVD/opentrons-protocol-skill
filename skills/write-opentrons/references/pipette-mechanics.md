# 移液器状态与体积核算：排查参考

仅在余液/空气段、容量、push_out报错、活塞复位或体积模式难以解释时查阅；不列入常规生成必读，不把本文件变为协议中的运行时计算器。用户经验默认仍唯一见operations.md、rates.md；本文件解释官方机制，不自动覆盖经验参数或自动添加动作。

## 查用索引

- 容量/空气/实际排液量：看“分开记账”和“状态演算”。
- push_out与blow_out：看“活塞位置”和“源码快照”。
- 模式切换/看似空头却报错：看“空与准备状态”。
- 版本冲突：看“证据与适用范围”。

## 判定速查：先查问题，不顺序通读

|遇到的问题|判定依据|结论/边界|证据类别|
|---|---|---|---|
|空气是否占容量？|枪头工作容量与已吸入液体+空气|占容量；目标孔只增加实际排出的液体|官方源码机制|
|current_volume>0是否有液体？|检查液体/空气段组成|可能只有空气，不能仅凭总数判断|官方源码机制|
|current_volume=0能否立即吸液？|枪头状态、活塞准备状态及上一动作|零值不等于准备完成，也不证明实际无残留|官方源码机制|
|dispense(V)是否给孔加了V液体？|从枪尖端逐段扣除空气/液体|只有液体部分计入目标孔|官方源码机制|
|液体排完能否非零push_out？|是否总占用排净，再核对额外行程与技能位置条件|剩空气也不能直接当full dispense；经验位置条件见operations|官方机制+用户规则引用|
|push_out能否补充吸液容量？|额外行程发生在正常排净之后|不能，和预先吸入的空气/保留液不是一回事|官方源码机制|
|切换模式后能否按标称量程吸液？|当前模式上限与枪头容量取较小值|还需扣除当前占用，低模式不等于标称全量程|官方源码机制|
|一吸多分最后目标能否吹空？|按经验策略仍留尾液|复用operations的余量规则，不在此另设默认|用户规则引用|

后续沉淀条目统一采用：问题、判定依据、结论、适用条件/例外、证据来源。官方实现与用户实测经验分开标识；未核对的猜测标“待验证”，不能作为硬性依据。只保存能解释状态或消除歧义的知识，不把一次实验特例泛化。用户经验数值只引用其原始规则，不重复维护。

## 分开记账

以下体积均为每通道µL；共享源孔消耗还需乘实际作用通道数。

|量|含义|不能据此推断|
|---|---|---|
|L|程序跟踪的液体体积|不代表实测液量，也不证明无残膜/滴漏|
|A|由air_gap明确跟踪的空气体积|不是液体，但占吸入容量|
|Q=L+A|正常可追踪状态下的累计吸入占用|不是实际向目标孔加入的液量|
|C=min(当前模式最大量, 枪头容量)|工作容量|不能再叠加push_out或blow_out行程作为吸液容量|
|C−Q|正常已准备/可追踪状态下还能吸入的量|未知/吹出后的状态不可只靠该算式认定可吸液|

核对源码：InstrumentContext.current_volume经engine.get_current_volume读取get_aspirated_volume，它返回fluid stack总量，包含空气。公开文档把它简称液量，排查时以此源码链辨别；不能写current_volume>0就断言一定还有液体。反之current_volume=0也不证明已准备、已装枪头或实物无残液：底层None/未装头也可能在公共属性映射为0。

API 2.22起air_gap以AIR段进入账本；排入孔时只增加实际弹出的LIQUID段体积。它依旧占容量，不能误解为“新版air_gap不占体积”。用普通aspirate在空气中吸入不会因此自动得到正确AIR标签，不能混同air_gap。更早API语义不同，本技能基线2.30不沿用旧算式。

## 状态演算

官方fluid_stack按后吸先出处理，靠近枪尖的最后吸入段先排。只知道L和A合计还不够，须保留段顺序；这是排查用逻辑模型，不预测真实气泡移动/混合。

|从空头开始的动作|剩余L|剩余A|Q/current_volume正常值|目标收到液体|
|---|---:|---:|---:|---:|
|aspirate(100)|100|0|100|0|
|随后air_gap(10)|100|10|110|0|
|随后dispense(50,push_out=0)|60|0|60|40|
|再dispense(60,push_out=0)|0|0|0|60|

若先air_gap(10)，再aspirate(100)，则先dispense(100,push_out=0)排出100液体，留下10空气；虽然L=0，但Q=10，不能按“液体已经排完”就把该步当full dispense。多段空气/液体同理逐段扣除；普通无空气时才简化为吸多少加多少、排多少减多少。

## 活塞位置与换算

这些是移液器内部活塞坐标，不是well.top/bottom，也不是枪尖甲板Z坐标。

|位置|含义|
|---|---|
|plunger top|配置的活塞上行端；不是吸液孔top|
|plunger bottom|正常排净/开始吸液的基准；正常吸入后活塞离开此点|
|push_out终点|正常排净后，在bottom基础上再推进一段；push_out单位µL，是等效空气排量|
|blowout|配置的吹出终点；高层blow_out()无体积参数，默认走到此位置|
|drop|弃头机构相关位置；不是可用吸液区间|

源码plunger_position在零修正量时使用p=bottom−V/k(V,action)。k是相应枪头/模式/动作的µL/mm换算函数，吸排可能用分段标定；不能把标称容量按整段行程简单线性摊分。本快照Flex的blowout换算使用shaftULperMM：push_out附加行程=P/shaftULperMM，允许范围不超过blowout−bottom。因此最大等效push_out=(blowout−bottom)×shaftULperMM；它不是能额外吸取的液量。

blow_out没有统一的固定“额外多少µL”：终点由配置决定，起点可能不同；下表最大push_out只指从bottom到blowout的等效行程。不要通过超量dispense模拟吹出，不把底层硬件volume参数误加到高层blow_out接口。

## 源码快照：模式、位置和官方默认

数值来源pipette-mechanics-data.json，选取固定提交中的各型号最新3.x硬件定义；不是声明用户设备正好为该硬件版本。位置单位mm，体积µL。诊断表只记录官方数值，不采用用户经验push_out默认。

|型号/硬件修订|模式|定义min–max|top / bottom / blowout / drop|shaft µL/mm|最大等效push_out|官方各枪头默认push_out|
|---|---|---|---|---:|---:|---|
|eight_channel p1000 3_6|default|5–1000|0.0 / 71.5 / 76.5 / 91.5|15.904|79.52|t50=7, t200=5, t1000=20|
|eight_channel p50 3_5|default|5–50|0 / 71.5 / 76.5 / 91.5|0.785|3.925|t20=2, t50=2|
|eight_channel p50 3_5|lowVolumeDefault|0.5–30|0 / 61.5 / 76.5 / 91.5|0.785|11.775|t20=7, t50=7|
|ninety_six_channel p1000 3_7|default|5–1000|0.5 / 68.5 / 73.5 / 80|15.904|79.52|t50=7, t200=5, t1000=20|
|ninety_six_channel p200 3_3|default|0.5–200|0.5 / 68.5 / 73.5 / 80|3.14159|15.70795|t20=2, t50=5, t200=5|
|single_channel p1000 3_7|default|5–1000|0.0 / 71.5 / 76.5 / 90.5|15.904|79.52|t50=7, t200=5, t1000=20|
|single_channel p50 3_7|default|5–50|0 / 71.5 / 76.5 / 90.5|0.785|3.925|t20=3.5, t50=2|
|single_channel p50 3_7|lowVolumeDefault|0.5–30|0 / 61.5 / 76.5 / 90.5|0.785|11.775|t20=3.5, t50=7|

P50的低体积模式最大30µL；装20µL头则有效最大仍是20µL，不能因为切模式而吸30。常规模式最大50。官方volume-modes说明页列低模式1–4.9、常规5–50，低模式最小1；本次最新硬件JSON低模式minVolume却是0.5。这是明确版本/资料差异，不能由诊断表自动放宽现有脚本最小量程；须匹配实际安装版本与硬件配置。其他快照定义最大P1000=1000、P96/200=200，也受实际枪头容量限制。

文档将P50最大push_out列为3.9/11.7、P1000列79.5；源码轴截面积×行程得到3.925/11.775/79.52。差异保留，日常不贴极限使用，不把源码小数自动升级成通用允许值。96/200的对应派生值15.70795来自快照计算，不伪称为官网公开规格。

## 空与准备状态

- 正常排净且push_out=0：Q=0，活塞可在bottom。是否准备仍结合命令历史和准备状态，不仅看一个数。
- 非零push_out：仅full dispense允许，硬件还校验额外行程。这里full dispense针对总吸入占用，包含空气；L=0但仍有空气也不等于Q=0。
- blow_out后底层内容状态可能为未知/不安全状态None，同时公共current_volume显示0。它不是“已准备好继续吸液”的证明。
- prepare_to_aspirate恢复到bottom；不用于消除有液体/空气的未知状态。技能仍按既有下一次吸液前、空头、源孔top规则执行。
- configure_for_volume的前置检查读取current_volume：有空气占用也可能被“contains liquid”错误拦截；不可因L=0就切模式。当前实现还可能先移到当前孔top，所以错误信息、位置变化应分别追踪。
- move_to/touch_tip不会主动改变已记录吸入体积；若实机液滴脱落，它不会因此自动变成一次定量dispense记录。报错/过压/人工干预后不可假定命令全部成功、继续用理想账本。
- 模拟层与真实硬件的检查不完全等价；本次核对发现执行器仍存在最大push_out检查的TODO，真实硬件另有行程检查，因此模拟通过不证明最大值合法。

## 排查顺序

先确认API/设备版本、型号、硬件修订、枪头与模式，再从最近可信状态按命令重放：液体/空气段顺序→总容量→实际排出液量→full dispense→额外行程→准备状态。把“没有液体”“没有累计吸入占用”“已准备吸液”“物理完全无残留”分别回答。只回查与异常有关的命令，不给正常脚本增添底层坐标控制。

## 证据与适用范围

核对日期2026-10-16；固定源码提交：05b494ba81636978fb79f08bbc20468f94464d5c。此为edge源码快照，不保证等同当前已发布/设备安装版本。日常离线查本参考；需要其他修订时反馈缺口，只有明确升级才再查官方。

官方文档：
- https://docs.opentrons.com/python-api/reference/instruments/
- https://docs.opentrons.com/python-api/building-block-commands/liquids/
- https://docs.opentrons.com/python-api/pipettes/volume-modes/

源码证据（均为固定提交）：
- [api/src/opentrons/protocol_api/instrument_context.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_api/instrument_context.py)
- [api/src/opentrons/protocol_api/core/engine/instrument.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_api/core/engine/instrument.py)
- [api/src/opentrons/protocol_engine/state/pipettes.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_engine/state/pipettes.py)
- [api/src/opentrons/protocol_engine/state/fluid_stack.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_engine/state/fluid_stack.py)
- [api/src/opentrons/protocol_engine/commands/air_gap_in_place.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_engine/commands/air_gap_in_place.py)
- [api/src/opentrons/protocol_engine/commands/dispense.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_engine/commands/dispense.py)
- [api/src/opentrons/protocol_engine/execution/pipetting.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/protocol_engine/execution/pipetting.py)
- [api/src/opentrons/hardware_control/instruments/ot3/pipette_handler.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/hardware_control/instruments/ot3/pipette_handler.py)
- [api/src/opentrons/hardware_control/instruments/ot3/pipette.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/hardware_control/instruments/ot3/pipette.py)
- [api/src/opentrons/hardware_control/ot3api.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/api/src/opentrons/hardware_control/ot3api.py)
- [shared-data/python/opentrons_shared_data/pipette/ul_per_mm.py](https://github.com/Opentrons/opentrons/blob/05b494ba81636978fb79f08bbc20468f94464d5c/shared-data/python/opentrons_shared_data/pipette/ul_per_mm.py)

硬件及模式JSON路径、原文SHA256保存在pipette-mechanics-data.json；取同一提交对应路径，不混用不同硬件修订。
