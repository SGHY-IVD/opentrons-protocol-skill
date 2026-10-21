# 执行命令 · 移液器

条目目录（可用rg按名称定位）：
- InstrumentContext.pick_up_tip
- InstrumentContext.drop_tip
- InstrumentContext.return_tip
- InstrumentContext.prepare_to_aspirate
- InstrumentContext.aspirate
- InstrumentContext.dispense
- InstrumentContext.mix
- InstrumentContext.blow_out
- InstrumentContext.air_gap
- InstrumentContext.touch_tip
- InstrumentContext.configure_for_volume
- InstrumentContext.configure_nozzle_layout
- InstrumentContext.move_to

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

取退枪头、吸排液、混匀、喷嘴切换和移动。
InstrumentContext.pick_up_tip InstrumentContext.drop_tip InstrumentContext.return_tip InstrumentContext.prepare_to_aspirate InstrumentContext.aspirate InstrumentContext.dispense InstrumentContext.mix InstrumentContext.blow_out InstrumentContext.air_gap InstrumentContext.touch_tip InstrumentContext.configure_for_volume InstrumentContext.configure_nozzle_layout InstrumentContext.move_to

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
values on Flex, and are based on the results of tip length calibration on OT-2. Note API version 2.19 updates the tip overlap values for Flex. When updating a
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
If not specified, defaults to True on an OT-2. When False , the pipette does not home its plunger. This can save a few
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


## InstrumentContext.prepare_to_aspirate

官方来源


```python
prepare_to_aspirate() -> None
```

无调用参数。

官方参数含义、返回值与使用约束（已保存在本文件） Prepare a pipette for aspiration. Before a pipette can aspirate into an empty tip, the plunger must be in its
bottom position. After dropping a tip or blowing out, the plunger will be in a
different position. This function moves the plunger to the bottom position,
regardless of its current position, to make sure that the pipette is ready to
aspirate. You rarely need to call this function. The API automatically prepares the
pipette for aspiration as part of other commands: After picking up a tip with pick_up_tip() . When calling aspirate() , if the pipette isn't
  already prepared. If the pipette is in a well, it will move out of the well,
  move the plunger, and then move back. Use prepare_to_aspirate() when you need to control exactly when the plunger
motion will happen. A common use case is a pre-wetting routine, which requires
preparing for aspiration, moving into a well, and then aspirating without
leaving the well : pipette . move_to ( well . bottom ( z = 2 )) protocol . delay ( 5 ) pipette . mix ( 10 , 10 ) pipette . move_to ( well . top ( z = 5 )) pipette . blow_out () pipette . prepare_to_aspirate () pipette . move_to ( well . bottom ( z = 2 )) protocol . delay ( 5 ) pipette . aspirate ( 10 , well . bottom ( z = 2 )) The call to prepare_to_aspirate() means that the plunger will be in the
bottom position before the call to aspirate() . Since it doesn't need to
prepare again, it will not move up out of the well to move the plunger. It will
aspirate in place.


## InstrumentContext.aspirate

官方来源


```python
aspirate(
    volume: float | None = None,
    location: Location | Well | None = None,
    rate: float = 1.0,
    flow_rate: float | None = None,
    end_location: Location | None = None,
    movement_delay: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 volume float | None None 位置或关键字 location Location | Well | None None 位置或关键字 rate float 1.0 位置或关键字 flow_rate float | None None 位置或关键字 end_location Location | None None 位置或关键字 movement_delay float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Draw liquid into a pipette tip. See Aspirate for more details and examples. Parameters: volume ( int or float , default: None )
          – The volume to aspirate, measured in µL. If
unspecified, defaults to the maximum volume for the pipette and its
currently attached tip. If aspirate() is called with a volume of precisely 0, its behavior
depends on the API level of the protocol. On API levels below 2.16,
it will behave the same as a volume of None /unspecified: aspirate
until the pipette is full. On API levels at or above 2.16, no liquid
will be aspirated. location ( Location | Well | None , default: None )
          – Tells the robot where
to aspirate from. The location can be a Well or a Location . If the location is a Well , the robot will aspirate at or above the
bottom center of the well. The distance (in mm) from the well bottom
is specified by well_bottom_clearance.aspirate . If the location is a Location (e.g., the result of Well.top() or Well.bottom() ), the
robot will aspirate from that specified position. If the location is unspecified, the robot will aspirate from its
current position. rate ( float , default: 1.0 )
          – A multiplier for the default flow rate of the
pipette. Calculated as rate multiplied by flow_rate.aspirate .
If not specified, defaults to 1.0. See Pipette Flow Rates . flow_rate ( float , default: None )
          – The absolute flow rate in µL/s. If flow_rate is specified, rate must not be set. end_location ( Location , default: None )
          – Tells the Flex to move the pipette from the specified location to the specified end_location while aspirating liquid. When this argument is used, the location and end_location must both be a Location . Raises an error if used with an OT-2 pipette. movement_delay ( float , default: None )
          – Time in seconds to delay after the pipette starts aspirating and before it begins moving
from the location to the end_location . This option is only valid when using end_location . When this
argument is used, the pipette will wait the specified time
after the pipette starts to aspirate before moving. This may help when
aspirating very viscous liquids that need to build up some pressure
before liquid starts to flow. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note If aspirate() is called with a single, unnamed argument, it will treat
that argument as volume . If you want to call aspirate() with only location , specify it as a keyword argument: pipette.aspirate(location=plate['A1']) . Changed in version 2.24 : Added the flow_rate parameter. Changed in version 2.27 : Added the end_location and movement_delay parameters.


## InstrumentContext.dispense

官方来源


```python
dispense(
    volume: float | None = None,
    location: Location | Well | TrashBin | WasteChute | None = None,
    rate: float = 1.0,
    push_out: float | None = None,
    flow_rate: float | None = None,
    end_location: Location | None = None,
    movement_delay: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 volume float | None None 位置或关键字 location Location | Well | TrashBin | WasteChute | None None 位置或关键字 rate float 1.0 位置或关键字 push_out float | None None 位置或关键字 flow_rate float | None None 位置或关键字 end_location Location | None None 位置或关键字 movement_delay float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Dispense liquid from a pipette tip. See Dispense for more details and examples. Parameters: volume ( int or float , default: None )
          – The volume to dispense, measured in µL. If unspecified or None , dispense the current_volume . If 0, the behavior of dispense() depends on the API level of the
protocol. In API version 2.16 and earlier, dispense all liquid in the
pipette (same as unspecified or None ). In API version 2.17 and later,
dispense no liquid. If greater than current_volume ,
the behavior of dispense() depends on the API level of the protocol.
In API version 2.16 and earlier, dispense all liquid in the pipette. In
API version 2.17 and later, raise an error. location ( Location | Well | TrashBin | WasteChute | None , default: None )
          – Tells the robot where to dispense liquid held in the pipette. The location can be a Well , Location , TrashBin , or WasteChute . If a Well , the pipette will dispense at or above the bottom center of
the well. The distance (in mm) from the well bottom is specified by well_bottom_clearance.dispense . If a Location (e.g., the result of Well.top() or Well.bottom() ), the
pipette will dispense at that specified position. If a trash container, the pipette will dispense at a location relative
to its center and the trash container's top center. See Position Relative to Trash Containers for details. If unspecified, the pipette will dispense at its current position. If only a location is passed (e.g., pipette.dispense(location=plate['A1']) ),
all of the liquid aspirated into the pipette will be dispensed (the amount
is accessible through current_volume ). Changed in version 2.16 : Accepts TrashBin and WasteChute values. rate ( float , default: 1.0 )
          – How quickly a pipette dispenses liquid. The speed in
µL/s is calculated as rate multiplied by flow_rate.dispense .
If not specified, defaults to 1.0. See Pipette Flow Rates . push_out ( float , default: None )
          – Continue past the plunger bottom to help ensure
all liquid leaves the tip. Measured in µL. The default value is None . When not specified or set to None , the plunger moves by a non-zero
default amount. For a table of default values, see Push Out After Dispense . flow_rate ( float , default: None )
          – The absolute flow rate in µL/s. If flow_rate is specified, rate must not be set. end_location ( `Location` , default: None )
          – Tells the Flex to move from the specified location to the specified end_location while dispensing liquid held in the pipette. When this
argument is used, the location and end_location must both be a Location . Raises an error if used with an OT-2 pipette. movement_delay ( float , default: None )
          – Time in seconds to delay after the pipette starts dispensing and before it begins moving from the location to the end_location .
This option is only valid when using end_location . When this argument
is used, the pipette will wait the specified time after the
pipette starts to dispense before moving. This may help when dispensing
very viscous liquids that need to build up some pressure before liquid
starts to flow. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note If dispense() is called with a single, unnamed argument, it will treat
that argument as volume . If you want to call dispense() with only location , specify it as a keyword argument: pipette.dispense(location=plate['A1']) . Changed in version 2.15 : Added the push_out parameter. Changed in version 2.17 : Behavior of the volume parameter. Changed in version 2.24 : Added the flow_rate parameter. Changed in version 2.24 : location is no longer required if the pipette just
moved to, dispensed, or blew out into a trash bin or waste chute. Changed in version 2.27 : Added the end_location and movement_delay parameters.


## InstrumentContext.mix

官方来源


```python
mix(
    repetitions: int = 1,
    volume: float | None = None,
    location: Location | Well | None = None,
    rate: float = 1.0,
    aspirate_flow_rate: float | None = None,
    dispense_flow_rate: float | None = None,
    aspirate_delay: float | None = None,
    dispense_delay: float | None = None,
    final_push_out: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 repetitions int 1 位置或关键字 volume float | None None 位置或关键字 location Location | Well | None None 位置或关键字 rate float 1.0 位置或关键字 aspirate_flow_rate float | None None 位置或关键字 dispense_flow_rate float | None None 位置或关键字 aspirate_delay float | None None 位置或关键字 dispense_delay float | None None 位置或关键字 final_push_out float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Mix a volume of liquid by repeatedly aspirating and dispensing it in a single
location. See Mix for examples. Parameters: repetitions ( int , default: 1 )
          – Number of times to mix (default is 1). volume ( float , default: None )
          – The volume to mix, measured in µL. If unspecified,
defaults to the maximum volume for the pipette and its attached tip. If mix() is called with a volume of precisely 0, its behavior depends
on the API level of the protocol. On API levels below 2.16, it will
behave the same as a volume of None /unspecified: mix the full working
volume of the pipette. On API levels at or above 2.16, no liquid will
be mixed. location ( Location | Well | None , default: None )
          – The location where the
pipette will mix. If unspecified, the pipette will mix at its current
position. rate ( float , default: 1.0 )
          – How quickly the pipette aspirates and dispenses
liquid while mixing. The aspiration flow rate is calculated as rate multiplied by flow_rate.aspirate .
The dispensing flow rate is calculated as rate multiplied by flow_rate.dispense .
See Pipette Flow Rates . aspirate_flow_rate ( float , default: None )
          – The absolute flow rate for each
aspirate in the mix, in µL/s. If this is specified, rate must not be
set. dispense_flow_rate ( float , default: None )
          – The absolute flow rate for each
dispense in the mix, in µL/s. If this is specified, rate must not be
set. aspirate_delay ( float , default: None )
          – How long to wait after each aspirate in
the mix, in seconds. dispense_delay ( float , default: None )
          – How long to wait after each dispense in
the mix, in seconds. final_push_out ( float , default: None )
          – How much volume to push out after the
final mix repetition. The pipette will not push out after earlier
repetitions. If not specified or None , the pipette will push out the
default non-zero amount. See Push Out After Dispense . Raises: UnexpectedTipRemovalError – If no tip is attached to the pipette. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note All the arguments of mix() are optional. However, if you omit one of them,
all subsequent arguments must be passed as keyword arguments. For instance, pipette.mix(1, location=wellplate['A1']) is a valid call, but pipette.mix(1, wellplate['A1']) is not. Changed in version 2.21 : Does not repeatedly check for liquid presence. New in version 2.24 : Added the aspirate_flow_rate , dispense_flow_rate , aspirate_delay , dispense_delay , and final_push_out parameters.


## InstrumentContext.blow_out

官方来源


```python
blow_out(
    location: Location | Well | TrashBin | WasteChute | None = None,
    flow_rate: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 location Location | Well | TrashBin | WasteChute | None None 位置或关键字 flow_rate float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Blow an extra amount of air through a pipette's tip to clear it. If dispense() is used to
empty a pipette, usually a small amount of liquid remains in the tip. During a
blowout, the pipette moves the plunger beyond its normal limits to help remove
all liquid from the pipette tip. See Blow Out . Parameters: location ( Location | Well | TrashBin | WasteChute | None , default: None )
          – The blowout location.
If no location is specified, the pipette will blow out from its current
position. Changed in version 2.16 : Accepts TrashBin and WasteChute values. flow_rate ( float | None , default: None )
          – The absolute flow rate in µL/s. New in version 2.28 Raises: RuntimeError – If no location is specified and the location cache is None .
This should happen if blow_out() is called without first calling a
method that takes a location, like aspirate() or dispense() . Returns: InstrumentContext ( InstrumentContext )          – This instance.


## InstrumentContext.air_gap

官方来源


```python
air_gap(
    volume: float | None = None,
    height: float | None = None,
    in_place: bool | None = None,
    rate: float | None = None,
    flow_rate: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 volume float | None None 位置或关键字 height float | None None 位置或关键字 in_place bool | None None 位置或关键字 rate float | None None 位置或关键字 flow_rate float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Draw air into the pipette's tip at the current well. See Air Gap . Parameters: volume ( float , default: None )
          – The amount of air, measured in µL. Calling air_gap() with no arguments uses the entire remaining volume in the
pipette. height ( float , default: None )
          – The height, in mm, to move above the current well
before creating the air gap. The default is 5 mm above the current well. in_place ( bool , default: None )
          – Air gap at the pipette's current position, without
moving to some height above the well. If in_place is specified, height must be unset. rate ( float , default: None )
          – A multiplier for the default flow rate of the pipette.
Calculated as rate multiplied by flow_rate.aspirate .
If neither rate nor flow_rate is specified, the pipette will aspirate
at a rate of 1.0 * InstrumentContext.flow_rate.aspirate . See Pipette Flow Rates . flow_rate ( float , default: None )
          – The rate, in µL/s, at which the pipette will draw
in air. Raises: UnexpectedTipRemovalError – If no tip is attached to the pipette. RuntimeError – If location cache is None and the air gap is not in_place .
This would happen if air_gap() is called without first calling a method
that takes a location (e.g., aspirate() , dispense() ). Returns: InstrumentContext ( InstrumentContext )          – This instance. Both volume and height are optional, but if you want to specify only height you must do it as a keyword argument: pipette.air_gap(height=2) . If you call air_gap with a single, unnamed argument, it will always be interpreted as a
volume. Note In API version 2.21 and earlier, this function was implemented as an aspirate,
and dispensing into a well would add the air gap volume to the liquid tracked
in the well. In API version 2.22 and later, air gap volume is not tracked as
liquid when dispensing into a well. Changed in version 2.22 : No longer implemented as an aspirate. Changed in version 2.24 : Added the in_place option. Changed in version 2.24 : Adds the rate and flow_rate parameter. You can only
define one or the other. If both are unspecified then rate is by default set to
1.0. Can air gap over a trash bin or waste chute.


## InstrumentContext.touch_tip

生成脚本时的按需启用及用户经验默认见[操作经验](operations.md#按需touch_tip)；以下签名保留官方默认值。

官方来源


```python
touch_tip(
    location: Well | None = None,
    radius: float = 1.0,
    v_offset: float = -1.0,
    speed: float = 60.0,
    mm_from_edge: float | _Unset = _Unset(),
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 location Well | None None 位置或关键字 radius float 1.0 位置或关键字 v_offset float -1.0 位置或关键字 speed float 60.0 位置或关键字 mm_from_edge float | _Unset _Unset() 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Touch the pipette tip to the sides of a well, with the intent of removing leftover
droplets. See Touch Tip for more details and examples. Parameters: location ( Well | None , default: None )
          – If no location is passed, the pipette will touch its tip at the edges of
the current well. radius ( float , default: 1.0 )
          – How far to move, as a proportion of the target well's radius.
When radius=1.0 , the pipette tip will move all the way to the edge of
the target well. When radius=0.5 , it will move to 50% of the well's
radius. Default is 1.0 (100%). v_offset ( float , default: -1.0 )
          – How far above or below the well to touch the tip, measured
in mm. A positive offset moves the tip higher above the well. A negative
offset moves the tip lower into the well. Default is -1.0 mm. speed ( float , default: 60.0 )
          – The speed for touch tip motion, in mm/s. Default: 60.0 mm/s Maximum: 80.0 mm/s Minimum: 1.0 mm/s mm_from_edge ( float , default: _Unset () )
          – How far to move inside the well, as a distance from the
well's edge. When mm_from_edge=0 , the pipette will move to the target
well's edge to touch the tip. When mm_from_edge=1 , the pipette will move
to 1 mm from the target well's edge to touch the tip. Values lower than 0
will press the tip harder into the target well's walls; higher values will
touch the well more lightly, or not at all. mm_from_edge and radius are mutually exclusive: to use mm_from_edge , radius must be
unspecified (left to its default value of 1.0). Raises: UnexpectedTipRemovalError – If no tip is attached to the pipette. RuntimeError – If no location is specified and the location cache is None .
    This should happen if touch_tip() is called without first calling a
    method that takes a location, like aspirate() or dispense() . If location is in a labware with touchTipDisabled quirk. ValueError – If both mm_from_edge and radius are specified. Returns: InstrumentContext ( InstrumentContext )          – This instance. Changed in version 2.24: Added the mm_from_edge parameter. Changed in version 2.28: The API will raise an error if touching tip on a labware with the touchTipDisabled quirk, like reservoirs or well plates with large wells.


## InstrumentContext.configure_for_volume

官方来源


```python
configure_for_volume(volume: float) -> None
```

参数名 类型 默认值 / 必填 传参方式 volume float 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Configure a pipette to handle a specific volume of liquid, measured in µL.
The pipette enters a volume mode depending on the volume provided. Changing
pipette modes alters properties of the instance of InstrumentContext , such as
default flow rate, minimum volume, and maximum volume. The pipette remains in
the mode set by this function until it is called again. The Flex 1-Channel 50 µL and Flex 8-Channel 50 µL pipettes must operate in a
low-volume mode to accurately dispense very small volumes of liquid. Low-volume
mode can only be set by calling configure_for_volume() . See Volume Modes . Note Changing a pipette's mode will reset its flow rates . This function will raise an error if called when the pipette's tip contains
liquid. It won't raise an error if a tip is not attached, but changing modes may
affect which tips the pipette can subsequently pick up without raising an error. This function will also raise an error if volume is outside of the minimum and maximum capacities of the pipette (e.g.,
setting volume=1 for a Flex 1000 µL pipette). Parameters: volume ( float )
          – The volume, in µL, that the pipette will prepare to handle.


## InstrumentContext.configure_nozzle_layout

官方来源


```python
configure_nozzle_layout(
    style: NozzleLayout,
    start: str | None = None,
    end: str | None = None,
    front_right: str | None = None,
    back_left: str | None = None,
    tip_racks: list[Labware] | None = None,
) -> None
```

参数名 类型 默认值 / 必填 传参方式 style NozzleLayout 必填 位置或关键字 start str | None None 位置或关键字 end str | None None 位置或关键字 front_right str | None None 位置或关键字 back_left str | None None 位置或关键字 tip_racks list[Labware] | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Configure how many tips the 8-channel or 96-channel pipette will pick up. Changing the nozzle layout will affect gantry movement for all subsequent
pipetting actions that the pipette performs. It also alters the pipette's
behavior for picking up tips. The pipette will continue to use the specified
layout until this function is called again. Note When picking up fewer than 96 tips at once, the tip rack must not be
placed in a tip rack adapter in the deck. If you try to pick up fewer than 96
tips from a tip rack that is in an adapter, the API will raise an error. Parameters: style ( NozzleLayout or None )
          – The shape of the nozzle layout.
You must import the layout constant in order to use it. ALL resets the pipette to use all of its nozzles. Calling configure_nozzle_layout() with no arguments also resets the pipette. COLUMN sets a 96-channel pipette to use 8 nozzles, aligned from front to back
with respect to the deck. This corresponds to a column of wells on labware.
For 8-channel pipettes, use ALL instead. PARTIAL_COLUMN sets an 8-channel pipette to use 2–7 nozzles, aligned from front to back
with respect to the deck. Not compatible with the 96-channel pipette. ROW sets a 96-channel pipette to use 12 nozzles, aligned from left to right
with respect to the deck. This corresponds to a row of wells on labware.
Not compatible with 8-channel pipettes. SINGLE sets the pipette to use 1 nozzle. This corresponds to a single well on labware. start ( str or None , default: None )
          – The primary nozzle of the layout, which the robot uses
to determine how it will move to different locations on the deck. The string
should be of the same format used when identifying wells by name.
Required unless setting style=ALL . Note If possible, don't use both start="A1" and start="A12" to pick up
tips from the same rack . Doing so can affect positional accuracy. end ( str or None , default: None )
          – The nozzle at the end of a linear layout, which is used
to determine how many tips will be picked up by a pipette. The string
should be of the same format used when identifying wells by name.
Required when setting style=PARTIAL_COLUMN . tip_racks ( list [ Labware ] , default: None )
          – Behaves the same as setting the tip_racks parameter of load_instrument() . If not specified,
the new configuration resets tip_racks and you must specify the location every time you call pick_up_tip() . Changed in version 2.20 : Added partial column, row, and single layouts.


## InstrumentContext.move_to

官方来源


```python
move_to(
    location: Location | TrashBin | WasteChute,
    force_direct: bool = False,
    minimum_z_height: float | None = None,
    speed: float | None = None,
    publish: bool = True,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 location Location | TrashBin | WasteChute 必填 位置或关键字 force_direct bool False 位置或关键字 minimum_z_height float | None None 位置或关键字 speed float | None None 位置或关键字 publish bool True 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Move the instrument. See Move To for examples. Parameters: location ( Location | TrashBin | WasteChute )
          – Where to move to. Changed in version 2.16 : Accepts TrashBin and WasteChute values. force_direct ( bool , default: False )
          – If True , move directly to the destination without arc
motion. Warning Forcing direct motion can cause the pipette to crash into labware,
modules, or other objects on the deck. minimum_z_height ( float , default: None )
          – An amount, measured in mm, to raise the
mid-arc height. The mid-arc height can't be lowered. speed ( float , default: None )
          – The speed at which to move. By default, InstrumentContext.default_speed .
This controls the straight linear speed of the motion. To limit
individual axis speeds, use ProtocolContext.max_speeds . publish ( bool , default: True )
          – Whether to list this function call in the run
preview. Default is True .
