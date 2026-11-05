# 移液器API · 移动与触壁

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.move_to](#instrumentcontextmove_to)
- [InstrumentContext.touch_tip](#instrumentcontexttouch_tip)

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
## InstrumentContext.touch_tip

生成脚本时的按需启用及用户经验默认见[操作经验](operation-motion-special.md#按需touch_tip)；以下签名保留官方默认值。

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
