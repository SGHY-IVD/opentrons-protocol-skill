# 孔位、位置与液体API · 位置、液面与体积高度

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[孔位、位置与液体成员索引](api-wells-liquids.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [Well.top](#welltop)
- [Well.bottom](#wellbottom)
- [Well.meniscus](#wellmeniscus)
- [Well.height_from_volume](#wellheight_from_volume)
- [Location.move](#locationmove)

## Well.top

官方来源


```python
top(z: float = 0.0) -> Location
```

参数名 类型 默认值 / 必填 传参方式 z float 0.0 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Parameters: z ( float , default: 0.0 )
          – An offset on the z-axis, in mm. Positive offsets are higher and
negative offsets are lower. Returns: Location – A Location corresponding to the
absolute position of the top-center of the well, plus the z offset
(if specified).


## Well.bottom

官方来源


```python
bottom(z: float = 0.0) -> Location
```

参数名 类型 默认值 / 必填 传参方式 z float 0.0 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Parameters: z ( float , default: 0.0 )
          – An offset on the z-axis, in mm. Positive offsets are higher and
negative offsets are lower. Returns: Location – A Location corresponding to the
absolute position of the bottom-center of the well, plus the z offset (if specified).


## Well.meniscus

官方来源：https://docs.opentrons.com/python-api/robot-position/#meniscus
固定源码核对：v10.0.0，api/src/opentrons/protocol_api/labware.py（返回Location）及instrument_context.py（解析起终点标记）。


```python
meniscus(
    z: float = 0.0, target: Literal["start", "end", "dynamic"] = "end"
) -> Location
```

参数名 类型 默认值 / 必填 传参方式 z float 0.0 位置或关键字 target Literal['start', 'end', 'dynamic'] 'end' 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Parameters: z ( float , default: 0.0 )
          – An offset on the z-axis, in mm. Positive offsets are higher and
negative offsets are lower. target ( str , default: 'end' )
          – The relative position of the liquid meniscus inside the well
to target when performing a liquid handling operation. Returns: Location ( Location )          – A Location corresponding to the
liquid meniscus, plus a target position and z offset as specified.

返回值为带液面标记的Location，可用于已维护aspirate/dispense的location或end_location；显式终点使用target="end"，衔接当前液面使用"start"。location使用target="dynamic"时由API展开为两端，不可同时另传end_location；显式起终点运动按对应接口核对API版本。标记随每次命令的实际液量解析；不是持续实测，也不表示曲底非线性区间全过程精确恒浸深。官方 Flex 软件 v10.0.0（API 2.30）对纯液体移动吸排，按单喷嘴命令量 × 实际作用于该孔的喷嘴数求终点，对应引擎安排见[geometry.py](https://github.com/Opentrons/opentrons/blob/e8c6d0a424c25fff1604e2a02e4ccaedac95b9af/api/src/opentrons/protocol_engine/state/geometry.py#L2174-L2205)及[喷嘴映射](https://github.com/Opentrons/opentrons/blob/e8c6d0a424c25fff1604e2a02e4ccaedac95b9af/api/src/opentrons/protocol_engine/state/_well_math.py#L214-L235)。不要再次把命令量乘通道数。映射使用喷嘴布局与定义 ordering；特殊耗材/偏移须核对映射与实际覆盖一致，未核对版本或配置不据此保证动态路径可用。排出含空气时，普通 END 定位与移动排液的记录边界另见[pipette-mechanics](pipette-mechanics.md#分开记账)。用户默认路径与偏移只见operations。



## Well.height_from_volume

官方来源：https://docs.opentrons.com/python-api/reference/wells-liquids/#opentrons.protocol_api.Well.height_from_volume
已保存官方接口文档核对；API 2.24新增，当前技能基线2.30包含此方法。

```python
height_from_volume(volume: LiquidTrackingType) -> LiquidTrackingType
```

volume：必填，可位置或关键字传入；输入该孔液体体积，单位µL，普通已知体积使用数值。返回该体积对应的孔内高度，单位mm；签名保留官方LiquidTrackingType，不把未知跟踪值强制转换为有效数值。本接口不需先把所传体积写入load_liquid，不改变真实液量，也不是液面实测。
用户已允许在最终脚本直接写well.bottom(z=well.height_from_volume(vol))，用作location或end_location。该值为相对孔底高度，不手工再加甲板或耗材绝对Z。仍须遵守本技能所有脚本进行液体可视化初始化的要求。具体耗材定义需支持体积—高度换算；不能用猜测公式替代缺失模型。
## Location.move

官方来源


```python
move(point: Point) -> 'Location'
```

参数名 类型 默认值 / 必填 传参方式 point Point 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Alter the point stored in the location while preserving the labware. This returns a new Location and does not alter the current one. It
should be used like loc = Location ( Point ( 1 , 1 , 1 ), None ) new_loc = loc . move ( Point ( 1 , 1 , 1 )) # The new point is the old one plus the given offset. assert new_loc . point == Point ( 2 , 2 , 2 ) # True # The old point hasn't changed. assert loc . point == Point ( 1 , 1 , 1 ) # True
