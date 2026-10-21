# API版本索引

这是轻量兼容索引，不维护每个API版本的一整套文档。参数签名与语义仍唯一保存在api-*.md；此处只记录目标选择及已核对的关键版本分界。

## 当前维护状态

|项目|当前值|
|---|---|
|默认目标API|2.30|
|已维护最新基线|2.30；指本技能已同步的基线，不承诺是外部官方实时最新版|
|最近资料核对|2026-10-16；具体源码提交/文档来源见对应参考|
|高于基线的接口|未作为可用接口维护；已发现的VacuumModuleContext需2.31，不纳入2.30|

技能规则版本（日期编号）、协议API apiLevel、机器人软件版本、硬件修订是不同概念，不互相替代。

## 选择与检查

- 新建协议未指定版本：使用维护基线2.30。用户明确指定：采用指定apiLevel，仅查本次用到的成员/参数/语义的版本边界。
- 修改已有协议：未要求升级时保留文件原有apiLevel；不能因最新基线变化默默升级客户脚本。用户本次明确指定版本优先。
- 支持判断分为“已核对支持”“已知不支持”“资料不足”。当前基线签名含某参数，不代表旧版本也支持；没有写最低版本也不等于所有旧版本支持。
- 对不支持项定位到具体命令/参数/最低版本；先完成可独立的部分，集中反馈真正受影响的选择。不静默提高apiLevel、不偷偷换高级命令或改变物理行为。只有已收录且保持用户意图的兼容写法才可采用，并交付说明；会改变既定规则的替代需用户明确选择。
- 用户指定高于已维护基线时说明资料范围；未经明确升级不联网猜补。声明apiLevel也不证明设备软件支持，实际软件兼容未知时单独说明，不假定。
- 版本选择是一次任务级判断；对相同接口/参数组合核对一次即可，只有目标版本或用法变化才重查。按版本号元组比较，不把2.9当成大于2.30的字符串/小数。

## 已核对的关键分界

|接口/行为|版本分界|参考与用途|
|---|---|---|
|dispense(push_out=...)|2.15新增|api-pipette.md；不可在更低版本直接套参数|
|prepare_to_aspirate()|2.16新增|api-pipette.md及固定源码requires_version|
|dispense(0)/超当前量|2.17起0不排液、超量报错|api-pipette.md；旧版行为不同|
|air_gap液体跟踪|2.22起空气不计入目标孔液量|api-pipette.md、pipette-mechanics.md；仍占枪头容量|
|aspirate/dispense显式flow_rate|2.24新增|api-pipette.md；旧版仅有rate不等于满足本技能显式流速规则|
|air_gap(in_place/rate/flow_rate)、touch_tip(mm_from_edge)|2.24新增|api-pipette.md；分别核对参数互斥|
|well.height_from_volume|2.24新增|api-wells-liquids.md|
|热震荡温度旧37℃下限|2.25起取消旧下限|module-conditions.md；区分API校验与环境温度可达性|
|模块加载的adapter_namespace/version、lid_namespace/version|2.26新增|api-module-common.md|
|aspirate/dispense(end_location, movement_delay)|2.27新增|api-pipette.md；Flex移动吸排液参数|
|模块并发Task、start_*、set_shake_speed、wait_for_tasks/create_timer|关键并发扩展在2.27|按api-module-*.md具体成员核对；不能把所有模块方法统一判为2.27新增|
|blow_out(flow_rate)|2.28新增|api-pipette.md；默认省略flow_rate与显式覆盖需分开判断|
|热循环ramp_rate实际生效|2.28起|api-module-thermocycler.md；不能只看老签名有参数|
|touch_tip对touchTipDisabled耗材报错|2.28起|api-pipette.md；属于行为限制变化|

此表是快速定位，不是完整历史兼容矩阵。未列成员继续读其维护条目的版本说明；未核对的旧版本用法报告缺口，不能靠该表遗漏反推兼容。动态meniscus、批量液体初始化等也必须按具体用法核对，不能用相邻功能的新增版本代替。

## 维护与交付

升级基线时更新本文件默认值、SKILL.md基线说明及真正变化的API条目；旧分界继续保留，不复制整库。参数/返回值/行为发生变化时在原API条目维护，此处只加索引。单次用户选旧版本不改变全局默认。
交付脚本写实际apiLevel，说明中简述“目标API版本、是否沿用/明确指定、具体兼容调整或未决项”；纯小改且版本未变时不重复长报告。
