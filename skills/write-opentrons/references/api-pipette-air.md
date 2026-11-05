# 移液器API · 吹空与空气间隙

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.blow_out](#instrumentcontextblow_out)
- [InstrumentContext.air_gap](#instrumentcontextair_gap)

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
