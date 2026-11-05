# Magnetic Block

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-magnetic-block.md) · [API与加载](api-module-magnetic-block.md)；静态安装唯一查[安装关系](installation.txt)。

### 弹性支撑与低位吸液

来源：用户2026-11-04提供的现场提示；弹簧支撑机制见[模块说明](module-conditions-magnetic-block.md#magnetic-block)。评估磁力架上孔板的近底或特殊低位吸液时，可将该结构作为接触缓冲的参考因素，不将其理解为没有触底接触或仅凭弹性放行过低/负高度。实际高度及可达性仍按[空间位置与路径规则](operations.md#空间位置与路径)核对；本提示不设置新的最低高度、下压量或自动覆盖默认值，未作本项目实机复验。

### 热震荡后转入磁力架时的放置偏移

来源：用户2026-11-04提供的现场经验，未作本项目实机复验，属于可选操作技巧，不是官方效果保证或默认搬运高度。
孔板经过热震荡且孔壁附液、随后需要移至磁力架时，可按实际耗材和模块组合，在该次抓手搬运move_labware(..., use_gripper=True)中设置drop_offset={"x": 0, "y": 0, "z": 1.0}，也可将该字典中的z改为2.0（单位mm），尝试利用略高释放后的落座动作帮助壁上液滴回落。正Z是在既有放置坐标上增加的偏移，不等同于精确自由落高；取值须结合实际落座、定位及是否飞溅核对，不推广到其他搬运动作。
该参数只调整本次放置动作，不修改耗材定义或吸排液高度，也不代替既有模块搬运前置条件；调用契约见[搬运API](api-gripper.md#protocolcontextmove_labware)，模块条件见[磁力架条件](module-conditions-magnetic-block.md)；本次由热震荡搬出时另查[热震荡搬出条件](module-conditions-heater-shaker.md#条件约束)。

### 磁吸后去上清操作示例

动作、默认值和边界唯一见[场景规则](operation-magnetic-supernatant.md#磁吸后去上清)，单批结构见[原子片段](patterns-magnetic-supernatant.md#磁吸后去上清单批吸液)。以下按“共用准备→A/B输入二选一→共用执行”组成两例，是API2.30的run体片段，不是可直接上传的完整协议；sop_magnetic_seconds须在进入前由实际SOP给出并预检，不猜磁吸时间。只展示正常运行水相分支，完整协议的dry_run仍按rates解析各次实际量，不自动共用本例吸液速度。

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
