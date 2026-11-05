# 混匀衔接与N次手写混匀片段

仅实现参考，按已命中的权威规则与本次前提使用；已读取内容直接复用。

## 加液后原位立即混匀

仅当同孔同枪头且无模式切换/需退出的准备动作。按[连续原位混匀](operations.md#连续原位混匀枪头连续性--位置--模式准备需求)在本次加液前选定dynamic_mix，使用[常规一吸一排](patterns-common.md#常规一吸一排)的吸液段，替换目标进入和排液段如下，随后直接接混匀片段，不插入top或prepare_to_aspirate。initial_push_out仍由统一规则判定；明确的位置覆盖、起终点可达性及等待均按原规则，不在此另立数值或选型条件。

```python
addition_start = (destination.meniscus(z=-0.5, target="start")
                  if dynamic_mix else destination.bottom(z=0.8))
addition_location = (destination.meniscus(z=-0.5, target="dynamic")
                     if dynamic_mix else destination.bottom(z=0.8))
pipette.move_to(destination.top())
pipette.move_to(addition_start, speed=entry_speed)
protocol.delay(seconds=before_dispense_delay)
pipette.dispense(volume, location=addition_location,
                 flow_rate=dispense_flow_rate, push_out=initial_push_out)
protocol.delay(seconds=after_dispense_delay)
```

若bottom(0.8)恰与已知液面重合，统一push_out判定仍适用；如因此启用非零push_out导致后续需要液面外准备，则不再符合原位立即混匀条件，使用下方退出/准备路径。不得为了保持模板假定而忽略活塞状态。

## 需要切换模式后混匀

先完成常规动态排液并校验空枪头，再执行下段，接所选模式的混匀片段。configure_for_volume仅适用于需切换模式的Flex50µL单/八通道；无模式切换但需液面外准备时省略该行。configure_volume依据已查API及计划模式确定。

```python
pipette.move_to(destination.top(), speed=exit_speed)
protocol.delay(seconds=after_dispense_retract_delay)
pipette.configure_for_volume(configure_volume)
pipette.prepare_to_aspirate()
mix_entry = (destination.meniscus(z=-0.5, target="start")
             if dynamic_mix else destination.bottom(z=0.8))
pipette.move_to(mix_entry, speed=entry_speed)
protocol.delay(seconds=mix_submerge_delay)
```

## N次手写混匀，保留液与末次排净

进入时空枪头、模式已匹配、已到本次吸液起点，液面外准备已完成或无需额外准备。dynamic_mix是按[模式选择](operation-mixing.md#模式选择)确定的内部布尔值，不是默认新增的运行参数；模式依据与以下执行片段分开。mix_volume=M、stroke_volume=S及N>=1依据[混匀规则](operation-mixing.md)确定，数值表达按参数化指引选择。aspirate_full_rate/aspirate_stroke_rate分别按实际M/S查询，排液同理。首次实际入液后的等待由进入段执行一次；普通轮次不重复添加。以下未拆分末排须在生成时按“分段排空”展开。

```python
mix_aspirate_location = (well.meniscus(z=-0.5, target="dynamic")
                         if dynamic_mix else well.bottom(z=0.8))
for cycle in range(mix_cycles):
    first_cycle = cycle == 0
    last_cycle = cycle == mix_cycles - 1
    pipette.aspirate(mix_volume if first_cycle else stroke_volume,
                    location=mix_aspirate_location,
                    flow_rate=aspirate_full_rate if first_cycle else aspirate_stroke_rate)
    protocol.delay(seconds=aspirate_delay)
    if last_cycle:
        pipette.dispense(mix_volume,
            location=well.bottom(z=0.8),
            end_location=well.meniscus(z=0, target="end"),
            flow_rate=dispense_full_rate, push_out=final_push_out)
    elif dynamic_mix:
        pipette.dispense(stroke_volume,
            location=well.bottom(z=0.8),
            end_location=well.meniscus(z=-0.5, target="end"),
            flow_rate=dispense_stroke_rate, push_out=ordinary_push_out)
    else:
        pipette.dispense(stroke_volume, location=well.bottom(z=0.8),
            flow_rate=dispense_stroke_rate, push_out=ordinary_push_out)
    protocol.delay(seconds=dispense_delay)
```

N=1只执行一次吸M及共用末排，不预吸保留量。动态最后一次吸液仍跟随液面；末次排液两模式都从bottom(0.8)边排边移至本次排完后液面0，不能提前到液面再排。普通动态排液终点按当前动作结束后的实际孔内量解析（标准留液轮按该孔实际喷嘴数，为 F−n×R），最后回到F；不把每轮终点都当作完整F。meniscus标记按每次命令的状态解析，不是预先冻结的高度。明确体积位置可采用[按体积确定排液终点](patterns-common.md#按体积确定排液终点)的height_from_volume示例。无模型不直接使用本片段的液面路径，按operations“液量模型核对与缺失处理”确认并替换对应位置；弃头/返回由后续流程决定。等待、push_out、准备及拆段分别查delays、operations和[分段排空](operation-dispense.md#分段排空)，不在此另设数值规则。

## 实例路由

组合演示见mixing-examples.md的静态、动态两个主例，覆盖前次加液、N=1/多轮、容量截断、保留液及末排分段；模式切换参考本页片段，后续吸液准备参考[活塞状态跨步骤衔接](patterns-common.md#活塞状态跨步骤衔接)；执行条件仍按已命中的权威规则。实例的数值与轮次只适用于其前提，不升格为全局默认；实际应用重新查询流速和等待，不把实例定值变成另一套参数表。
