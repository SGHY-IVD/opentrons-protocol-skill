# 梯度稀释流程参考

## 定位与适用范围
本文件仅是快速查用法的完整组合示例，核心规则与原子模板优先；可以不参考本文件重新生成。实际脚本只保留所需阶段，运行时确需切换的才保留为参数。不建立大函数/通用实验框架，不从本文件复制流速默认。
等倍、各级等体积转移；首孔原液均匀；同一移液器模式下完成加液和混匀；完整通道取头。至少2个梯度孔。四个独立选择：stock_preloaded、diluent_preloaded、change_tips_between_steps、remove_final_excess。末孔另有final_disposal="trash"或"waste_well"，必须明确。末孔移除统一为吸液→排入指定废液位置→处理枪头；垃圾桶与废液孔只区别排液目标，不设带液直接弃头分支。

## 输入与预检查
所有下列变量先按当前流程赋值，禁止未定义占位交付。体积/流速按规则生成阶段计算；等待查询delays.md的官方阶段配置，明确指定优先；有模型且初始化为0的空孔首次加液同样采用常规动态液面排液，不需要另给固定起点。source/destination为真实孔，完整八通道时为列主孔；初始化须覆盖所有通道实际参与孔。
- dilution_wells按梯度顺序；first_column_wells、target_column_wells为用于批量初始化的全部实际孔，勿只标主孔。stock_source_wells、diluent_source_wells及其labware指向实际源孔/耗材。共享槽声明的是多通道总供液量。
- first_well_initial_volume（已就位量）、stock_load_volume（未就位加样量）、diluent_volume、transfer_volume、mixed_well_volume、mix_volume、stroke_volume、final_remove_volume分别核算；两种首孔路径应满足实验所需起始量。末孔移除量不超可吸量。
- 移动速度按各阶段源液/目标接触液分别确定，使用下列分阶段变量；级间类别改变时在对应迭代赋值，不把原液、稀释液与混合液共用一套速度。数值一致时最终脚本可合并变量。
- 每步实际体积查询对应flow_rate；全部push_out依operations判定。原位立即混匀的addition_push_out应符合不需退出准备的条件；若不符则替换入口，不强套本例。
- tip位置按阶段分配且不重叠；return_tips不意味着跨浓度随意复用。移液器tip_racks和trash_container已加载。dry_run按rates.md统一切换水相吸排速率，并改变确认过的等待/混匀次数，不自行取消末孔液体去向。所有流速变量按patterns.md先完成正常/水相定值选择，覆盖原液、稀释液、级间转移、混匀及末孔移除。
- 本例stock_source为均匀原液，首孔不另加稀释液，首次加样后不额外混匀。小体积定位、容量分批、模式切换或无模型等不满足本例条件时，从原子模板替换相应部分。

## 完整参考片段

```python
# 具体脚本注明实际读取的技能版本与覆盖项，不能把本示例当已验证协议。
first_well = dilution_wells[0]
final_well = dilution_wells[-1]
target_wells = dilution_wells[1:]
mix_cycles = dry_run_mix_cycles if dry_run else normal_mix_cycles

# 1. 初始化实际起始液量与用途标签
stock_liquid = protocol.define_liquid(name="原液", display_color=stock_color)
diluent_liquid = protocol.define_liquid(name="稀释液", display_color=diluent_color)
reaction_liquid = protocol.define_liquid(name="稀释孔", display_color=empty_color)
if stock_preloaded:
    plate.load_liquid(wells=first_column_wells,
                     volume=first_well_initial_volume, liquid=stock_liquid)
else:
    plate.load_liquid(wells=first_column_wells, volume=0, liquid=reaction_liquid)
    stock_labware.load_liquid(wells=stock_source_wells,
                             volume=stock_source_initial_volume, liquid=stock_liquid)
if diluent_preloaded:
    plate.load_liquid(wells=target_column_wells,
                     volume=diluent_volume, liquid=diluent_liquid)
else:
    plate.load_liquid(wells=target_column_wells, volume=0, liquid=reaction_liquid)
    diluent_labware.load_liquid(wells=diluent_source_wells,
                               volume=diluent_source_initial_volume, liquid=diluent_liquid)
if remove_final_excess and final_disposal == "waste_well":
    waste_liquid = protocol.define_liquid(name="废液", display_color=waste_color)
    waste_labware.load_liquid(wells=waste_wells,
                             volume=waste_initial_volume, liquid=waste_liquid)

# 2. 可选预铺；此处仅展示逐孔一吸一排
if not diluent_preloaded:
    if return_tips:
        pipette.pick_up_tip(diluent_tip_position)
    else:
        pipette.pick_up_tip()
    for destination in target_wells:
        pipette.move_to(diluent_source.top())
        if destination == target_wells[0] or prefill_push_out != 0:
            pipette.prepare_to_aspirate()
        pipette.move_to(diluent_source.bottom(z=0.8), speed=diluent_source_entry_speed)
        protocol.delay(seconds=diluent_submerge_delay)
        pipette.aspirate(diluent_volume, location=diluent_source.bottom(z=0.8),
                        flow_rate=diluent_aspirate_rate)
        protocol.delay(seconds=diluent_aspirate_delay)
        pipette.move_to(diluent_source.top(), speed=diluent_source_exit_speed)
        protocol.delay(seconds=diluent_aspirate_retract_delay)
        pipette.move_to(destination.top())
        prefill_start = destination.meniscus(z=0, target="start")
        pipette.move_to(prefill_start, speed=prefill_entry_speed)
        pipette.dispense(diluent_volume,
            location=destination.meniscus(z=0, target="dynamic"),
            flow_rate=diluent_dispense_rate, push_out=prefill_push_out)
        protocol.delay(seconds=diluent_dispense_delay)
        pipette.move_to(destination.top(), speed=prefill_exit_speed)
        protocol.delay(seconds=diluent_dispense_retract_delay)
    if return_tips:
        pipette.return_tip()
    else:
        pipette.drop_tip()

# 3. 可选首孔原液加样
if not stock_preloaded:
    if return_tips:
        pipette.pick_up_tip(stock_tip_position)
    else:
        pipette.pick_up_tip()
    pipette.move_to(stock_source.top())
    pipette.prepare_to_aspirate()
    pipette.move_to(stock_source.bottom(z=0.8), speed=stock_source_entry_speed)
    protocol.delay(seconds=stock_submerge_delay)
    pipette.aspirate(stock_load_volume, location=stock_source.bottom(z=0.8),
                    flow_rate=stock_aspirate_rate)
    protocol.delay(seconds=stock_aspirate_delay)
    pipette.move_to(stock_source.top(), speed=stock_source_exit_speed)
    protocol.delay(seconds=stock_aspirate_retract_delay)
    pipette.move_to(first_well.top())
    stock_dispense_start = first_well.meniscus(z=0, target="start")
    pipette.move_to(stock_dispense_start, speed=stock_destination_entry_speed)
    pipette.dispense(stock_load_volume,
        location=first_well.meniscus(z=0, target="dynamic"),
        flow_rate=stock_dispense_rate, push_out=stock_load_push_out)
    protocol.delay(seconds=stock_dispense_delay)
    pipette.move_to(first_well.top(), speed=stock_destination_exit_speed)
    protocol.delay(seconds=stock_dispense_retract_delay)
    if return_tips:
        pipette.return_tip()
    else:
        pipette.drop_tip()

# 4. 逐级转移、原位混匀；保留最后一级枪头用于可选末孔操作
for index in range(len(dilution_wells) - 1):
    source = dilution_wells[index]
    destination = dilution_wells[index + 1]
    last_step = index == len(dilution_wells) - 2
    if index == 0 or change_tips_between_steps:
        if return_tips:
            pipette.pick_up_tip(dilution_tip_positions[index])
        else:
            pipette.pick_up_tip()
    pipette.move_to(source.top())
    if index == 0 or change_tips_between_steps or final_mix_push_out != 0:
        pipette.prepare_to_aspirate()
    pipette.move_to(source.bottom(z=0.8), speed=transfer_source_entry_speed)
    protocol.delay(seconds=transfer_submerge_delay)
    pipette.aspirate(transfer_volume, location=source.bottom(z=0.8),
                    flow_rate=transfer_aspirate_rate)
    protocol.delay(seconds=transfer_aspirate_delay)
    pipette.move_to(source.top(), speed=transfer_source_exit_speed)
    protocol.delay(seconds=transfer_aspirate_retract_delay)
    pipette.move_to(destination.top())
    pipette.move_to(destination.bottom(z=0.8), speed=transfer_destination_entry_speed)
    pipette.dispense(transfer_volume, location=destination.bottom(z=0.8),
                    flow_rate=transfer_dispense_rate, push_out=addition_push_out)
    protocol.delay(seconds=transfer_dispense_delay)
    for cycle in range(mix_cycles):
        first_cycle = cycle == 0
        last_cycle = cycle == mix_cycles - 1
        pipette.aspirate(mix_volume if first_cycle else stroke_volume,
            location=destination.bottom(z=0.8),
            flow_rate=mix_full_aspirate_rate if first_cycle else mix_stroke_aspirate_rate)
        protocol.delay(seconds=mix_aspirate_delay)
        if last_cycle:
            pipette.dispense(mix_volume, location=destination.bottom(z=0.8),
                end_location=destination.bottom(z=destination.height_from_volume(mixed_well_volume)),
                flow_rate=mix_full_dispense_rate, push_out=final_mix_push_out)
        else:
            pipette.dispense(stroke_volume, location=destination.bottom(z=0.8),
                flow_rate=mix_stroke_dispense_rate, push_out=ordinary_mix_push_out)
        protocol.delay(seconds=mix_dispense_delay)
    pipette.move_to(destination.top(), speed=mix_exit_speed)
    protocol.delay(seconds=mix_dispense_retract_delay)
    if change_tips_between_steps and not last_step:
        if return_tips:
            pipette.return_tip()
        else:
            pipette.drop_tip()

# 5. 末孔可选移除；当前在末孔top，枪头尚未处理
if remove_final_excess:
    if final_mix_push_out != 0:
        pipette.prepare_to_aspirate()
    pipette.move_to(final_well.bottom(z=0.8), speed=removal_entry_speed)
    protocol.delay(seconds=removal_submerge_delay)
    pipette.aspirate(final_remove_volume, location=final_well.bottom(z=0.8),
                    flow_rate=final_remove_aspirate_rate)
    protocol.delay(seconds=removal_aspirate_delay)
    pipette.move_to(final_well.top(), speed=removal_exit_speed)
    protocol.delay(seconds=removal_aspirate_retract_delay)
    # waste_dispense_location在生成阶段确定：
    # 已加载的trash_bin对象，或指定waste_well.top()位置。
    pipette.dispense(final_remove_volume, location=waste_dispense_location,
                    flow_rate=waste_dispense_rate, push_out=0)
    protocol.delay(seconds=removal_dispense_delay)

# 6. 废液已排出，统一处理枪头
if return_tips:
    pipette.return_tip()
else:
    pipette.drop_tip()
```

## 交付与实例化
本例prepare条件来自新取枪头或上一阶段非零push_out；若组合其他动作，须按核心规则补入其待准备事件，而非照抄条件。先检查四开关与末孔去向，按需要抽取片段。所有变量来源应可追溯到核心规则/用户指定/速率工具，不把示例变量当完整配置。保留液、流速、位置、活塞、枪头规则均不在本文件重新定义。末孔移除统一使用独立排液，按目标核对位置/速度/接收容量；不额外添加blow_out，push_out仍按核心规则。
最后交付技能标识、液体分类依据、参数来源、实际验证结果；本参考本身不构成实机验证。

等待变量按diluent/stock/transfer/mix/removal实际液体分别查询，不通用复用同一秒数。所有delay占位在生成时按enabled/effective_seconds裁剪，0秒删除。当前官方入液等待均为0，排液前无有效等待；若用户覆盖则在实际入液后添加。末孔废液排出后实际无撤离动作，不伪造撤离来添加延时。
