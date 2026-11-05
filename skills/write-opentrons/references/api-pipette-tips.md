# 移液器API · 取头、弃头与回头

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.pick_up_tip](#instrumentcontextpick_up_tip)
- [InstrumentContext.drop_tip](#instrumentcontextdrop_tip)
- [InstrumentContext.return_tip](#instrumentcontextreturn_tip)

## InstrumentContext.pick_up_tip

官方来源


```python
pick_up_tip(
    location: Location | Well | Labware | None = None,
    presses: int | None = None,
    increment: float | None = None,
    prep_after: bool | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 location Location | Well | Labware | None None 位置或关键字 presses int | None None 位置或关键字 increment float | None None 位置或关键字 prep_after bool | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Pick up a tip for the pipette to run liquid-handling commands. See Picking Up a Tip . If no location is passed, the pipette will pick up the next available tip in its tip_racks list. Within
each tip rack, tips will be picked up in the order specified by the labware
definition and Labware.wells() . To
adjust where the sequence starts, use starting_tip . The exact position for tip pickup accounts for the length of the tip and how
much the tip overlaps with the pipette nozzle. These measurements are fixed
values on Flex. Note API version 2.19 updates the tip overlap values for Flex. When updating a
protocol from 2.18 (or lower) to 2.19 (or higher), pipette performance
should improve without additional changes to your protocol. Nevertheless, it
is good practice after updating to do the following: Run Labware Position Check. Perform a dry run of your protocol. If tip position is slightly higher than expected, adjust the location parameter of pipetting actions to achieve the desired result. Parameters: location ( Location | Well | Labware | None , default: None )
          – The location from
which to pick up a tip. The location argument can be specified in
several ways: As a Well . For example, pipette.pick_up_tip(tiprack.wells()[0]) will always pick up the first
tip in tiprack , even if the rack is not a member of InstrumentContext.tip_racks . As a labware. pipette.pick_up_tip(tiprack) will pick up the next
available tip in tiprack , even if the rack is not a member of InstrumentContext.tip_racks . As a Location . Use this to make fine adjustments to the pickup
location. For example, to tell the robot to start its pick up tip
routine 1 mm closer to the top of the well in the tip rack, call pipette.pick_up_tip(tiprack["A1"].top(z=-1)) . presses ( int , default: None )
          – The number of times to lower and then raise the
pipette when picking up a tip, to ensure a good seal. Zero ( 0 ) will
result in the pipette hovering over the tip but not picking it up
(generally not desirable, but could be used for a dry run). Deprecated in version 2.14 : Use the Opentrons App to change pipette
pick-up settings. increment ( float , default: None )
          – The additional distance to travel on each
successive press. For example, if presses=3 and increment=1.0 , then
the first press will travel down into the tip by 3.5 mm, the second by
4.5 mm, and the third by 5.5 mm). Deprecated in version 2.14 : Use the Opentrons App to change pipette
pick-up settings. prep_after ( bool , default: None )
          – Whether the pipette plunger should prepare
itself to aspirate immediately after picking up a tip. If True , the pipette will move its plunger position to bottom in
preparation for any following calls to aspirate() . If False , the pipette will prepare its plunger later, during the next
call to aspirate() .
This is accomplished by moving the tip to the top of the well, and
positioning the plunger outside any potential liquids. Warning This is provided for compatibility with older Python Protocol API
behavior. You should normally leave this unset. Setting prep_after=False may create an unintended pipette
movement, when the pipette automatically moves the tip to the top of
the well to prepare the plunger. Returns: InstrumentContext ( InstrumentContext )          – This instance. New in version 2.13 : Adds the prep_after argument. In version 2.12
and earlier, the plunger can't prepare itself for aspiration during pick_up_tip() ,
and will instead always prepare during aspirate() .
Version 2.12 and earlier will raise an APIVersionError if a value is
set for prep_after . Changed in version 2.19 : Uses new values for how much a tip overlaps
with the pipette nozzle.


## InstrumentContext.drop_tip

官方来源


```python
drop_tip(
    location: Location | Well | TrashBin | WasteChute | None = None,
    home_after: bool | None = None,
    alternate_drop_location: bool | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 location Location | Well | TrashBin | WasteChute | None None 位置或关键字 home_after bool | None None 位置或关键字 alternate_drop_location bool | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Drop the current tip. See Dropping a Tip for examples. If no location is passed (e.g. pipette.drop_tip() ), the pipette will drop
the attached tip into its trash_container . The location in which to drop the tip can be manually specified with the location argument. The location argument can be specified in several
ways: As a Well . This uses a default
    location relative to the well. This style of call can be used to make the
    robot drop a tip into labware like a well plate or a reservoir. For
    example, pipette.drop_tip(location=reservoir["A1"]) . As a Location . For example, to drop a tip
    from an unusually large height above the tip rack, you could call pipette.drop_tip(tip_rack["A1"].top(z=10)) . As a TrashBin . This uses a default
    location relative to the TrashBin object. For example, pipette.drop_tip(location=trash_bin) . As a WasteChute . This uses a
    default location relative to the WasteChute object. For example, pipette.drop_tip(location=waste_chute) . In API versions 2.15 to 2.17, if location is a TrashBin or not specified,
the API will instruct the pipette to drop tips in different locations within
the bin. Varying the tip drop location helps prevent tips from piling up in a
single location. Between API version 2.18 and 2.27, the API will only vary the tip drop location if location is not specified. Specifying a TrashBin as the location behaves
the same as specifying TrashBin.top() ,
which is a fixed position. Starting in API version 2.28, you can manually control whether drop_tip() varies
the drop location with alternate_drop_location . Parameters: location ( Location | Well | TrashBin | WasteChute | None , default: None )
          – Where to drop the tip. Changed in version 2.16 : Accepts TrashBin and WasteChute values. home_after ( bool | None , default: None )
          – Whether to home the pipette's plunger after dropping the tip.
When False , the pipette does not home its plunger. This can save a few
seconds, but is not recommended. Homing helps the robot track the
pipette's position. alternate_drop_location ( bool | None , default: None )
          – Whether to vary the tip drop position to prevent tips from piling up in
one spot. If not specified, the API will vary tip drop position by default when location is None , and drop the tip to a fixed position when location is specified. New in version 2.28 Returns:
    This instance.


## InstrumentContext.return_tip

官方来源


```python
return_tip(home_after: bool | None = None) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 home_after bool | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Drop the currently attached tip in its original location in the tip rack. Returning a tip does not reset tip tracking, so Well.has_tip will remain False for the destination. Returns: InstrumentContext – This instance. Parameters: home_after ( bool | None , default: None )
          – See the home_after parameter of drop_tip() .
