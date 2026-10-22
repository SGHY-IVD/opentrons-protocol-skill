---
name: write-opentrons
description: 按用户实验需求、Flex配置和维护的移液经验编写、修改及检查Opentrons Python协议。用于客户SOP转代码、液量与液面跟随、流速查询、模块和耗材加载、抓手搬运及手写混匀；信息不足时提供完整描述示例，按用户补充及已说明的推荐值生成，仅查维护的API和安装关系。
---

# Opentrons代码助手

规则版本：2026-10-22.6（交付标识使用实际读取版本）。

将用户设计的流程和布局转换成可审阅的原子命令脚本。文档基线API 2.30；新建未指定时按此基线，指定版本或修改既有脚本按[版本索引](references/api-versions.md)确定目标，不静默升级。当前用户指令优先于经验默认；与硬件/API明确限制冲突时报告，不静默改布局。

## 每次必须执行

- 只查本技能维护资料。未收录接口、参数、load name、兼容关系就报缺失，不凭记忆或自动联网补齐。API和安装关系只有用户要求升级时才查官方并更新。按需查询例外：已确定耗材的孔几何/定义属性缺失时，允许直接获取官方GitHub定义，按operations的“耗材几何按需查询”执行，不必再请求联网许可。具体报错或维护资料无法解释的关键行为可按[官方仓库导航](references/upstream-maintenance.md)定向查证；仅查证原因，不擅自采用未收录API/关系或修改维护资料。未收录关系不等于不兼容。
- 证据约束同时覆盖代码、注释和聊天建议，按operations的“证据与能力边界”执行。做不到、查不到或无法验证时明确报告缺口；不得猜补后称审查通过。交付前按protocol-review核对事实依据、文案与代码及实际验证范围。
- 编写完整协议前按operations的“布局与耗材确认”复用已有信息；需求笼统时给贴合实验的一段完整描述示例，集中补充后按已说明的推荐值处理省略项，不逐阶段连问。区分用户提供、推荐补齐和真实未决条件，已有信息足够时直接生成。
- 用aspirate、dispense、move_to、delay与显式循环组装。默认不用transfer/distribute/consolidate；混匀不用mix/dynamic_mix。避免过度封装。
- 每步aspirate、dispense、air_gap显式flow_rate；air_gap默认20µL/s。blow_out例外：默认省略flow_rate使用官方默认，仅用户指定时显式覆盖。禁止全局流速和rate倍率代替。查询/插值在生成阶段完成，脚本只保留算好的数值或赋定值变量。
- 所有脚本加载液体用于可视化及液量跟踪。覆盖实际参与的源孔、样本孔、反应孔和接收孔。试剂色鲜明；空反应孔优先浅灰Liquid、volume=0，按用途命名，优先4–5字/字符内；不需颜色可load_empty。批量列表/映射初始化，禁止逐孔调用可合并的load_liquid。
- 常规吸液默认bottom(z=0.8)，排液默认meniscus(z=0,target="dynamic")。使用end_location时location默认操作孔bottom(0.8)，用户明确起点优先；混匀末次引用此规则移动排至最终液面；小体积吸液确认、立即混匀和无模型位置按操作经验处理，实测仅明确指定时启用。
- dispense显式push_out；基础默认0，仅满足操作经验的余液/液面条件时自动启用规格默认值，明确覆盖仍校验余液。保持受控入液/退出、top准备、delay，不作为冗余删除；吸排液等待按维护配置（用户覆盖优先）匹配型号/枪头/滤芯/液体，见等待路由。活塞准备统一归入吸液前检查：blow_out/非零push_out/模式切换只标记待准备；下一次aspirate前才在该吸液孔top、空枪头状态显式prepare_to_aspirate，再控速入液；没有下一次吸液就不触发。
- 每次加载和搬运都查安装关系并更新占位。第4列先查同排第3列，不能直接移液；热循环占A1+B1。冲突反馈，不擅自重新设计。
- 部分喷嘴取头默认禁止返回；仅用户针对该场景明确允许才例外。dry_run/return_tips开关不构成该例外。
- 不把单次特例自动推广成全局经验，不把用户经验说成官方保证。

## 规则组织

按液体账本、枪头管理、空间路径、活塞状态分别维护；跨维度必要条件集中在operations.md的“组合校验”。API只定义调用契约，参数表只维护数据，原子/流程模板只示范组合。先分维度校验，再检查组合条件和流程顺序，不枚举所有动作组合。设备额外经验分为“机制与参数参考”和“操作经验与技巧”，由设备经验入口按需定位；已确认为核心规范的内容保持原处唯一维护。

## 工作流与路由

1. 提取当前流程、硬件/耗材、布局、初始液量、逐步体积、类别、排净和复用意图；按operations的“布局与耗材确认”一次集中补充或应用已说明的推荐值，再编写协议。未给初始试剂量按本次需求计算，建立逐孔液量与位置账本，共享储液槽按实际通道合计扣量。相对资料和命令路径均以本SKILL.md所在目录为根；工具调用使用解析后的绝对路径或先进入该目录，不依赖会话工作目录。
2. 每次生成先读[操作规则](references/operations.md)的“分工与查用”“证据与能力边界”“布局与耗材确认”和“主动确认：按影响筛选”，按当前任务读相关维度及组合校验的完整章节。新建完整移液协议需覆盖液体账本、枪头、路径、活塞及相关组合条件；仅修改局部时检查变更动作和受影响的后续状态，不重做无关流程。按下表读取对应资料；先rg定位，再读完整条目，不一次读全部API。

|任务|必查资料|
|---|---|
|本次设备的额外使用经验|[设备经验入口](references/device-experience.md)：按设备/操作定位；机制参数仅疑难判断时展开，技巧按场景查；没有条目不阻塞生成|
|指定API版本／新建默认／保留已有版本|[版本索引](references/api-versions.md)，仅核对本次实际使用的接口、参数与行为分界|
|任何硬件/耗材加载|[名称](references/catalog.txt)、[安装关系](references/installation.txt)、[加载API](references/api-layout.md)|
|吸排液、取弃头、活塞、移动|[移液器API](references/api-pipette.md)、[孔位API](references/api-wells-liquids.md)|
|沿壁/特殊位置需要耗材孔尺寸或定义属性|[操作规则](references/operations.md)“耗材几何按需查询”：已有定义优先，缺失时查官方GitHub，仅提取当前所需字段|
|液体标签/初始化、meniscus|[孔位与液体API](references/api-wells-liquids.md)、操作经验|
|计算吸排液速度/air_gap默认值|[说明](references/rates.md)、运行scripts/flow_rate.py；吸液[JSON](references/aspiration-rates.json)、排液[JSON](references/dispense-rates.json)|
|吸排液/混匀/撤离等待|[等待规则](references/delays.md)、运行scripts/delay.py；数值源[JSON](references/delay-rates.json)，按阶段输出|
|非零push_out排空分段|操作规则的“分段排空”，生成时展开；[原子片段](references/patterns.md)提供动态液面和显式终点两种路径|
|混匀或常规移液|[原子片段](references/patterns.md)，按任务实例化；容量截断/保留液/切换模式组合见[混匀实例](references/mixing-examples.md)|
|仅排查余液/空气/容量/活塞异常|[状态与体积核算参考](references/pipette-mechanics.md)，数值[源码快照](references/pipette-mechanics-data.json)；非日常生成必读，不覆盖经验默认|
|明确一吸多分|操作规则的“一吸多分”：按枪头查首尾量；组合现有路径、流速、等待及push_out规则|
|梯度稀释流程快速参考|[完整流程示例](references/serial-dilution.md)，仅作组合参考；核心规则/原子模板优先，可不使用该参考重新生成|
|8通道1–7喷嘴在储液槽吸排液|[储液槽定位经验](references/reservoir-partial-nozzles.md)：主动确认默认定位或完整8通道对齐，仅确认后计算Y偏移|
|部分取头、复用、空跑、枪头不足/同位置补给|操作规则的枪头管理、测试运行参数及移液器API|
|参数/CSV、展示文案与参数排序|[参数API](references/api-parameters-csv.md)、操作规则的“源码说明与运行文案”|
|夹爪/板盖/搬运|[搬运API](references/api-gripper.md)、安装关系；更新位置账本|
|模块操作|[模块API索引](references/api-modules.md)、[硬性条件](references/module-conditions.md)、[使用经验](references/module-practices.md)对应章节；安装关系独立|
|从零生成后的完整审查／修改后的按需检查|[沿执行路径的状态推演](references/protocol-review.md)，引用已有规则，不另造数值或强制依赖官方模拟|
|暂停/延时/归位/灯光|[流程API](references/api-flow.md)|
|类型/Point/枚举/入口|[类型参考](references/api-types.md)|
|明确单次液面实测|[探测API](references/api-probe.md)及operations的“50µL移液器探测后清膜”，不默认调用|

3. 流速仍在生成阶段算好。需要按给定体积确定位置时，直接在脚本使用well.bottom(z=well.height_from_volume(vol))，可用于location/end_location；不再要求生成前算成固定高度，不自写几何公式。vol是该孔在目标时刻的总液量，不一定等于本次移液量。常规动态液面吸排仍用meniscus；用户明确指定按体积换算时，不擅自改为meniscus。耗材模型不支持时反馈，不自行近似。
4. 按加载、初始化、原子步骤、明确收尾编写完整脚本；初始化在移液前。排液查询维护的数据（用户覆盖优先，其余官方singleDispense），按实际滤芯类型区分；air_gap默认20，blow_out默认官方值，不因这些默认而新增动作。
5. 检查语法、完整参数、体积守恒/容量、枪头、动态占位、第4列、显式flow_rate/push_out（blow_out默认例外）及N次混匀。按操作经验追踪跨孔路径，查缺失目标top造成整段低速的问题，检查变量/循环/分支的实际孔，不只搜speed。从零生成按protocol-review.md完整审阅状态及冗余动作；已有脚本的小改按变更影响选择参数核对、局部审查或必要的全量审查，不因重新交付完整文件强制全量复审。按改动需要执行语法检查。交付前按protocol-review.md检查当前环境：opentrons_simulate可执行时对最终脚本增加官方模拟，不可用时只做技能审查及适用的语法检查，不自动安装依赖；纯非行为编辑可跳过模拟，各项结果分别报告。框架审查不保证模拟100%通过，模拟也不能替代实机验证。
6. 每个新脚本默认加入独立的dry_run、return_tips二选一choice参数（内部布尔语义默认False），受操作经验约束；dry_run默认用水，所有吸排液按水相速率切换，生成阶段查好两套定值，详见operations的测试运行参数与rates。实际读取并应用技能后，脚本顶部添加技能write-opentrons、实际规则版本、本次用户覆盖项及实际框架审查状态注释。全量审查交付提供protocol-review.md规定的紧凑审查凭据（适用规则/覆盖范围、覆盖项、未决项、结论），不能只贴标识代替审查；未解决关键状态或分支不得标通过。小改只说明实际修改/检查范围，不重复完整审查报告、不虚称全量复审。完整生成交付同步标识，聊天交付中的液体类型仅突出有机相/甘油相的适用操作及简短依据（按operations，不逐项列水相），并说明参数来源（技能经验/已收录官方数据或API默认/本次覆盖/未覆盖）、容量截断、特例、实际验证结果和真正未解决项。聊天交付同时按operations附关键孔/关键操作的吸排液流速、高度和移动速度参数摘要。对按用量初始化的试剂源孔，另按operations给出用量标签与实际额外装载建议。读取失败不得贴已使用标识，未运行模拟不得称通过。可独立完成的先完成，只集中询问阻塞项。

## 模块API直达

按设备只读相关成员：[共享加载与属性](references/api-module-common.md)、[热震荡](references/api-module-heater-shaker.md)、[温控](references/api-module-temperature-module.md)、[热循环](references/api-module-thermocycler.md)、[Flex磁力架](references/api-module-magnetic-block.md)、[OT-2磁力模块](references/api-module-magnetic-module.md)、[读板机](references/api-module-absorbance-plate-reader.md)、[Stacker](references/api-module-flex-stacker.md)、[并发Task配套](references/api-module-tasks.md)。成员覆盖记录见[同步清单](references/module-api-coverage.json)，仅维护核对时读。

## 减少重复推断

- 本轮已读取且未修改的规则/接口直接复用；按“型号、枪头容量、滤芯、液体类别、动作、实际体积”去重流速查询，等待按其真实查询键去重。输入或资料版本改变时重新查询，不跨配置套值。
- 先确定动作及初始状态，再查询实际用到的接口和参数；未启用touch_tip、air_gap、探测或搬运时不展开其示例。基础约束和动作相关组合校验不得跳过。
- 规则冲突先区分官方契约、技能默认、本次明确覆盖、模板示例；本次覆盖可替换默认，不能绕过API限制。模板无权覆盖规则；同层规则矛盾须定位原始条目处理，不猜优先级。
- 模板按需选一个最相关片段，其余直接由原子规则组合；不反复比较所有流程参考。只重查发生变化的状态及其下游依赖。

## 维护

技能项目的修改、项目级审查、版本与公开发布按[项目维护规则](references/project-maintenance.md)执行；仅维护时读取，不加入协议生成流程。

特殊问题排查与官方资料更新按[官方仓库导航与更新入口](references/upstream-maintenance.md)执行，仅相关排查/维护时读取；安装不自动刷新，来源与经验覆盖分开保留。

修改速度只改JSON，工具从同一数据源读取。API参数放API参考；用户生成规范放本文件与operations；模板只展示原子结构。最新确认覆盖旧偏好，不引入历史待确认规则。仅修改相关文件，保留稳定规则。查询缺口按rates.md判断，不阻碍参数已明确的流程。

审查能力维护时按[回归维护说明](assets/review-regression/maintenance.md)运行固定案例；仅维护时读取，不加入日常生成路由。题面与答案隔离，先独立审查后评分；类别/定位自动比对与理由人工核对分别记录。
