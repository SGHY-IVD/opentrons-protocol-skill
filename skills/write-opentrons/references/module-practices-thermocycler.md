# Thermocycler

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-thermocycler.md) · [API与加载](api-module-thermocycler.md)；静态安装唯一查[安装关系](installation.txt)。

按本次动作读取共用经验的相应完整小节：人工初始装载时查[开始装载](module-practices-common.md#开始装载)的热循环分支；运行中处理已知/未知状态时查[状态组织](module-practices-common.md#运行中按已知状态组织)；PCR程序与计时任务选择等待方式时查[并发选择](module-practices-common.md#按等待对象选择并发)；正常结束或持续保温时查[收尾](module-practices-common.md#正常结束与持续保温)中的热循环装载、块/盖停用与持续保温分支。未触发的场景不展开，硬件与条件见[本设备条件](module-conditions-thermocycler.md)。

### 官方建议与程序组织

来源：2026-11-04核对[热循环条件](module-conditions-thermocycler.md)所引官方Python用法与GEN2密封指南；在线内容未固定修订，未作本项目实机验证。以下用于按场景组织方案，硬条件仍唯一查该节。

- PCR前分别安排热盖准备与块温程序，按实际实验设定热盖并等待相应准备完成；不从块温直接推定盖温。选择实际密封方案，不能只凭代码设置盖温推定已经密封。
- 使用可重复密封垫时，按该节要求完成用前清洁消毒；每轮运行后检查磨损和损坏，必要时更换。密封件状态会影响蒸发，不将机械关盖成功当作所有耗材密封效果已验证。
- PCR后的暂存与结束安排受设备低温时限和取板条件约束。不能将4℃无限保持作为普通终点，也不能把pause当自动停用；需要更长暂存时另按试剂要求安排合适储存，不擅自升温规避时限。

PCR循环表达默认沿用本节原生profile示例：官方说明，外层for循环逐步调用set_block_temperature并指定每步保持时间，也能表达相应温度动作，但运行日志会展开更多步骤。依据用户2026-11-04确认的取舍，该替代写法暂不另加示例；确有逐轮定制需要时可按实际收益选择，不作为常规模板。整段Python for循环本身不是可交给wait_for_tasks的模块Task。

### PCR操作示例

以下为已讨论的组合片段：例1为“共用准备＋阻塞循环＋普通收尾”，例2改用并发循环，例3将收尾换为短时低温保持。均放在run函数体内，按场景选用；不是完整可上传协议，也不要求最终代码采用相同结构。目标示意为Flex API2.30，并发最低API2.27；B1、耗材、温度、时长、30轮及25µL均为示例，实际布局仍按installation核对，完整协议补充真实液体初始化、参数及相关审查。
装板前初始盖状态未知；实际耗材与GEN2密封方案已核对。普通收尾的25℃只展示一个块温目标，不是统一取板温度或热盖已可触摸的证明；应按本次设备冷却/取板条件确定实际目标并确认。低温例须有符合设备时限的人工结束安排，不作为无人值守自动限时方案。

共用准备与预变性：

```python
tc = protocol.load_module("thermocycler module gen2", "B1")
plate = tc.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt")

# 示例单孔最大液量；完整协议在此补充实际液体初始化。
max_well_volume = 25
steps = [
    {"temperature": 95, "hold_time_seconds": 20},
    {"temperature": 60, "hold_time_seconds": 20},
    {"temperature": 72, "hold_time_seconds": 30},
]

tc.open_lid()
protocol.pause("请放入已加样的PCR板，并确认所选密封方案已准备好；完成后继续。")
tc.close_lid()
protocol.comment("开始PCR程序")
tc.set_lid_temperature(105)
tc.set_block_temperature(
    95, hold_time_seconds=180, block_max_volume=max_well_volume
)
```

阻塞循环与终延伸：

```python
tc.execute_profile(
    steps=steps, repetitions=30, block_max_volume=max_well_volume
)
tc.set_block_temperature(
    72, hold_time_seconds=300, block_max_volume=max_well_volume
)
```

并发循环与终延伸：本例Task只覆盖30轮循环，预变性与终延伸分别阻塞。

```python
pcr_task = tc.start_execute_profile(
    steps=steps, repetitions=30, block_max_volume=max_well_volume
)

# 此处可插入PCR循环期间的其他独立步骤。
# 插入的步骤不依赖本次PCR完成，也不改变热循环所需条件。

protocol.wait_for_tasks([pcr_task])
tc.set_block_temperature(
    72, hold_time_seconds=300, block_max_volume=max_well_volume
)
```

普通收尾：

```python
tc.deactivate_lid()
tc.set_block_temperature(25, block_max_volume=max_well_volume)
tc.deactivate_block()
# 已满足本次取板冷却条件；热盖密封处仍可能有余热。
tc.open_lid()
```

短时低温保持收尾：替换上面的普通收尾，不将两段连续执行；继续取板前同样确认冷却条件。

```python
tc.deactivate_lid()
tc.set_block_temperature(4, block_max_volume=max_well_volume)
protocol.pause(
    "模块保持4℃，请及时结束，低于室温累计勿超2小时；"
    "点击继续后停止温控并开盖。"
)
tc.deactivate_block()
tc.open_lid()
```
