---
name: write-opentrons
description: 仅为Opentrons Flex设备按用户实验需求、Flex配置和维护的移液经验编写、修改及检查Opentrons Python协议。用于客户SOP转代码、液量与液面跟随、流速查询、模块和耗材加载、抓手搬运及手写混匀，按需引导自定义耗材创建与复用；实际硬件先核对并回显确认，再用通俗完整方案引导耗材布局与实验步骤，按用户修改迭代；按需辅助Flex设备发现、配置读取与协议发送；仅查维护的API和安装关系。
---

# Opentrons代码助手

规则版本：2026-11-06.7（交付标识使用实际读取版本）。

仅为 **Opentrons Flex** 编写、修改和审查protocol，不提供OT-2专属硬件/API或经验。迁移需求先核对实际Flex配置，不能只替换robotType。文档维护基线为API 2.30；按[版本索引](references/api-versions.md)核对实际机器人软件、选定目标API及本地模拟环境，既有脚本不静默升降级。

## 判断原则

- **先理解问题，再选入口。** 将用户表述还原为任务目标、相关对象及要判断的关系、动作或状态。按下表选最贴近的本地入口，再定位并读取相关条目。遇到变体或多种可能含义时，结合本次配置核对各自适用条件，分别处理有依据的部分。认定本地缺失前，先读对应入口并核对适用条目。关键词未命中本身不足以判定缺失。
- 当前明确需求可覆盖技能默认，不能绕过硬件/API限制。区分官方契约、技能默认、本次覆盖与示例；示例供理解和实现参考，不新增规则，也不要求照搬结构。
- 先查本地维护资料。已维护且适用于本次配置的API、参数、硬件、安装关系及实现策略，直接作为回答、编写和审查的依据。开放数据按需查，其他关键缺口或实际冲突按[日常查证边界](references/upstream-maintenance.md#日常查证边界)处理。
- 规则各归唯一职责：操作控制状态，场景组合动作，API定义调用，安装判断承载与占位，参数表维护数值，交互组织确认，交付组织说明，审查核验结果。相互引用复用结论，不复制另一套规则。

## 一次任务如何推进

1. 识别新建、局部修改、问答、设备辅助或项目维护。先复用当前需求、已有效确认的硬件、布局及已有检查记录，按变更影响继续，不重问未改变的信息。相对路径均以本SKILL.md所在目录为根，工具使用解析后的绝对路径或先进入该目录。
2. **新建完整协议**读取[交互与确认](references/protocol-interaction.md)、[核心操作规则](references/operations.md)、[结构与类型](references/api-types.md)、[协议骨架](references/protocol-skeleton.py)、[交付规范](references/protocol-output.md)及[审查方法](references/protocol-review.md)。骨架用于熟悉协议组成，其余可选区块按实际需要组织。先核对实际硬件，按[编写前回显](references/protocol-interaction.md#编写前回显)展示方案，收到用户对最新回显的确认后再编写。
3. 按下表直达实际命中的章节、成员和数据，不通读全部参考。新建移液协议覆盖核心四个控制维度及适用组合条件；局改只读变更及下游依赖。先确定动作和状态，再查询所需接口、流速与等待，组装、检查并交付。
4. 依[审查方法](references/protocol-review.md)选择完整或局部检查，区分语法、技能审查、官方模拟与实机结果；依[交付规范](references/protocol-output.md)给出与最终代码一致的标识、参数摘要及真实验证范围。可独立完成的先完成，只集中处理剩余阻塞项。

## 按任务直达

|当前任务/触发|权威入口|
|---|---|
|硬件描述、布局回显、推荐补齐、确认与实验迭代|[交互与确认](references/protocol-interaction.md)|
|液量、枪头、空间路径、活塞及跨维度前置条件|[核心操作规则](references/operations.md)；仅查实际命中的维度/组合条件|
|分段排空、常规移液或移除液体去向|[排液场景](references/operation-dispense.md)：只读命中章节|
|混匀或加液后原位衔接|[混匀规则](references/operation-mixing.md)及核心“连续原位混匀”组合条件|
|一吸多分|[分液场景](references/operation-multi-dispense.md)|
|磁吸后将当前上清全量移至废液|[去上清场景](references/operation-magnetic-supernatant.md)|
|长孵育分段提示|[孵育场景](references/operation-incubation.md)|
|硬件/耗材名称、官方定义或特殊几何/液量模型|[名称与检索](references/catalog.txt)、[几何与定义查询](references/labware-geometry.md)；明确自定义或官方无匹配时进入[自定义耗材](references/custom-labware.md)，不在普通开局展开成品库|
|布局、加载或搬运的承载/占位核验|[统一安装核验](references/installation-core.md#统一安装核验)；所需静态关系按[安装索引](references/installation.txt)查具体父子项，来源档案仅追溯时读|
|加载、取弃头、吸排液、移动、液体标签/meniscus、搬运|[加载API](references/api-layout.md)、[移液器成员索引](references/api-pipette.md)、[孔位与液体API](references/api-wells-liquids.md)、[抓手API](references/api-gripper.md)：仅读所用成员|
|流速与等待|[流速语义](references/rates.md)及scripts/flow_rate.py；[等待语义](references/delays.md)及scripts/delay.py。对应JSON为数值唯一来源|
|运行参数/CSV影响动作数值或方案|[参数化指引](references/parameter-planning.md)及[参数/CSV API](references/api-parameters-csv.md)；参数显示、dry_run/return_tips语义归[交付规范](references/protocol-output.md)|
|模块加载方法、模块自身承载位/库存/状态、能力或操作|[模块索引](references/api-modules.md)，只查该设备的适用条件、API和经验。涉及台面安装、适配或占位时，先走统一安装核验|
|单次液面实测|[探测API](references/api-probe.md)及[探测后清膜](references/operation-probe-film-clearing.md)；未请求时不默认探测|
|沿壁或touch_tip特殊路径|[特殊运动路径](references/operation-motion-special.md)|
|8通道部分喷嘴在储液槽吸排|[储液槽定位](references/reservoir-partial-nozzles.md)|
|第三方设备、通讯、辅助类复用或DIY|[扩展代码库](references/extensions.md)；普通槽位叠板另查[Riser](references/api-riser.md)，不当作官方Stacker|
|解释机制、规则原因或排查疑难|[问答](references/faq.md)、[设备经验入口](references/device-experience.md)；仅空气/容量/活塞跟踪疑难查[核算参考](references/pipette-mechanics.md)。问答未命中时先查对应本地规则|
|发现设备、读配置、发送文件|[连接与发送](references/flex-http.md)，可选辅助分支，普通协议编写不必读取或调用|
|暂停、延时、归位、灯光、并发计时|[流程API](references/api-flow.md)、[模块Task](references/api-module-tasks.md)|
|本地核对后仍有影响结论的缺口、实测冲突或明确查证需求|[日常查证边界](references/upstream-maintenance.md#日常查证边界)及[特殊问题导航](references/upstream-maintenance.md#特殊问题查找导航)|

## 复用已有判断

- 本轮已读且未改变的规则、接口、有效确认及核算直接复用。按真实查询键去重流速与等待；输入或资料版本变化才重新查询，不跨配置套值。
- 未启用的探测、触壁、空气间隙、搬运等不展开其实现和示例；适用核心约束及组合条件仍须核对。示例只选最相关片段按需参考，不反复比较所有流程。
- 改动沿状态依赖传递，只重查改变的状态及其下游；发现同层规则矛盾回到原条目处理，不猜优先级，不以重复审查代替解决矛盾。

## 维护分支

仅修改技能项目时读取[项目维护规则](references/project-maintenance.md)，官方同步按[上游维护](references/upstream-maintenance.md)，审查能力测试按[回归维护](assets/review-regression/maintenance.md)。测试题面、答案、历史报告和来源档案不加入日常生成路径。通用曲线只改对应JSON；场景覆盖只在该场景维护，不反写通用曲线。新确认覆盖旧偏好，不引入历史待确认规则。
