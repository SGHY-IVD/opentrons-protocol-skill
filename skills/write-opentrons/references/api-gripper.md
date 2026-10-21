# 执行命令 · 夹爪与搬运
来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

移动耗材、枪头盒和板盖；同一接口中的人工搬运用法也归这里。
ProtocolContext.move_labware ProtocolContext.move_lid

## ProtocolContext.move_labware

官方来源


```python
move_labware(
    labware: Labware,
    new_location: (
        DeckLocation
        | Labware
        | ModuleTypes
        | ModuleFixtureLocation
        | OffDeckType
        | WasteChute
        | TrashBin
    ),
    use_gripper: bool = False,
    pick_up_offset: Mapping[str, float] | None = None,
    drop_offset: Mapping[str, float] | None = None,
) -> None
```

参数名 类型 默认值 / 必填 传参方式 labware Labware 必填 位置或关键字 new_location DeckLocation | Labware | ModuleTypes | ModuleFixtureLocation | OffDeckType | WasteChute | TrashBin 必填 位置或关键字 use_gripper bool False 位置或关键字 pick_up_offset Mapping[str, float] | None None 位置或关键字 drop_offset Mapping[str, float] | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Move a loaded labware to a new location. See Moving Labware for more details. Parameters: labware ( Labware )
          – The labware to move. It should be a labware already loaded
using load_labware() . new_location ( DeckLocation | Labware | ModuleTypes | ModuleFixtureLocation | OffDeckType | WasteChute | TrashBin )
          – Where to move the labware to. This is either: A deck slot like 1 , "1" , or "D1" . See Deck Slots . A hardware module that's already been loaded on the deck
with load_module() . A labware or adapter that's already been loaded on the deck
with load_labware() or load_adapter() . The special constant OFF_DECK . use_gripper ( bool , default: False )
          – Whether to use the Flex Gripper for this movement. If True , use the gripper to perform an automatic
movement. This will raise an error in an OT-2 protocol. If False , pause protocol execution until the user
performs the movement. Protocol execution remains paused until
the user presses Confirm and resume . pick_up_offset ( Mapping [ str , float ] | None , default: None )
          – Optional x, y, z vector offset for the gripper to use when picking up labware. drop_offset ( Mapping [ str , float ] | None , default: None )
          – Optional x, y, z vector offset for the gripper to use when dropping off labware. Note Before moving a labware to or from a hardware module, make sure that the labware's
current and new locations are accessible, i.e., open the Thermocycler lid or
open the Heater-Shaker's labware latch.


## ProtocolContext.move_lid

官方来源


```python
move_lid(
    source_location: DeckLocation | Labware,
    new_location: DeckLocation | Labware | OffDeckType | WasteChute | TrashBin,
    use_gripper: bool = False,
    pick_up_offset: Mapping[str, float] | None = None,
    drop_offset: Mapping[str, float] | None = None,
) -> Labware | None
```

参数名 类型 默认值 / 必填 传参方式 source_location DeckLocation | Labware 必填 位置或关键字 new_location DeckLocation | Labware | OffDeckType | WasteChute | TrashBin 必填 位置或关键字 use_gripper bool False 位置或关键字 pick_up_offset Mapping[str, float] | None None 位置或关键字 drop_offset Mapping[str, float] | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Move a compatible lid from a valid source to a new location. Can return a lid stack if one is created. Parameters: source_location ( DeckLocation | Labware )
          – The lid's starting location. This is either: A deck slot like 1 , "1" , or "D1" . See deck slots . A labware or adapter that's already been loaded on the deck
with load_labware() or load_adapter() . A lid stack that's already been loaded on the deck with load_lid_stack() . new_location ( DeckLocation | Labware | OffDeckType | WasteChute | TrashBin )
          – Where to move the lid to. This is either: A deck slot like 1 , "1" , or "D1" . See deck slots . A hardware module that's already been loaded on the deck
with load_module() . A labware or adapter that's already been loaded on the deck
with load_labware() or load_adapter() . The special constant OFF_DECK . use_gripper ( bool , default: False )
          – Whether to use the Flex Gripper to move the lid. If True , use the gripper to perform an automatic
movement. This will raise an error in an OT-2 protocol. If False , pause protocol execution until the user
performs the movement. Protocol execution remains paused until
the user presses Confirm and resume . pick_up_offset ( Mapping [ str , float ] | None , default: None )
          – Optional x, y, z vector offset to use when picking up a lid. drop_offset ( Mapping [ str , float ] | None , default: None )
          – Optional x, y, z vector offset to use when dropping off a lid. Note Before moving a lid to or from a labware in a hardware module, make sure that the
labware's current and new locations are accessible, i.e., open the Thermocycler lid
or open the Heater-Shaker's labware latch. New in version 2.23.
