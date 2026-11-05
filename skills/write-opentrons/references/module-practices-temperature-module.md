# Temperature Module

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-temperature-module.md) · [API与加载](api-module-temperature-module.md)；静态安装唯一查[安装关系](installation.txt)。

沿用共用经验中的温控与停用分支，不套用模块盖/锁扣操作。按本次动作读取相应完整小节：人工初始装载时查[开始装载](module-practices-common.md#开始装载)中的温控分支；运行中处理已知/未知状态时查[状态组织](module-practices-common.md#运行中按已知状态组织)；到温与孵育期间选择等待方式时查[并发选择](module-practices-common.md#按等待对象选择并发)；正常结束或持续保温时查[收尾](module-practices-common.md#正常结束与持续保温)的温控与停用分支。未触发的场景不展开，硬件与条件见[本设备条件](module-conditions-temperature-module.md)。

### 制冷前的侧盖准备

来源：用户2026-11-04提供的现场操作经验，尚未在本项目实机复验。涉及温控制冷时，在配置核对、上机准备或交付提示中简短提醒：打开或取下模块所在位置对应的侧边磁吸挡板，保持散热通道通畅；已明确准备好的状态不反复询问或提示。这是人工准备，不生成自动打开挡板的API，也不强制增加pause。
此处指模块排风/走线用的可拆侧盖（side cover），不是透明侧窗、前门或顶板。官方[术语表](https://docs.opentrons.com/flex/glossary/#side-covers)及[Flex安装步骤](https://docs.opentrons.com/temperature-module/installation-flex/)确认其用途，2026-11-04在线核对，未固定修订；“磁吸、制冷前打开/取下”的具体做法按上述用户经验记录，不声称官方逐字规定。排风朝向的官方条件仍唯一见installation。

### 低温暂存与冷凝

来源：用户2026-11-04提供的场景经验，结合[本设备条件](module-conditions-temperature-module.md)中的官方冷凝与温度机制；未作本项目实机验证。长时间低温时主动考虑模块及耗材的冷凝，尤其关注敞口试剂孔/管：检查冷凝水是否进入、滴入或随操作带入体系，以及对实际液量、浓度和后续操作的影响。这些是风险检查方向，不将敞口耗材必然被稀释说成官方验证结论。
若目的只是运行期间低温暂存，且试剂说明、SOP或稳定性依据允许，可建议8–10℃，不为追求更冷而采用更低设定。该范围是有条件的用户经验，不是所有试剂的默认温度，不覆盖明确4℃、2–8℃或其他保存/反应要求，也不能保证不冷凝。模块设定与样品液温分别判断；实际保温时间和起点按实验决定。

### 官方建议的应用

来源：2026-11-04核对[温控条件](module-conditions-temperature-module.md)所引官方温度特性与环境条件，在线内容未固定修订，未作本项目实机验证。官方建议与据此形成的应用判断分开使用：

- 对实际液温有明确要求的应用，官方建议实测样品内部温度，判断是否需要调整温控方案；按实际铝块、耗材和液量验证。更换这些条件后重新判断原验证是否适用，是据此形成的应用建议，不自动补偿设定温度或强制所有实验增加探测动作。
- 制冷效果验证和重复运行时留意环境温度。官方列20–22℃为最佳制冷的推荐环境、20–25℃为可接受环境；这些是环境指标，不是模块目标温度，也不与前述8–10℃暂存建议混为一谈。超出推荐条件时效果可能变化，不将其改成新的API限制或固定降温耗时保证。

### 操作示例

以下三段是独立的run函数体片段，展示模块动作组合，不是可直接上传的完整协议。按本次场景选用，不要求套用其变量名、布局、温度或时长；目标示意为Flex API2.30，Task/timer例最低API2.27。D1模块、适配器、耗材及样品均假定已正确装好；制冷例另以初温高于目标、侧盖/排风准备完成及试剂条件允许为前提。
完整协议在温控前按实际孔位、液体和初始体积补充初始化，时长及dry_run沿用本次方案和操作规则；这里不虚构样品。计时均从模块到温且样品已在位后开始，不代表液体实测到温；正常收尾范围沿用[共用经验](module-practices-common.md#正常结束与持续保温)。接口及加载关系查相应API和installation，示例不另定义规则。

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

例2：异步降至10℃，到温后保持10分钟；降温和保持期间分别留出独立代码插入位。timer的计时与超时边界见[共用经验](module-practices-common.md#按等待对象选择并发)。

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
