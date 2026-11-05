# 移液器API · 排液

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.dispense](#instrumentcontextdispense)

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
argument is used, the location and end_location must both be a Location . movement_delay ( float , default: None )
          – Time in seconds to delay after the pipette starts dispensing and before it begins moving from the location to the end_location .
This option is only valid when using end_location . When this argument
is used, the pipette will wait the specified time after the
pipette starts to dispense before moving. This may help when dispensing
very viscous liquids that need to build up some pressure before liquid
starts to flow. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note If dispense() is called with a single, unnamed argument, it will treat
that argument as volume . If you want to call dispense() with only location , specify it as a keyword argument: pipette.dispense(location=plate['A1']) . Changed in version 2.15 : Added the push_out parameter. Changed in version 2.17 : Behavior of the volume parameter. Changed in version 2.24 : Added the flow_rate parameter. Changed in version 2.24 : location is no longer required if the pipette just
moved to, dispensed, or blew out into a trash bin or waste chute. Changed in version 2.27 : Added the end_location and movement_delay parameters.
