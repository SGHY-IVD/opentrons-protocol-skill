# 普通槽位叠板辅助类 Riser

目录：[用途与依赖](#用途与依赖) · [接口](#接口) · [状态与失败](#状态与失败) · [使用示例](#使用示例) · [来源与调整](#来源与调整)

## 用途与依赖

[riser.py](../assets/python/helpers/riser.py)是一个独立辅助文件，用于普通槽位中的同类孔板堆叠供料：SDK只登记当前最顶层一块板，抓手从顶部取走后，再在源位登记下一块。重新load_labware只是补充软件库存记录，不会物理补板，也没有建立整个真实板堆的上下层对象或障碍包络。

它不是官方Flex Stacker模块，不使用retrieve/store；也不是实体opentrons_flex_deck_riser适配器，不据类名推定安装了任何硬件。安装和真实堆叠关系见installation的普通槽位叠板条目；官方加载/搬运契约仍见[加载API](api-layout.md)与[搬运API](api-gripper.md)。

生成协议时把本文件完整实现（含导入、异常类及辅助函数）内嵌，再写本次实验。无需USB、第三方通讯包或兄弟源码；运行时使用传入的ProtocolContext及官方抓手搬运。导入不执行实验，构造会按初始数量登记当前板；有板时才会调用load_labware，实际抓手动作只发生在move_next_to。原附件API 2.27不作为新协议固定目标；使用第4列时另核对暂存区域所需API与甲板配置。

## 接口

```text
Riser(protocol, slot_name, load_name, quantity, stack_height_mm,
      riser_base_height_mm=0)
move_next_to(target_location, *, drop_offset=None) -> Labware
```

|参数|当前契约|
|---|---|
|protocol|当前ProtocolContext；由其加载和搬运耗材|
|slot_name|普通源槽位，非空字符串；实际安装与可达性另核对|
|load_name|本次同类板的加载名，非空字符串；本类不加载整套自定义JSON|
|quantity|非负整数，拒绝bool；0表示空库存，不登记虚拟板|
|stack_height_mm|正有限毫米数，表示相邻两层相同参考平面的高度增量；不是板总高或官方堆叠重叠量|
|riser_base_height_mm|非负有限毫米数，第一层抓取相对普通SDK位置的额外Z增量；默认0，不重复加入耗材定义自身高度|
|target_location|传给官方move_labware的目标；拒绝源槽位本身，其余目标及占用仍由本次布局和SDK核对|
|drop_offset|可选目标侧抓手偏移；默认x/y/z均为0。显式提供时只接受x/y/z有限数，缺失分量补0|

单次取板使用：

`抓取Z偏移 = riser_base_height_mm + (当前剩余数量 - 1) × stack_height_mm`

抓取X/Y偏移为0；放板使用本次drop_offset。数量、距离及计算结果在动作前检查，不硬编码所有板型的最大层数。实际层数、层间增量、整体高度、抓手可达与邻位条件须先按定义和实物核对。公式只修正取板点，不把整个板堆自动加入官方避碰模型。

|只读属性|含义|
|---|---|
|quantity|软件账本中剩余板数|
|current_labware|源位当前登记的板；空库存或下一板登记失败时为None|
|last_moved_labware|最近一次SDK正常返回的已搬出板对象；用于核对部分完成，不代表后续失败动作结果|
|faulted|搬运或后续登记失败的标记；为True时阻止继续盲目取板|

move_next_to返回本次实际传给SDK搬运的原生Labware对象，供后续液体初始化及实验使用。current_labware是普通槽位坐标的代理记录，不能直接当作已补偿顶层高度的移液位置。本类不管理液体、板盖、补货或回收压栈。

## 状态与失败

- 参数与源/目标同位检查尽量在SDK动作前完成；不建立另一套台面或模块校验框架。
- 搬运正常返回后，才减少数量、保存已搬出对象，并先清空源位引用，再登记下一块。
- 搬运成功但下一块登记失败：数量已经减少，current_labware保持None，last_moved_labware保留已搬出的对象；不把旧对象重新当成源位顶板。
- move_labware抛异常：保留最后已知数量与源位记录并标为faulted，不声称实物完全没动或已经回滚。实际状态未知时不自动扣数、重试、搬回或清除占用。
- 空库存或faulted等不可继续状态抛RiserStateError；SDK自身异常继续传播。没有自动恢复或补板流程，后续按实际状态重新规划，不通过手改计数假定实物已恢复。

## 使用示例

两组片段展示组织方式，不是完整protocol。完整实现已内嵌，实际支撑、板型、层数、抓手及源/目标布局已核对。原附件使用5层PCR板；当前维护的该板定义v4记录stackLimit=4（见installation），因此这里采用4层示意，不把原5层当作已确认兼容。层间增量由本次实物配置传入，原附件13mm只是源案例取值。

第一组：从同一源位连续取出两块，并保留不同对象引用。

```python
def riser_supply_example(protocol, *, stack_height_mm, riser_base_height_mm=0):
    riser = Riser(
        protocol, "C4", "opentrons_96_wellplate_200ul_pcr_full_skirt",
        quantity=4, stack_height_mm=stack_height_mm,
        riser_base_height_mm=riser_base_height_mm,
    )
    plate_1 = riser.move_next_to("C2")
    plate_2 = riser.move_next_to("D2")
    # 分别通过plate_1、plate_2组织后续初始化与实验步骤。
    return riser, plate_1, plate_2
```

第二组：目标使用本次已确认的抓手放板偏移；官方模块对象也按其正常加载、状态及承载条件使用。

```python
def riser_custom_target_example(
    protocol, *, source_slot, load_name, quantity, stack_height_mm,
    riser_base_height_mm, target_location, drop_offset,
):
    riser = Riser(
        protocol, source_slot, load_name, quantity,
        stack_height_mm, riser_base_height_mm,
    )
    plate = riser.move_next_to(target_location, drop_offset=drop_offset)
    return riser, plate
```

## 来源与调整

原始依据：用户提供Riser.py，SHA-256 ed4697668b4bf98b7032dc91631d1ca9fc9b3ba8ec9afaafc9fb033592628780。保留从顶层取板、按剩余层数计算Z、原位登记下一板及返回原对象的核心逻辑。

收录时移除示例协议metadata/requirements/run、未使用导入及不可达return；补充动作前参数检查、空库存、源目标同位、搬运/重载失败状态与可选目标偏移。运行文案称“堆叠板”，不冒充官方Stacker，也不向操作员显示Z计算或源码实现细节。离线验证不等同官方模拟或实机堆叠、抓手和路径验证。
