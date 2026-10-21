# 混匀组合实例

## 目录
- 适用边界
- A：容量截断与保留液
- B：低体积模式切回后混匀
- C：混匀收尾后的下一次吸液

## 适用边界
这是局部原子代码实例，不是可直接上机的完整协议。protocol、pipette、well及dry_run须由完整协议定义；实际使用先查operations、API和流速工具，实例数值不替代规则。完整协议仍含液体初始化、独立且默认False的dry_run/return_tips与真实技能版本标识。
本页水相实例在正常/dry_run下流速相同，无需增加选择分支。实例用于非水相时，按patterns.md的dry_run赋值结构分别选择M/S吸排速率，覆盖N=1与N>=2全部分支，不直接保留本页流速。
两个实例明确假设：水相；无滤芯枪头；源/目标有模型、已初始化；bottom(0.8)可达；每次吸后/排后等待0.2秒，进入/退出速度按operations：A的200µL枪头为20mm/s，B的50µL枪头为10mm/s。等待0.2秒是演示输入，不是新增默认。无模型时不能照搬动态终点。以下混匀均为每通道体积，普通轮次不退出液面。

## A：容量截断与保留液
Flex八通道1000配200µL枪头；加液后孔内300µL；当前枪头为空、活塞已准备、尖端在bottom(0.8)，无需模式切换。原算210µL，受枪头容量限制采用M=200µL；保留R=20µL，往返S=180µL。交付必须说明截断。

```python
mix_cycles = 1 if dry_run else 3
if mix_cycles == 1:
    pipette.aspirate(200, well.bottom(z=0.8), flow_rate=300)
    protocol.delay(seconds=0.2)
    pipette.dispense(200, location=well.bottom(z=0.8),
                     end_location=well.bottom(z=well.height_from_volume(300)),
                     flow_rate=300, push_out=3)
    protocol.delay(seconds=0.2)
else:
    pipette.aspirate(200, well.bottom(z=0.8), flow_rate=300)
    protocol.delay(seconds=0.2)
    pipette.dispense(180, well.bottom(z=0.8), flow_rate=280.0, push_out=0)
    protocol.delay(seconds=0.2)
    for _ in range(mix_cycles - 2):
        pipette.aspirate(180, well.bottom(z=0.8), flow_rate=273.333333)
        protocol.delay(seconds=0.2)
        pipette.dispense(180, well.bottom(z=0.8), flow_rate=280.0, push_out=0)
        protocol.delay(seconds=0.2)
    pipette.aspirate(180, well.bottom(z=0.8), flow_rate=273.333333)
    protocol.delay(seconds=0.2)
    pipette.dispense(200, location=well.bottom(z=0.8),
                     end_location=well.bottom(z=well.height_from_volume(300)),
                     flow_rate=300, push_out=3)
    protocol.delay(seconds=0.2)
```

三轮枪头状态：200→20→200→20→200→0，孔内最终恢复300µL。容量上限200µL，不是先吸200再额外加20。N=1仅200吸/排一次；不预吸保留量。

## B：低体积模式切回后混匀
Flex八通道50配50µL枪头，目前低体积模式，已吸入2µL水相准备加入已有98µL的反应孔。该2µL吸液定位已由用户明确；此片段从加液开始，不省略小体积吸液确认要求。
加液后总量100µL，70%原算70µL；规划切回常规模式后容量50µL，采用M=50µL，R=5µL，S=45µL。不能直接按旧低体积模式容量截断并原位混匀。先动态排空、退出、切模式、准备，再入液。

```python
pipette.move_to(well.top())
pipette.move_to(well.meniscus(z=0, target="start"), speed=10)
pipette.dispense(2, well.meniscus(z=0, target="dynamic"),
                 flow_rate=50, push_out=1)
pipette.move_to(well.top(), speed=10)
pipette.configure_for_volume(50)
pipette.prepare_to_aspirate()
pipette.move_to(well.bottom(z=0.8), speed=10)
mix_cycles = 1 if dry_run else 3
if mix_cycles == 1:
    pipette.aspirate(50, well.bottom(z=0.8), flow_rate=35)
    protocol.delay(seconds=0.2)
    pipette.dispense(50, location=well.bottom(z=0.8),
                     end_location=well.bottom(z=well.height_from_volume(100)),
                     flow_rate=50, push_out=1)
    protocol.delay(seconds=0.2)
else:
    pipette.aspirate(50, well.bottom(z=0.8), flow_rate=35)
    protocol.delay(seconds=0.2)
    pipette.dispense(45, well.bottom(z=0.8), flow_rate=50, push_out=0)
    protocol.delay(seconds=0.2)
    for _ in range(mix_cycles - 2):
        pipette.aspirate(45, well.bottom(z=0.8), flow_rate=33.625)
        protocol.delay(seconds=0.2)
        pipette.dispense(45, well.bottom(z=0.8), flow_rate=50, push_out=0)
        protocol.delay(seconds=0.2)
    pipette.aspirate(45, well.bottom(z=0.8), flow_rate=33.625)
    protocol.delay(seconds=0.2)
    pipette.dispense(50, location=well.bottom(z=0.8),
                     end_location=well.bottom(z=well.height_from_volume(100)),
                     flow_rate=50, push_out=1)
    protocol.delay(seconds=0.2)
```

三轮枪头状态：50→5→50→5→50→0，孔内最终恢复100µL。模式切换在无液体/液面外进行；准备只在进入前执行，留液循环内不调用。N=1仅50吸/排一次，仍需前面的模式切换与准备。流速全部逐步显式传入，不依赖模式切换后的全局默认。

最后一次（包括N=1）都从bottom(0.8)开始边排边移动，终点分别按300/100µL总液量换算，不是按200/50µL混匀量换算。微量加液的普通动态排液不受此混匀专用规则影响。

## C：混匀收尾后的下一次吸液
A/B收尾非零push_out只把活塞标为待准备。下一次aspirate的前置检查才触发下面衔接；同孔就在well.top执行，换孔则到下一吸液孔top。没有下一次吸液就无准备动作。弃头/取新头不触发准备，若换头后继续吸液，此检查自然发生在取新头之后。blow_out和模式切换同样归入这一个检查入口。
```python
pipette.move_to(well.top(), speed=exit_speed)
pipette.prepare_to_aspirate()
pipette.move_to(well.bottom(z=0.8), speed=entry_speed)
```

entry_speed/exit_speed按operations中液体类别及实际枪头规格赋值。然后接按流程确认的吸液前等待和显式flow_rate吸液。下一次为20/50µL枪头且<=10µL时，仍需满足小体积定位确认；此处bottom(0.8)不覆盖该规则。若换孔，先退出当前孔，再移动至下一孔top准备/控速进入。
