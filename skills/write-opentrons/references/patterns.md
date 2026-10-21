# 原子片段

片段不是完整协议。先读operations.md确定位置、模式、体积、流速、push_out及等待；以下变量均须在生成阶段赋定值，禁止未定义占位交付。数值默认只维护在规则/速率JSON，不从旧片段继承。move_to速度按既有规则或明确指定填入；等待查询delays.md的官方阶段配置，用户明确指定优先。模板不封装为通用移液函数。所有prepare_to_aspirate行都由吸液前待准备检查实例化：新头首次或存在待准备事件时保留，已准备且无新事件时省略，不因复用片段重复准备。入液/退出速度按每个实际动作所在液体分别赋值，源端与目标端不默认共用。以下delay占位仅在对应阶段启用且非零时生成；相邻片段连接时同一实际撤离的等待只执行一次。

## dry_run流速赋值

按rates.md先在生成阶段查询两套定值；以下为结构占位，不得原样交付，最终用数值或已赋定值变量替换右侧来源变量。只需选择速率，不复制整段移液流程。

```python
aspirate_flow_rate = water_aspirate_rate if dry_run else normal_aspirate_rate
dispense_flow_rate = water_dispense_rate if dry_run else normal_dispense_rate
```

混匀同样分别选择mix_aspirate_rate（M）、stroke_aspirate_rate（S）、stroke_dispense_rate（S）和final_dispense_rate（M）；一吸多分按各实际体积赋值。相同值直接合并。下列原子片段使用这些已选定的flow_rate变量。

## 活塞状态跨步骤衔接

本段只由“下一次吸液前检查”调用。blow_out/非零push_out/模式切换只标记待准备，不在收尾立即插入命令。计划下一次aspirate时，若待准备且枪头为空，才在本次吸液孔top执行下段；需要模式切换时在top先切换、再准备。没有后续吸液就不触发；换头时检查自然位于取新头之后。留液混匀普通轮次不会触发准备。生成时追踪状态即可，不必在协议里另封装状态机。
```python
pipette.move_to(current_well.top(), speed=exit_speed)
protocol.delay(seconds=previous_retract_delay)
pipette.move_to(next_source.top())
pipette.prepare_to_aspirate()
pipette.move_to(next_source.bottom(z=0.8), speed=entry_speed)
```

current_well与next_source相同时合并重复top；已经退出孔内或刚取新头时省略旧孔退液步骤。next_source的吸液位置若有明确覆盖，替换最后一行；跨孔时先从当前孔控速退到top，再跨孔到next_source.top，勿将入液/退液速度机械用于全部跨孔行程。

## 跨孔移动分段

从source孔内到destination孔内时，默认使用下面结构；entry_speed/exit_speed来自当前确认值。已经在source.top时省略首行；如果需要活塞准备，插在destination.top之后、入液之前。目标可能是bottom、meniscus或指定偏移位置，均先到目标top。

```python
pipette.move_to(source.top(), speed=exit_speed)
protocol.delay(seconds=after_aspirate_retract_delay)
pipette.move_to(destination.top())
pipette.move_to(destination.bottom(z=0.8), speed=entry_speed)
```

不能省略中间行而直接从source.top控速移到destination.bottom，否则整个跨孔段被低速限制。同孔内移动不适用跨孔补top规则，混匀普通轮次不因此抬出孔。跨耗材与跨孔同样处理。

## 沿壁路径：高度与横向偏移分开

这是空间路径片段，通常用于排液，也可组合吸液；不自带液体操作。使用前按operations的“沿壁路径”核对实际耗材孔尺寸、形状、深度及枪头空间，再确定合法偏移和高度。wall_z相对孔顶；若按孔底定位，使用well.bottom(z=wall_z)。well是本次操作孔，不限定源孔或目标孔。参数按本次任务赋值，示例不提供通用偏移或间隙值。

```python
from opentrons.types import Point

center = well.top(z=wall_z)
wall = center.move(Point(x=wall_x, y=wall_y, z=0))
wall_top = well.top().move(Point(x=wall_x, y=wall_y, z=0))
# 已完成上一孔退出；跨孔到本孔top，不使用入液低速。
pipette.move_to(well.top())
# 若后续吸液有待准备事件，在此空枪头、液面外完成准备。
pipette.move_to(center, speed=entry_speed, force_direct=True)  # 只改变Z
pipette.move_to(wall, speed=wall_move_speed, force_direct=True)  # 同高度横移
# 在wall处按实验组合aspirate或dispense，并插入适用的等待阶段。
# 下方退出段仅适用于组合动作未改变wall位置；否则按实际终点重建。
pipette.move_to(wall_top, speed=exit_speed, force_direct=True)  # 保持XY竖直退出
pipette.move_to(well.top(), speed=wall_move_speed, force_direct=True)
# 按实际液体操作放置适用的撤离后等待。
```

force_direct只用于已核对可达的同孔局部段。相邻片段已有相同top时合并重复移动；等待仅保留实际适用的非零阶段。组合吸排液时显式使用wall位置，不用未偏移的Well让其回到中心。需要移动吸排液时，另核对location/end_location和整段路径，不使液体命令隐式产生未经规划的斜向运动。任意沿壁点不自动视为液面，push_out资格仍按统一规则判断。

## 常规一吸一排

前提：空枪头，已初始化液量，完成小体积定位确认；所示bottom吸液仅适用于未被覆盖的常规场景。目标有模型且支持有效液面位置；空孔显式初始化0后也使用本常规动态路径，不额外指定固定起点。先按operations判定dispense_push_out。

```python
pipette.move_to(source.top())
pipette.prepare_to_aspirate()
pipette.move_to(source.bottom(z=0.8), speed=source_entry_speed)
protocol.delay(seconds=before_aspirate_delay)
pipette.aspirate(volume, location=source.bottom(z=0.8), flow_rate=aspirate_flow_rate)
protocol.delay(seconds=after_aspirate_delay)
pipette.move_to(source.top(), speed=source_exit_speed)
protocol.delay(seconds=after_aspirate_retract_delay)
pipette.move_to(destination.top())
pipette.move_to(destination.meniscus(z=0, target="start"), speed=destination_entry_speed)
protocol.delay(seconds=before_dispense_delay)
pipette.dispense(volume, location=destination.meniscus(z=0, target="dynamic"),
                 flow_rate=dispense_flow_rate, push_out=dispense_push_out)
protocol.delay(seconds=after_dispense_delay)
```

## 加液后原位立即混匀

仅当同孔同枪头且无模式切换/需退出的准备动作。使用常规片段的吸液段，替换目标进入和排液段如下，随后直接接混匀片段，不插入top或prepare_to_aspirate。initial_push_out由统一规则判定，不硬编码为“混匀专用”值。

```python
pipette.move_to(destination.top())
pipette.move_to(destination.bottom(z=0.8), speed=entry_speed)
pipette.dispense(volume, location=destination.bottom(z=0.8),
                 flow_rate=dispense_flow_rate, push_out=initial_push_out)
protocol.delay(seconds=after_dispense_delay)
```

若bottom(0.8)恰与已知液面重合，统一push_out判定仍适用；如因此启用非零push_out导致后续需要液面外准备，则不再符合原位立即混匀条件，使用下方退出/准备路径。不得为了保持模板假定而忽略活塞状态。

## 需要切换模式后混匀

先完成常规动态排液并校验空枪头，再执行下段，接混匀片段。configure_for_volume仅适用于需切换模式的Flex50µL单/八通道；无模式切换但需液面外准备时省略该行。configure_volume依据已查API及计划模式确定。

```python
pipette.move_to(destination.top(), speed=exit_speed)
protocol.delay(seconds=after_dispense_retract_delay)
pipette.configure_for_volume(configure_volume)
pipette.prepare_to_aspirate()
pipette.move_to(destination.bottom(z=0.8), speed=entry_speed)
```

## N次手写混匀，保留液与末次排净

进入时空枪头、模式已匹配、位于bottom(0.8)，液面外准备已完成或无需额外准备。mix_volume=M、stroke_volume=S由operations生成阶段确定并写定值。N>=1。aspirate_full_rate/aspirate_stroke_rate分别查询M/S；dispense_stroke_rate/dispense_full_rate分别查询S/M。ordinary_push_out、final_push_out各按统一规则确定。等待变量按官方阶段配置或用户明确覆盖赋值。

```python
if mix_cycles == 1:
    pipette.aspirate(mix_volume, location=well.bottom(z=0.8),
                    flow_rate=aspirate_full_rate)
    protocol.delay(seconds=aspirate_delay)
    pipette.dispense(mix_volume,
        location=well.bottom(z=0.8),
        end_location=well.bottom(z=well.height_from_volume(final_well_volume)),
        flow_rate=dispense_full_rate, push_out=final_push_out)
    protocol.delay(seconds=dispense_delay)
else:
    pipette.aspirate(mix_volume, location=well.bottom(z=0.8),
                    flow_rate=aspirate_full_rate)
    protocol.delay(seconds=aspirate_delay)
    pipette.dispense(stroke_volume, location=well.bottom(z=0.8),
                    flow_rate=dispense_stroke_rate, push_out=ordinary_push_out)
    protocol.delay(seconds=dispense_delay)
    for cycle in range(mix_cycles - 2):
        pipette.aspirate(stroke_volume, location=well.bottom(z=0.8),
                        flow_rate=aspirate_stroke_rate)
        protocol.delay(seconds=aspirate_delay)
        pipette.dispense(stroke_volume, location=well.bottom(z=0.8),
                        flow_rate=dispense_stroke_rate, push_out=ordinary_push_out)
        protocol.delay(seconds=dispense_delay)
    pipette.aspirate(stroke_volume, location=well.bottom(z=0.8),
                    flow_rate=aspirate_stroke_rate)
    protocol.delay(seconds=aspirate_delay)
    pipette.dispense(mix_volume,
        location=well.bottom(z=0.8),
        end_location=well.bottom(z=well.height_from_volume(final_well_volume)),
        flow_rate=dispense_full_rate, push_out=final_push_out)
    protocol.delay(seconds=dispense_delay)
```

最后一次排液固定从bottom(0.8)起步，使用Location类型的end_location边排边移动到排完后液面，不能提前移到液面再排。final_well_volume为排完后孔内总液量，含返回的保留液；不是mix_volume。纯混匀最终总量等于混匀开始总量。模型缺失时由用户明确终点后替换，不能使用height_from_volume。统一push_out规则适用于经模型核对的最终液面终点。弃头/返回由后续流程决定，不在混匀片段固定drop_tip。dry_run可减少N但至少1，仍走正确收尾分支。

## 按体积确定排液终点

```python
pipette.dispense(volume, location=well.bottom(z=0.8),
    end_location=well.bottom(z=well.height_from_volume(final_well_volume)),
    flow_rate=dispense_flow_rate, push_out=dispense_push_out)
protocol.delay(seconds=after_dispense_delay)
```

使用end_location时，未另行指定的location统一为操作孔well.bottom(z=0.8)；明确指定起点时替换。final_well_volume为目标时刻孔内总液量；不自写几何公式，不要求预算高度数值。是否确认液面终点、是否排空仍查统一push_out规则。无模型不能使用此换算，由用户指定固定end_location。

## 实例路由

完整组合演示见mixing-examples.md：容量截断与10%保留、低体积模式切回后混匀，以及末次push_out后的下一次吸液准备。实例的等待/移动速度只是明确设定的演示输入，不升格为全局默认。实际应用重新运行流速查询，不能把实例数字变成另一套速查表。

## 交付标识与参数

脚本顶部注释填写实际读取的write-opentrons规则版本、本次用户覆盖项；不可原样保留占位。新脚本按operations使用parameters.add_str配choices声明dry_run/return_tips，内部布尔语义默认False；查api-parameters-csv完整签名，不自造参数。返回判断需先满足operations取头限制。聊天交付按operations仅突出非水相液体对应的操作、类别及简短依据，不逐项列水相；说明技能/官方/用户覆盖/未覆盖来源、容量截断和真实验证结果。

完成吸排后若实际退出到该孔top，执行对应retract等待再跨孔/弃头；不为执行等待而另造退出动作。混匀最后一次排后的等待与退出后的等待是两项，连接收尾时不可漏掉或重复。


## 二选一参数：choice显示、布尔判断

以下示范参数声明与读取，不是完整协议；其他二选一参数采用相同结构，标签按具体行为命名。

```python
def add_parameters(parameters):
    parameters.add_str(
        variable_name="dry_run", display_name="运行方式", default="normal",
        choices=[{"display_name": "正式运行", "value": "normal"},
                 {"display_name": "用水试运行", "value": "water_test"}],
    )
    parameters.add_str(
        variable_name="return_tips", display_name="枪头处理", default="discard",
        choices=[{"display_name": "丢弃枪头", "value": "discard"},
                 {"display_name": "返回枪头", "value": "return"}],
    )

# 在run(protocol)中读取，后续原子流程使用这两个布尔变量：
dry_run = protocol.params.dry_run == "water_test"
return_tips = protocol.params.return_tips == "return"
```

return_tips仍须结合当前喷嘴配置及复用规则判断，不因choice选中返回而绕过限制。


## 50µL移液器：探测后清膜

通用规则见operations“50µL移液器探测后清膜”，跟踪原理见api-probe“液面记录与转换”。下例只演示本次已确认实例：API2.28、Flex50µL配50µL枪头、SINGLE H1，已在液面外configure_for_volume(2)，新干燥空枪头已取好；从有机相母液取2µL、液面下1mm跟随吸液。清膜水相流速、正式取液流速及等待均已按本例配置查好；其他体积/模式/位置/液体须按规则重新确定，不把2µL和-1mm推广为默认。

```python
# protocol、pipette、source由实际协议提供，dry_run为已解析的布尔值。
aspirate_rate = 33.777778 if dry_run else 7.333333
pipette.move_to(source.top())
pipette.prepare_to_aspirate()
pipette.measure_liquid_height(source)

pipette.move_to(source.top(z=2), speed=10)
# 低体积模式清膜30µL；正式/试运行均按水相，原位吸排不传location。
pipette.aspirate(30, flow_rate=29.5)
protocol.delay(seconds=0.2)
pipette.dispense(30, flow_rate=50, push_out=0)
protocol.delay(seconds=0.2)

# 此时无需重复准备；以保留的探测体积换算液面。
pipette.move_to(source.meniscus(z=-1, target="start"), speed=10)
pipette.aspirate(2, location=source.meniscus(z=-1, target="dynamic"),
                 flow_rate=aspirate_rate)
protocol.delay(seconds=0.2)
pipette.move_to(source.top(), speed=10)
protocol.delay(seconds=0.5)
```

本例探测前已准备，之后无模式切换/非零push_out，因此清膜前及正式取液前不重复准备；其他前置状态按operations检查。模板止于离开源孔，2µL仍在枪头中，交由后续加样流程处理。该片段在官方10.1.0/API2.28模拟验证，不能替代实机验证。
