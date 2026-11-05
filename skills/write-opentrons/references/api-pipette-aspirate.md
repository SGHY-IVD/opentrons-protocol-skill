# 移液器API · 吸液与活塞准备

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.prepare_to_aspirate](#instrumentcontextprepare_to_aspirate)
- [InstrumentContext.aspirate](#instrumentcontextaspirate)

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
          – Tells the Flex to move the pipette from the specified location to the specified end_location while aspirating liquid. When this argument is used, the location and end_location must both be a Location . movement_delay ( float , default: None )
          – Time in seconds to delay after the pipette starts aspirating and before it begins moving
from the location to the end_location . This option is only valid when using end_location . When this
argument is used, the pipette will wait the specified time
after the pipette starts to aspirate before moving. This may help when
aspirating very viscous liquids that need to build up some pressure
before liquid starts to flow. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note If aspirate() is called with a single, unnamed argument, it will treat
that argument as volume . If you want to call aspirate() with only location , specify it as a keyword argument: pipette.aspirate(location=plate['A1']) . Changed in version 2.24 : Added the flow_rate parameter. Changed in version 2.27 : Added the end_location and movement_delay parameters.
