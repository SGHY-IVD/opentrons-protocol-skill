# 静态与动态混匀实例

## 目录
- 查用与共同前提
- A：静态混匀示例
- B：动态混匀示例
- 其他衔接

## 查用与共同前提
模式、体积与轮次依据[operations“手写混匀”](operations.md#手写混匀)；加液衔接按[组合校验](operations.md#组合校验)，原子结构见[patterns](patterns.md)。A以用户明确要求静态为前提，B展示默认动态；这里只组合两个具体算例，不另设选择条件或默认，实际协议不要求保留函数名或组织形式。

两个主例均为Flex八通道1000配200µL普通枪头、水相，每通道枪头已吸入100µL且源孔退出已完成；目标是八个独立板孔，每孔只接一个喷嘴（n=1），以下总量均指其中一个孔。共享槽另按operations的逐孔账本。没有待准备事件，无需切换移液器体积模式，使用同一枪头加液后立即混匀。目标孔的示例前提为深40mm、容量2000µL，具备有效液量模型并按下表加液前体积初始化；全部实际位置和路径可达。这是局部算例，不指代具体装机耗材，也不是可直接上机的完整protocol。

dry_run已由完整协议解析为bool；本例取正式3轮、用水试运行1轮，只示范两种轮次，实际次数按本次方案及operations确定。水相两分支流速相同，只有轮次变化。入液/退出20mm/s，入液、吸后及排后等待0.2秒，撤离后无有效等待。流速已按实际动作量查询flow_rate.py；实际换量、枪头或液体时重新查rates/delays，不把示例定值当成另一套参数表。

|主例|加液前→加液后F|70%推荐量→容量后M|多轮时R / S|模式依据|
|---|---|---|---|---|
|A|100→200µL|140→140µL|14 / 126µL|用户明确静态|
|B|500→600µL|420→200µL，需说明容量截断|20 / 180µL|默认动态|

两例择一用于符合各自前提的孔。N=1仅吸M再排M，不预吸保留液；多轮的M已包含R，不能额外加R超过容量。所有液面标记依赖当前有效模型及逐步液量账本，不是持续实测；位置边界与明确覆盖继续按原规则核对。

## A：静态混匀示例
本例用户明确要求静态混匀。前次加液及普通吸排保持bottom(0.8)。首轮吸140µL，非末轮排126µL、保留14µL；后续吸126µL恢复枪头内140µL。末次排净按130+10µL展开，最终孔内恢复200µL。

```python
def add_then_fixed_mix(protocol, pipette, well, dry_run):
    # 前次加液：目标孔原有100µL，枪头已有100µL。
    pipette.move_to(well.top())
    pipette.move_to(well.bottom(z=0.8), speed=20)
    protocol.delay(seconds=0.2)
    pipette.dispense(100, location=well.bottom(z=0.8),
        flow_rate=200, push_out=0)
    protocol.delay(seconds=0.2)

    # 示例轮次：正式3轮，用水试运行1轮。
    mix_cycles = 1 if dry_run else 3
    for cycle in range(mix_cycles):
        pipette.aspirate(140 if cycle == 0 else 126,
            location=well.bottom(z=0.8),
            flow_rate=220 if cycle == 0 else 201.333333)
        protocol.delay(seconds=0.2)
        if cycle == mix_cycles - 1:
            pipette.dispense(130, location=well.bottom(z=0.8),
                end_location=well.meniscus(z=0, target="end"),
                flow_rate=230, push_out=0)
            protocol.delay(seconds=0.2)
            pipette.dispense(10, location=well.meniscus(z=0, target="start"),
                end_location=well.meniscus(z=0, target="end"),
                flow_rate=40, push_out=3)
        else:
            pipette.dispense(126, location=well.bottom(z=0.8),
                flow_rate=226, push_out=0)
        protocol.delay(seconds=0.2)
    pipette.move_to(well.top(), speed=20)
```

## B：动态混匀示例
前次加液及每次吸液使用液面下0.5mm动态定位；普通排180µL从bottom(0.8)移至该次排完后的液面下0.5mm，孔内量为F−R=580µL。最后一次吸液仍动态，末次排净才共用底部起排至液面0的路径，分为190+10µL，分别对应孔内590/600µL；末段从中间液面连续排，不回底部。

```python
def add_then_dynamic_mix(protocol, pipette, well, dry_run):
    # 前次加液：目标孔原有500µL，枪头已有100µL。
    pipette.move_to(well.top())
    pipette.move_to(well.meniscus(z=-0.5, target="start"), speed=20)
    protocol.delay(seconds=0.2)
    pipette.dispense(100, location=well.meniscus(z=-0.5, target="dynamic"),
        flow_rate=200, push_out=0)
    protocol.delay(seconds=0.2)

    # 示例轮次：正式3轮，用水试运行1轮。
    mix_cycles = 1 if dry_run else 3
    for cycle in range(mix_cycles):
        pipette.aspirate(200 if cycle == 0 else 180,
            location=well.meniscus(z=-0.5, target="dynamic"),
            flow_rate=300 if cycle == 0 else 273.333333)
        protocol.delay(seconds=0.2)
        if cycle == mix_cycles - 1:
            pipette.dispense(190, location=well.bottom(z=0.8),
                end_location=well.meniscus(z=0, target="end"),
                flow_rate=290, push_out=0)
            protocol.delay(seconds=0.2)
            pipette.dispense(10, location=well.meniscus(z=0, target="start"),
                end_location=well.meniscus(z=0, target="end"),
                flow_rate=40, push_out=3)
        else:
            pipette.dispense(180, location=well.bottom(z=0.8),
                end_location=well.meniscus(z=-0.5, target="end"),
                flow_rate=280, push_out=0)
        protocol.delay(seconds=0.2)
    pipette.move_to(well.top(), speed=20)
```

两例加液后均保留该次排后等待，直接接首次混匀吸液；普通轮次之间不退出、不准备或重复入液等待。结束时枪头记账归零并退出至top，非零push_out只留下待准备状态，不在收尾提前准备。

## 其他衔接
- 只需混匀、没有前次加液时：以空枪头按patterns完成所需准备与受控进入，再复用相应混匀段；根据本次实际F实例化体积/速率，不保留本例的100µL加液。
- 必须切换移液器体积模式时：不满足原位立即混匀资格，直接查[patterns“需要切换模式后混匀”](patterns.md#需要切换模式后混匀)。例如50µL枪头在低体积模式持2µL加入已有98µL的孔后，先常规排空、退出top、切回正常模式并准备，再进入所选混匀起点；推荐70µL受正常模式/枪头容量限制取M=50µL。不能按旧低体积模式容量截断后直接混匀。
- 后续还要吸液时：按[patterns“活塞状态跨步骤衔接”](patterns.md#活塞状态跨步骤衔接)在下一吸液孔top、空枪头状态准备，再控速进入本次实际吸液位置。没有下一次吸液就不触发；取弃/返回枪头由实际流程另行处理。
