# Flex Stacker

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-flex-stacker.md) · [API与加载](api-module-flex-stacker.md)；静态安装唯一查[安装关系](installation.txt)。

来源：用户2026-10-29确认的供料使用经验；操作原则按官方机制核对，未作实机验证。以下为场景建议，必要前置条件仍唯一见[Stacker条件](module-conditions-flex-stacker.md)。

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

官方示例源：v10.0.0 docs/python-api/docs/modules/flex-stacker.md，固定身份见[Stacker来源](module-conditions-flex-stacker.md#条件约束)；相关契约见api-module-flex-stacker与共享加载API。这里保留片段，不重复复制完整官方API速查表。

### 连续供料与对象引用

来源：用户提供stacker_test.py的供料片段（SHA-256 db036afd6a0ee3b540664f72fa695aadd42f3cdbfe48b2b4664c4fa98b6701b5），按已有Stacker API整理。展示官方模块对象维护仓内库存、retrieve返回原生耗材，再按实验需要搬运和处理盖子的组织方式。

以下为独立片段：仓内已人工预装3盒带匹配盖的50µL枪头盒、shuttle初始为空；B2/C2/D2空闲且路径、抓手及垃圾槽配置已确认。盖子在本例送到外置垃圾槽，实际去向按本次流程选择。

```python
stacker = protocol.load_module("flexStackerModuleV1", "A4")
stacker.set_stored_labware(
    load_name="opentrons_flex_96_tiprack_50ul", count=3,
    lid="opentrons_flex_tiprack_lid",
)
chute = protocol.load_waste_chute()

retrieved_labware = []
for destination in ["B2", "C2", "D2"]:
    labware = stacker.retrieve()
    retrieved_labware.append(labware)
    protocol.move_labware(labware, new_location=destination, use_gripper=True)
    protocol.move_lid(labware, new_location=chute, use_gripper=True)

# 每个元素保留一次retrieve返回的原生耗材对象，供后续实验使用。
```

仓内数量随官方retrieve更新，不另写剩余计数、不反复set_stored_labware，也不用把全部仓内状态复制进自定义类。需要查看时使用get_stored_labware；这是协议跟踪库存，不是设备实时感知盘点。retrieved_labware只是本例已成功取出的对象引用集合，不是仓内库存副本，也不证明后续搬运/移盖已完成；不需要保留全部引用的流程可直接使用当前返回对象。

每次先搬离shuttle，才继续下一次retrieve；若工作位已有旧耗材，按本次确定的去向先释放工作位。异常继续上抛，保留已经完成的取出/位置事实，不自动再取一件、搬回或重新声明库存。该片段仅作组合参考，最终可按实验步骤组织或改写，不要求套用固定函数。
