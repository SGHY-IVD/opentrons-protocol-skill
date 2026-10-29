# 模块操作经验与使用示例

按设备定位：[热震荡](#heater-shaker) · [温控](#temperature-module) · [热循环](#thermocycler) · [磁力架](#magnetic-block) · [读板机](#absorbance-plate-reader) · [Stacker](#flex-stacker)

按[模块索引](api-modules.md)定位当前设备。官方硬条件唯一查module-conditions，API签名/参数查对应API文件，静态安装唯一查installation。经验应写明场景、来源、条件及验证程度；建议不自动升格为硬性约束，没有额外经验也不阻止合法用法。

## 热震荡、温控和热循环的共用经验

来源：用户2026-10-16确认的使用偏好；本节仅适用于这三类模块，不将其开关、停用或保温步骤套到其他设备。位置/温度/时长由实验决定，不新增数值默认。

### 开始装载

初始布局有耗材位于热震荡/热循环且需要人工装载时，把访问准备放在运行早期、取枪头及实验动作前：热震荡确认停止震荡→打开锁扣，热循环打开模块盖→pause提示放入相应耗材→用户继续→按接下来的动作需要关闭。软件load_labware只是声明布局，不等于已经完成实体放置。
初始状态未知时允许一次必要初始化，不假定上一程序留在打开状态。如果当前流程已有可信的已打开状态，不重复打开；人工干预是否改变状态按暂停提示与实际确认判断。温控模块没有盖/锁扣，不机械套用开关。

示例仅展示装载交互：已完成布局声明，两个模块初始状态未知，假定后续热震荡需移液、热循环先做温控。只保留实际使用模块的行；不是每次搬板都调用的包装函数。

```python
hs.deactivate_shaker()  # 初始状态未知，先确保能打开锁扣
hs.open_labware_latch()
tc.open_lid()
protocol.pause("请将耗材装入热震荡和热循环模块；完成后点击继续。")
hs.close_labware_latch()
tc.close_lid()  # 本例下一步温控；若下一步先移液，保持打开直到真正需要关盖
```

### 运行中按已知状态组织

生成和审阅时逐步记录锁扣/盖的位置（打开、关闭、未知、过渡中）、震荡状态、块/盖/温控模块目标及到达情况、待完成Task、占用耗材。只在需要的状态与当前可信状态不一致时切换；不用“每次搬板先无条件开关”的通用函数，也不为了状态跟踪强制生成运行时框架。
状态变更只在成功完成命令后成立；异步任务尚未等待完成时不能直接记为到达目标。一个已完成open→不改变盖状态的其他步骤→再次open，第二次是冗余候选，不因中间隔了很多行就忽略。
API强制的首次确认不算冗余，例如Heater-Shaker首次明确close、读板机initialize前要求的close。人工操作可能改变的具体状态设未知/重新确认；普通pause本身不自动关闭温控，也不必清空所有无关状态。

### 正常结束与持续保温

用户未指定持续运行时，正常结束路径显式停用实际使用的温控功能、停止震荡，并打开热震荡锁扣/热循环模块盖方便取板。热震荡先停震荡再开锁扣；热循环同时处理块和盖温控。已在此前步骤停用/打开且状态可信时不为“收尾”再执行同样动作。停止温控不等于已经冷却，不承诺可立即触摸高温物件。

```python
# 本例进入收尾时：震荡/加热仍开启，锁扣和热循环盖仍关闭。
hs.deactivate_shaker()
hs.deactivate_heater()
hs.open_labware_latch()
temp.deactivate()
tc.deactivate()  # 同时停止块和盖温控
tc.open_lid()
```

如流程明确需要长时间保温：先按所需温度建立保持状态，再pause等待用户回来；点击继续后执行停用和必要开盖。不要先deactivate再pause而声称仍在保温。

```python
# hold_temperature由本次实验给出；体积依据已初始化的液量及相应API。
tc.set_block_temperature(hold_temperature)
protocol.pause("当前继续保温；准备结束实验时点击继续，随后停止温控并开盖。")
tc.deactivate()
tc.open_lid()  # 仅当此前盖为关闭状态
```

这些收尾保证仅指正常执行到该分支；用户取消、断电、报错可能不执行后续代码，不能声称pause后收尾或try/finally保证所有中止情况下关闭设备。明确长期保温要求优先，不自行缩短；dry_run按已有规则处理，不另设模块温度默认。

## Heater-Shaker

沿用上方共用经验中的热震荡装载、已知状态组织及停止震荡/加热后开锁扣分支；额外经验尚无新增。硬件与条件见module-conditions同名节。

## Temperature Module

沿用上方共用经验中的温控与停用分支；不套用模块盖/锁扣操作。额外经验尚无新增。硬件与条件见module-conditions同名节。

## Thermocycler

沿用上方共用经验中的热循环装载、块/盖停用与持续保温分支。额外经验尚无新增。硬件与条件见module-conditions同名节。

## Magnetic Block

额外操作经验待补充；当前按对应API及module-conditions使用。此入口不表示模块缺少能力，不套用其他模块经验。

## Absorbance Plate Reader

额外操作经验待补充；初始化、盖与读数边界属于module-conditions，参数及读数接口查对应API，不作为可省略的经验处理。

## Flex Stacker

来源：用户2026-10-29确认的供料使用经验；操作原则按官方机制核对，未作实机验证。以下为场景建议，必要前置条件仍唯一见module-conditions的Flex Stacker节。

### 人工预装与按需供料

当本次需求是连续供应耗材时，优先采用操作员通过装料门预装仓内耗材、协议声明实际初始库存、需要时retrieve再搬到目标位置的组织方式；无需为已在仓内的每件耗材再写抓手入仓动作。数量、型号、盖子及目标位置按本次确认选择，不设固定装仓数量；不因使用Stacker就默认插入store/fill/empty。需要主动存回、回收或中途人工补给时采用相应接口，仍可双向使用。

### 官方用法改编片段

仅示范API组合，非完整协议；假定目标API支持、已确认抓手和相应甲板配置。示例槽位、耗材、盖及数量只演示写法，必须按本次配置替换；完整协议仍应用加载、占位、盖和枪头规则。

```python
# 供料示例：仓内已人工预装5盒200µL枪头且均带匹配盖，shuttle初始为空。
stacker = protocol.load_module("flexStackerModuleV1", "A4")
stacker.set_stored_labware(
    load_name="opentrons_flex_96_tiprack_200ul",
    count=5,
    lid="opentrons_flex_tiprack_lid",
)
tips = stacker.retrieve()
protocol.move_labware(tips, new_location="B2", use_gripper=True)
# 本片段只供料至B2，尚未移盖/取头；按实际后续动作处理。
```

```python
# 独立的存入示例：storage_stacker已配置且有余量；shuttle为空；
# labware_to_store及其盖/适配器整套与该仓内配置一致，搬运已核对。
protocol.move_labware(labware_to_store, new_location=storage_stacker, use_gripper=True)
storage_stacker.store()
```

官方示例源：v10.0.0 docs/python-api/docs/modules/flex-stacker.md，固定身份见module-conditions的Stacker来源；相关契约见api-module-flex-stacker与共享加载API。这里保留片段，不重复复制完整官方API速查表。
