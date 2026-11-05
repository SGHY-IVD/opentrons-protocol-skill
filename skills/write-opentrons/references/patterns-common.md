# 基础移液、路径、活塞与分段排空片段

仅实现参考，按已命中的权威规则与本次前提使用；已读取内容直接复用。

## 活塞状态跨步骤衔接

本段只由“下一次吸液前检查”调用。blow_out/非零push_out/模式切换只标记待准备，不在收尾立即插入命令。计划下一次aspirate时，若待准备且枪头为空，才在本次吸液孔top执行下段；需要模式切换时在top先切换、再准备。没有后续吸液就不触发；换头时检查自然位于取新头之后。留液混匀普通轮次不会触发准备。生成时追踪状态即可，不必在协议里另封装状态机。
```python
pipette.move_to(current_well.top(), speed=exit_speed)
protocol.delay(seconds=previous_retract_delay)
pipette.move_to(next_source.top())
pipette.prepare_to_aspirate()
pipette.move_to(next_aspirate_location, speed=entry_speed)
```

current_well与next_source相同时合并重复top；已经退出孔内或刚取新头时省略旧孔退液步骤。next_aspirate_location按下一实际吸液策略赋值：常规默认next_source.bottom(0.8)，本次采用动态混匀时取next_source.meniscus(z=-0.5,target="start")，明确位置覆盖优先；跨孔时先从当前孔控速退到top，再跨孔到next_source.top，勿将入液/退液速度机械用于全部跨孔行程。

## 跨孔移动分段

从source孔内到destination孔内时，默认使用下面结构；entry_speed/exit_speed来自当前确认值。已经在source.top时省略首行；如果需要活塞准备，插在destination.top之后、入液之前。目标可能是bottom、meniscus或指定偏移位置，均先到目标top。

```python
pipette.move_to(source.top(), speed=exit_speed)
protocol.delay(seconds=after_aspirate_retract_delay)
pipette.move_to(destination.top())
pipette.move_to(destination.bottom(z=0.8), speed=entry_speed)
protocol.delay(seconds=mix_submerge_delay)
```

不能省略中间行而直接从source.top控速移到destination.bottom，否则整个跨孔段被低速限制。同孔内移动不适用跨孔补top规则，混匀普通轮次不因此抬出孔。跨耗材与跨孔同样处理。

## 沿壁路径：高度与横向偏移分开

这是空间路径片段，通常用于排液，也可组合吸液；不自带液体操作。使用前按[沿壁路径](operation-motion-special.md#沿壁路径)核对实际耗材孔尺寸、形状、深度及枪头空间，再确定合法偏移和高度。wall_z相对孔顶；若按孔底定位，使用well.bottom(z=wall_z)。well是本次操作孔，不限定源孔或目标孔。参数按本次任务赋值，示例不提供通用偏移或间隙值。

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

## 按体积确定排液终点

```python
pipette.dispense(volume, location=well.bottom(z=0.8),
    end_location=well.bottom(z=well.height_from_volume(final_well_volume)),
    flow_rate=dispense_flow_rate, push_out=dispense_push_out)
protocol.delay(seconds=after_dispense_delay)
```

使用end_location时，未另行指定的location统一为操作孔well.bottom(z=0.8)；明确指定起点时替换。final_well_volume为目标时刻孔内总液量；不自写几何公式，不要求预算高度数值。是否确认液面终点、是否排空仍查统一push_out规则。无模型不能使用此换算，位置替代按operations“液量模型核对与缺失处理”，不默认另造end_location。

## 分段排空：两种路径

按[分段排空](operation-dispense.md#分段排空)确定body_volume、tail_volume，原push_out按核心组合条件判定；分别确定body_rate、tail_rate，数值表达按参数化指引选择，示例不另建数值表。两个默认路径按原操作择一展开，不定义通用封装函数；纯液分段的中间/最终孔内量按该孔实际喷嘴数核对 F−n×T / F，单个喷嘴作用于每个孔时退化为 F−T / F。明确按体积定位时，才使用上一节height_from_volume构造相应点。中间等待示例0.2秒，明确覆盖时替换。

常规动态液面：
```python
pipette.dispense(body_volume, well.meniscus(z=0, target="dynamic"),
                 flow_rate=body_rate, push_out=0)
protocol.delay(seconds=0.2)
pipette.dispense(tail_volume, well.meniscus(z=0, target="dynamic"),
                 flow_rate=tail_rate, push_out=final_push_out)
protocol.delay(seconds=dispense_delay)
```

显式终点（包括混匀末次）：
```python
pipette.dispense(body_volume, location=well.bottom(0.8),
    end_location=well.meniscus(z=0, target="end"),
    flow_rate=body_rate, push_out=0)
protocol.delay(seconds=0.2)
pipette.dispense(tail_volume,
    location=well.meniscus(z=0, target="start"),
    end_location=well.meniscus(z=0, target="end"),
    flow_rate=tail_rate, push_out=final_push_out)
protocol.delay(seconds=dispense_delay)
```

第一段起点遵循原路径或用户指定；第二段起点复用第一段终点，不能重新套用默认bottom(0.8)。无模型/非液面终点按operations处理。

片段衔接中的排后/撤离后等待按[等待规则](delays.md)处理；只对实际发生的阶段执行，复用已完成的等待。
