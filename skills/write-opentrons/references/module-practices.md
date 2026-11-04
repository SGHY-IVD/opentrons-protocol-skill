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

### 按等待对象选择并发

来源：用户2026-11-04提出的场景经验；接口组合按官方[热震荡](https://docs.opentrons.com/python-api/modules/heater-shaker/)、[热循环](https://docs.opentrons.com/python-api/modules/thermocycler/)及[并发说明](https://docs.opentrons.com/python-api/modules/concurrent/)核对，未作实机验证。以下是组织建议，不要求每个模块动作都创建Task；现有阻塞及并发用法示例均可保留。并发接口及最低版本仍唯一查[Task配套API](api-module-tasks.md)和对应模块API。

|本次要等待的对象|建议的组织方式|
|---|---|
|热震荡达到目标转速|升速通常较快，常规优先用set_and_wait_for_shake_speed直接到速；确有升速期间交错工作的收益时仍可用set_shake_speed返回的Task。到速后的持续震荡时间另行安排。|
|较慢的升温或降温过程|有独立工作可交错时，采用对应模块的温度Task；依赖到温的步骤前等待该任务。按设备实际加热/制冷能力判断，不将耗时估算或timer代替到温条件。|
|条件已满足后的定时孵育、恒温或持续震荡|需要在保持期间执行其他独立步骤时，创建timer，在创建与等待之间插入这些步骤，再wait_for_tasks等待计时完成；没有可交错工作时可直接等待，不为并发而并发。|
|热循环PCR程序完成|需要在PCR期间交错工作时使用start_execute_profile返回的程序Task，并在依赖PCR结果前等待；不以外部timer估算程序完成。无需并发时仍可用阻塞的execute_profile。|

计时起点按实验定义；要求到温/到速后保持时，先满足相应目标、样品在位等开始条件，再创建timer。timer只计时间，不自动停用模块；若插入的独立工作超过计时长度，实际保持时间会延长，因此要求严格结束时点的流程须按允许时间窗安排。模块状态/收尾沿用本节原有规则；阻塞delay的长孵育提示仍见[操作规则](operations.md#长孵育分段提示)，不机械改写并发等待。

示例：已完成热震荡、适配器与耗材加载，已装入样品板且锁扣关闭；API≥2.27。37℃、500rpm及10分钟仅示意，完整协议按本次实验与试运行方案选择实际值。本例按模块到温且到速后开始计时，不等于实测液体温度。

```python
hs.set_and_wait_for_temperature(37)
hs.set_and_wait_for_shake_speed(500)

protocol.comment("开始恒温震荡，计时10分钟")
hold_timer = protocol.create_timer(seconds=600)

# 此处可插入在这10分钟内执行的其他独立步骤。
# 例如处理另一块板；具体动作仍须满足布局、避碰和模块状态约束。

protocol.wait_for_tasks([hold_timer])
hs.deactivate_shaker()
hs.deactivate_heater()
hs.open_labware_latch()
```

### 正常结束与持续保温

用户未指定持续运行时，正常结束路径显式停用实际使用的温控功能、停止震荡，并在满足设备取板条件后打开热震荡锁扣/热循环模块盖。热震荡先停震荡再开锁扣；热循环同时处理块和盖温控，其冷却/取板条件见[module-conditions](module-conditions.md#thermocycler)。已在此前步骤停用/打开且状态可信时不为“收尾”再执行同样动作。停止温控不等于已经冷却，不承诺可立即触摸高温物件。

```python
# 本例进入收尾时：震荡/加热仍开启，锁扣和热循环盖仍关闭；
# 热循环样品块已按本次方案完成冷却并确认取板条件。
hs.deactivate_shaker()
hs.deactivate_heater()
hs.open_labware_latch()
temp.deactivate()
tc.deactivate()  # 同时停止块和盖温控
tc.open_lid()
```

如流程明确需要持续保温：先按所需温度建立保持状态，再pause等待用户回来；点击继续后执行停用和必要开盖。热循环低于环境温度的保持须受上述设备条件中的时限约束，提前安排结束，不将pause当作无人值守的自动超时控制。不要先deactivate再pause而声称仍在保温。
以下片段仅适用于结束保持时样品块已满足本次取板冷却条件的温度；若保持的是高温，用户继续后还需先执行按本次方案选择的冷却及确认，再停用开盖，不能直接套用此处的相邻收尾行。

```python
# hold_temperature由本次实验给出；体积依据已初始化的液量及相应API。
tc.set_block_temperature(hold_temperature)
protocol.pause("当前继续保温；准备结束实验时点击继续，随后停止温控并开盖。")
tc.deactivate()
tc.open_lid()  # 此前盖为关闭状态，且已满足本次取板冷却条件
```

这些收尾保证仅指正常执行到该分支；用户取消、断电、报错可能不执行后续代码，不能声称pause后收尾或try/finally保证所有中止情况下关闭设备。明确持续保温要求在设备使用条件内优先，不自行缩短；dry_run按已有规则处理，不另设模块温度默认。

## Heater-Shaker

沿用上方共用经验中的热震荡装载、已知状态组织及停止震荡/加热后开锁扣分支；升速与保持期间的并发选择见[共用经验](#按等待对象选择并发)。硬件与条件见module-conditions同名节。

## Temperature Module

沿用上方共用经验中的温控与停用分支；不套用模块盖/锁扣操作。到温与孵育期间的并发选择见[共用经验](#按等待对象选择并发)。硬件与条件见module-conditions同名节。

### 制冷前的侧盖准备

来源：用户2026-11-04提供的现场操作经验，尚未在本项目实机复验。涉及温控制冷时，在配置核对、上机准备或交付提示中简短提醒：打开或取下模块所在位置对应的侧边磁吸挡板，保持散热通道通畅；已明确准备好的状态不反复询问或提示。这是人工准备，不生成自动打开挡板的API，也不强制增加pause。
此处指模块排风/走线用的可拆侧盖（side cover），不是透明侧窗、前门或顶板。官方[术语表](https://docs.opentrons.com/flex/glossary/#side-covers)及[Flex安装步骤](https://docs.opentrons.com/temperature-module/installation-flex/)确认其用途，2026-11-04在线核对，未固定修订；“磁吸、制冷前打开/取下”的具体做法按上述用户经验记录，不声称官方逐字规定。排风朝向的官方条件仍唯一见installation。

### 低温暂存与冷凝

来源：用户2026-11-04提供的场景经验，结合module-conditions中的官方冷凝与温度机制；未作本项目实机验证。长时间低温时主动考虑模块及耗材的冷凝，尤其关注敞口试剂孔/管：检查冷凝水是否进入、滴入或随操作带入体系，以及对实际液量、浓度和后续操作的影响。这些是风险检查方向，不将敞口耗材必然被稀释说成官方验证结论。
若目的只是运行期间低温暂存，且试剂说明、SOP或稳定性依据允许，可建议8–10℃，不为追求更冷而采用更低设定。该范围是有条件的用户经验，不是所有试剂的默认温度，不覆盖明确4℃、2–8℃或其他保存/反应要求，也不能保证不冷凝。模块设定与样品液温分别判断；实际保温时间和起点按实验决定。

### 官方建议的应用

来源：2026-11-04核对module-conditions温控节所引官方温度特性与环境条件，在线内容未固定修订，未作本项目实机验证。官方建议与据此形成的应用判断分开使用：

- 对实际液温有明确要求的应用，官方建议实测样品内部温度，判断是否需要调整温控方案；按实际铝块、耗材和液量验证。更换这些条件后重新判断原验证是否适用，是据此形成的应用建议，不自动补偿设定温度或强制所有实验增加探测动作。
- 制冷效果验证和重复运行时留意环境温度。官方列20–22℃为最佳制冷的推荐环境、20–25℃为可接受环境；这些是环境指标，不是模块目标温度，也不与前述8–10℃暂存建议混为一谈。超出推荐条件时效果可能变化，不将其改成新的API限制或固定降温耗时保证。

### 操作示例

以下三段是独立的run函数体片段，展示模块动作组合，不是可直接上传的完整协议。按本次场景选用，不要求套用其变量名、布局、温度或时长；目标示意为Flex API2.30，Task/timer例最低API2.27。D1模块、适配器、耗材及样品均假定已正确装好；制冷例另以初温高于目标、侧盖/排风准备完成及试剂条件允许为前提。
完整协议在温控前按实际孔位、液体和初始体积补充初始化，时长及dry_run沿用本次方案和操作规则；这里不虚构样品。计时均从模块到温且样品已在位后开始，不代表液体实测到温；正常收尾范围沿用共用经验。接口及加载关系查相应API和installation，示例不另定义规则。

例1：同步升温至37℃，孵育10分钟后停用；无独立工作交错，按阻塞等待的长孵育规则提示进度。

```python
temp_mod = protocol.load_module("temperature module gen2", "D1")
aluminum_block = temp_mod.load_adapter("opentrons_96_well_aluminum_block")
plate = aluminum_block.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt")

protocol.comment("开始升温至37℃")
temp_mod.set_temperature(37)
protocol.comment("开始孵育10分钟")
for elapsed_minutes in (5, 10):
    protocol.delay(seconds=300)
    protocol.comment(f"孵育等待：{elapsed_minutes}/10分钟")
temp_mod.deactivate()
```

例2：异步降至10℃，到温后保持10分钟；降温和保持期间分别留出独立代码插入位。timer的计时与超时边界见共用经验。

```python
temp_mod = protocol.load_module("temperature module gen2", "D1")
aluminum_block = temp_mod.load_adapter("opentrons_96_well_aluminum_block")
plate = aluminum_block.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt")

protocol.comment("开始降温至10℃")
cooling_task = temp_mod.start_set_temperature(10)

# 此处可插入降温期间的其他独立步骤。
# 插入的步骤不依赖本模块到温，并须满足布局和避碰要求。

protocol.wait_for_tasks([cooling_task])
protocol.comment("开始低温保持10分钟")
hold_timer = protocol.create_timer(seconds=600)

# 此处可插入低温保持期间的其他独立步骤。
# 插入的步骤不依赖本次保持完成，也不改变其所需条件。

protocol.wait_for_tasks([hold_timer])
temp_mod.deactivate()
```

例3：24孔铝块＋NEST 1.5mL翻盖管整套加载，维持8℃至操作员继续，随后停用。本例用已维护组合，不重复加载铝块与管；这组耗材不采用抓手搬运。

```python
temp_mod = protocol.load_module("temperature module gen2", "D1")
tubes = temp_mod.load_labware("opentrons_24_aluminumblock_nest_1.5ml_snapcap")

protocol.comment("开始降温至8℃")
temp_mod.set_temperature(8)
protocol.pause("模块继续维持8℃目标；准备结束保温时点击继续。")
temp_mod.deactivate()
```

## Thermocycler

沿用上方共用经验中的热循环装载、块/盖停用与持续保温分支；PCR程序与计时任务的选择见[共用经验](#按等待对象选择并发)。硬件与条件见module-conditions同名节。

### 官方建议与程序组织

来源：2026-11-04核对module-conditions热循环节所引官方Python用法与GEN2密封指南；在线内容未固定修订，未作本项目实机验证。以下用于按场景组织方案，硬条件仍唯一查该节。

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

## Magnetic Block

### 弹性支撑与低位吸液

来源：用户2026-11-04提供的现场提示；弹簧支撑机制见[模块说明](module-conditions.md#magnetic-block)。评估磁力架上孔板的近底或特殊低位吸液时，可将该结构作为接触缓冲的参考因素，不将其理解为没有触底接触或仅凭弹性放行过低/负高度。实际高度及可达性仍按[空间位置与路径规则](operations.md#空间位置与路径)核对；本提示不设置新的最低高度、下压量或自动覆盖默认值，未作本项目实机复验。

### 热震荡后转入磁力架时的放置偏移

来源：用户2026-11-04提供的现场经验，未作本项目实机复验，属于可选操作技巧，不是官方效果保证或默认搬运高度。
孔板经过热震荡且孔壁附液、随后需要移至磁力架时，可按实际耗材和模块组合，在该次抓手搬运move_labware(..., use_gripper=True)中设置drop_offset={"x": 0, "y": 0, "z": 1.0}，也可将该字典中的z改为2.0（单位mm），尝试利用略高释放后的落座动作帮助壁上液滴回落。正Z是在既有放置坐标上增加的偏移，不等同于精确自由落高；取值须结合实际落座、定位及是否飞溅核对，不推广到其他搬运动作。
该参数只调整本次放置动作，不修改耗材定义或吸排液高度，也不代替既有模块搬运前置条件；调用契约见[搬运API](api-gripper.md#protocolcontextmove_labware)，模块条件见module-conditions。

### 磁吸后去上清操作示例

动作、默认值和边界唯一见[场景规则](operations.md#磁吸后去上清)，单批结构见[原子片段](patterns.md#磁吸后去上清单批吸液)。以下按“共用准备→A/B输入二选一→共用执行”组成两例，是API2.30的run体片段，不是可直接上传的完整协议；sop_magnetic_seconds须在进入前由实际SOP给出并预检，不猜磁吸时间。只展示正常运行水相分支，完整协议的dry_run仍按rates解析各次实际量，不自动共用本例吸液速度。

示意配置：左侧单通道1000µL、200µL普通枪头及抓手；C1磁力架，B2为NEST2mL深孔板初始位，C2枪头盒，D2 NEST195mL废液槽，D1内置垃圾桶。实际应用前核对该配置、源孔和枪头几何、低位及移动路径和磁珠沉积分布；例中move_to不保证严格垂直路径。废液槽初始为空，top(-3)须高于本例最高废液液面，按悬空排液处理；本例按每孔新头、同孔跨批复用演示，不改变一般复用规则。未做实机、碰撞或磁珠回收率验证。

共用准备：

```python
mag = protocol.load_module("magneticBlockV1", "C1")
plate = protocol.load_labware("nest_96_wellplate_2ml_deep", "B2")
tips = protocol.load_labware("opentrons_flex_96_tiprack_200ul", "C2")
waste = protocol.load_labware("nest_1_reservoir_195ml", "D2")
trash = protocol.load_trash_bin("D1")
p = protocol.load_instrument("flex_1channel_1000", "left", tip_racks=[tips])
waste_well = waste["A1"]
```

例A：单孔200µL，一批完成普通180＋低位20，随后排废。

```python
initial_supernatant_ul = {"A1": 200}
# 每个二元组依次为本批的（普通段µL，低位段µL）。
removal_plan = [("A1", [(180, 20)])]
```

例B：A1为450µL，分三批200、200、50；另有B1为10µL，只做低位段。与例A互斥，选择其一。

```python
initial_supernatant_ul = {"A1": 450, "B1": 10}
removal_plan = [
    ("A1", [(200, 0), (200, 0), (30, 20)]),
    ("B1", [(0, 10)]),
]
```

共用初始化、搬入磁力架、磁吸及执行：

```python
supernatant = protocol.define_liquid(
    "上清", description="磁吸后待移除的水相上清", display_color="#2196F3"
)
waste_liquid = protocol.define_liquid("废液", display_color="#D9D9D9")
plate.load_liquid_by_well(initial_supernatant_ul, supernatant)
waste.load_liquid(wells=["A1"], volume=0, liquid=waste_liquid)

protocol.move_labware(plate, mag, use_gripper=True)
protocol.comment("开始磁吸")
waited_seconds = 0
while waited_seconds < sop_magnetic_seconds:
    wait_seconds = min(300, sop_magnetic_seconds - waited_seconds)
    protocol.delay(seconds=wait_seconds)
    waited_seconds += wait_seconds
    protocol.comment(f"磁吸等待：{waited_seconds}/{sop_magnetic_seconds}秒")

# 仅覆盖例A/B真实排量；修改计划后须按实际排量重新查询。
dispense_rate_by_volume = {200: 300, 50: 100, 10: 40}
protocol.comment("开始移除上清")
for well_name, batches in removal_plan:
    source = plate[well_name]
    p.pick_up_tip()
    for batch_index, (ordinary_ul, low_ul) in enumerate(batches):
        p.move_to(source.top())
        if batch_index == 0:
            p.prepare_to_aspirate()  # 新取头后的首次吸液，空头且位于源孔top。
        p.move_to(source.bottom(z=0.8), speed=20)

        if ordinary_ul > 0:
            protocol.delay(seconds=0.2)  # 本批首次入液等待。
            p.aspirate(ordinary_ul, source.bottom(z=0.8), flow_rate=20)
            protocol.delay(seconds=0.2)  # 普通段吸后等待。

        if low_ul > 0:
            p.move_to(source.bottom(z=0.1), speed=2)
            # 仅低位的一批，此等待同时覆盖本批首次入液和低位稳定，不叠加。
            protocol.delay(seconds=0.2)
            p.aspirate(low_ul, source.bottom(z=0.1), flow_rate=10)
            protocol.delay(seconds=0.2)  # 低位段吸后等待。
            p.move_to(source.bottom(z=0.8), speed=2)

        p.move_to(source.top(), speed=20)
        p.move_to(waste_well.top())  # 跨孔移动不设置入液用的低速。
        p.move_to(waste_well.top(z=-3), speed=20)
        batch_ul = ordinary_ul + low_ul
        p.dispense(
            batch_ul,
            waste_well.top(z=-3),
            flow_rate=dispense_rate_by_volume[batch_ul],
            push_out=0,
        )
        protocol.delay(seconds=0.2)  # 悬空排液无入液等待，仅保留排后等待。
        p.move_to(waste_well.top(), speed=20)
    p.drop_tip()
```

本例各非零段均满足所选配置量程，当前批次表为生成阶段定值；参数/CSV改变输入时按[参数化指引的预检时机](parameter-planning.md#计算与执行边界)核对全部计划及量程。正式吸液速度来自场景覆盖；排液200/50/10µL分别查得300/100/40µL/s，其他体积须重新查询。200µL水相头的吸排after和首次submerge均为0.2s，retract为0；仅低位的首次入液和同位置稳定要求由一次等待覆盖，悬空排废无submerge。push_out=0排空未产生新的待准备事件，因此后续批次不重复复位；需要非零push_out等其他动作时按实际状态重新处理。

A/B终态分别向废液槽送入200/460µL，参与源孔记录为0、枪头已弃，孔板留在被动磁力架上。程序液量为0不表示物理无残液或未带走磁珠；完整协议另按本次方案安排后续搬离、重悬或收尾，不从本例推导统一实验SOP。

## Absorbance Plate Reader

初始化、模块盖与读数边界见module-conditions，参数及业务波长支持范围查对应API，不作为可省略的经验处理。

### 默认选板与其他品牌

来源：用户2026-11-04提供的选板经验，结合官方96孔平底板范围与实际定义核对，未作本项目实机验证。默认推荐96孔平底细胞板，先从已维护的Corning和NEST两款准确加载名中匹配实物，具体对象及安装条件唯一见installation；用户已有明确板型时不为套默认推荐而更换。
可向用户说明也能评估其他品牌的96孔平底细胞板。按准确型号及实际定义核对标准外形、尺寸、孔底透光与吸光测定适用性、模块及抓手适配，不因品牌或孔数相同就承诺可用。推荐两款不是品牌白名单，不将其他品牌直接判为不支持；官方库无匹配时再按自定义耗材流程处理，沿用原有确认规则。
Corning/NEST的定义只解决相应几何定位，不能把同一几何定义覆盖的所有颜色、底材或货号都当作已验证光学兼容。

### 加热后的温度平衡与闭盖等待

来源：用户2026-11-04提供的现场经验，未作本项目实机复验，属于场景建议而非官方API硬条件。涉及加热孵育的测定（如37℃孵育的BCA）时，先按实验方案让样品和孔板冷却、平衡到当前室温，再送入读板机，避免板仍热时出现吸光度读数波动。停用加热或移离加热模块不证明已经回到室温；不自行补固定冷却时长或把室温写死为25℃。本次有明确且已验证的测定温度/时序时，按该方案判断。
孔板搬入并关闭模块盖后，建议用protocol.delay(seconds=10)等待，再开始本次装板后的首次read；这是闭盖后稳定等待，不是冷却或热平衡的证明。空腔初始化前的close_lid及测后空腔收盖不加这段等待；未重新开盖/装板的连续读数，其间隔按具体实验安排，不机械追加。该建议不改变module-conditions中的空腔初始化与装板读数顺序。

### 结果下载与当次后续处理

接口及数据结构仍按[读数API](api-module-absorbance-plate-reader.md#absorbancereadercontextread)维护：需要运行后下载时，在read中指定export_filename导出CSV，运行后从App对应Flex的协议运行记录（Recent Protocol Runs）获取文件。当次协议后续需要取值、计算或分析时，直接保留并使用read返回的数据，不必先导出再回读CSV；同一次read可以同时满足这两种用途。参考扣减与模拟零值/不写文件的边界沿用该API，不据模拟结果声称完成了实测分析。

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
# 独立的存入示例：storage_stacker已配置为存放无适配器、无盖的单块板，仓内有余量且shuttle为空。
# labware_to_store是与仓内配置匹配且可由抓手搬运的孔板；带适配器的组合不能照抄这一行。
protocol.move_labware(labware_to_store, new_location=storage_stacker, use_gripper=True)
storage_stacker.store()
```

官方示例源：v10.0.0 docs/python-api/docs/modules/flex-stacker.md，固定身份见module-conditions的Stacker来源；相关契约见api-module-flex-stacker与共享加载API。这里保留片段，不重复复制完整官方API速查表。
