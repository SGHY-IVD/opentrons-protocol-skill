# 公共查询 · 孔位、位置与液体

条目目录（可用rg按名称定位）：
- Well.height_from_volume
- ProtocolContext.define_liquid
- Labware.wells
- Labware.wells_by_name
- Labware.rows
- Labware.columns
- Labware.load_liquid
- Labware.load_liquid_by_well
- Labware.load_empty
- Labware.parent
- Labware.child
- Well.top
- Well.bottom
- Well.meniscus
- Well.load_liquid
- Well.parent
- Location.move

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

访问孔位、位置偏移、液体标记及对象关系。
ProtocolContext.define_liquid Labware.wells Labware.wells_by_name Labware.rows Labware.columns Labware.load_liquid Labware.load_liquid_by_well Labware.load_empty Labware.parent Labware.child Well.top Well.bottom Well.meniscus Well.load_liquid Well.parent Location.move

## ProtocolContext.define_liquid

官方来源


```python
define_liquid(
    name: str,
    description: str | None | _Unset = _Unset(),
    display_color: str | None | _Unset = _Unset(),
) -> Liquid
```

参数名 类型 默认值 / 必填 传参方式 name str 必填 位置或关键字 description str | None | _Unset _Unset() 位置或关键字 display_color str | None | _Unset _Unset() 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Define a liquid within a protocol. Parameters: name ( str )
          – A human-readable name for the liquid. description ( str | None , default: _Unset () )
          – An optional description of the liquid. display_color ( str | None , default: _Unset () )
          – An optional hex color code, with hash included,
to represent the specified liquid. For example, "#48B1FA" .
Standard three-value, four-value, six-value, and eight-value syntax are all
acceptable. Returns: Liquid – An object representing the specified liquid. Changed in version 2.20: You can now omit the description and display_color arguments.
    Formerly, when you didn't want to provide values, you had to supply description=None and display_color=None explicitly.


## Labware.wells

官方来源


```python
wells(*args: str | int) -> List[Well]
```

参数名 类型 默认值 / 必填 传参方式 *args str | int 可省略 可变位置

官方参数含义、返回值与使用约束（已保存在本文件） Accessor function to navigate a labware top to bottom, left to right. i.e., this method returns a list ordered A1, B1, C1…A2, B2, C2…. Use indexing to access individual wells contained in the list.
For example, access well A1 with labware.wells()[0] . Note Using args with this method is deprecated. Use indexing instead. If your code uses args, they can be either strings or integers, but not a
mix of the two. For example, .wells(1, 4) or .wells("1", "4") is
valid, but .wells("1", 4) is not. Returns: list [ Well ] – Ordered list of all wells in a labware.


## Labware.wells_by_name

官方来源


```python
wells_by_name() -> Dict[str, Well]
```

无调用参数。

官方参数含义、返回值与使用约束（已保存在本文件） Accessor function used to navigate through a labware by well name. Use indexing to access individual wells contained in the dictionary.
For example, access well A1 with labware.wells_by_name()["A1"] . Returns: dict [ str , Well ] – Dictionary of Well objects
keyed by well name.


## Labware.rows

官方来源


```python
rows(*args: int | str) -> List[List[Well]]
```

参数名 类型 默认值 / 必填 传参方式 *args int | str 可省略 可变位置

官方参数含义、返回值与使用约束（已保存在本文件） Accessor function to navigate through a labware by row. Use indexing to access individual rows or wells contained in the nested list.
On a standard 96-well plate, this will output a list of Well objects containing A1 through A12. Note Using args with this method is deprecated. Use indexing instead. If your code uses args, they can be either strings or integers, but not a
mix of the two. For example, .rows(1, 4) or .rows("1", "4") is
valid, but .rows("1", 4) is not. Returns: list [ list [ Well ]] – A list of row lists.


## Labware.columns

官方来源


```python
columns(*args: int | str) -> List[List[Well]]
```

参数名 类型 默认值 / 必填 传参方式 *args int | str 可省略 可变位置

官方参数含义、返回值与使用约束（已保存在本文件） Accessor function to navigate through a labware by column. Use indexing to access individual columns or wells contained in the nested list.
For example, access column 1 with labware.columns()[0] .
On a standard 96-well plate, this will output a list of Well objects containing A1 through H1. Note Using args with this method is deprecated. Use indexing instead. If your code uses args, they can be either strings or integers, but not a
mix of the two. For example, .columns(1, 4) or .columns("1", "4") is
valid, but .columns("1", 4) is not. Returns: list [ list [ Well ]] – A list of column lists.


## Labware.load_liquid

官方来源


```python
load_liquid(wells: Sequence[str | Well], volume: float, liquid: Liquid) -> None
```

参数名 类型 默认值 / 必填 传参方式 wells Sequence[str | Well] 必填 位置或关键字 volume float 必填 位置或关键字 liquid Liquid 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Mark several wells as containing the same amount of liquid. This method should be called at the beginning of a protocol, soon after
loading labware and before liquid handling operations begin. Loading
liquids is required for liquid tracking functionality. If a well hasn't
been assigned a starting volume with load_empty() , load_liquid() , or load_liquid_by_well() ,
the volume it contains is unknown and the well's liquid will not be tracked
throughout the protocol. Parameters: wells ( list [ str | Well ] )
          – The wells to load the liquid into. This can
be a list of string well names or a list of Well objects (e.g., from wells() ). volume ( float )
          – The volume of liquid to load into each well. liquid ( Liquid )
          – The liquid to load into each well, previously defined by define_liquid() .


## Labware.load_liquid_by_well

官方来源


```python
load_liquid_by_well(
    volumes: Mapping[str | Well, float], liquid: Liquid
) -> None
```

参数名 类型 默认值 / 必填 传参方式 volumes Mapping[str | Well, float] 必填 位置或关键字 liquid Liquid 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Mark several wells as containing unique volumes of liquid. This method should be called at the beginning of a protocol, soon after
loading labware and before liquid handling begins. Loading liquids is
required for liquid tracking functionality. If a well hasn't been assigned
a starting volume with load_empty() , load_liquid() , or load_liquid_by_well() ,
the volume it contains is unknown and the well's liquid will not be tracked
throughout the protocol. Parameters: volumes ( dict [ str | Well , float ] )
          – A dictionary of well names (or Well objects, for instance
from labware['A1'] ) to their respective volumes. liquid ( Liquid )
          – The liquid to load into each well, previously defined by define_liquid() .


## Labware.load_empty

官方来源


```python
load_empty(wells: Sequence[Well | str]) -> None
```

参数名 类型 默认值 / 必填 传参方式 wells Sequence[Well | str] 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Mark several wells as empty. This method should be called at the beginning of a protocol, after loading
the labware and before liquid handling begins. Loading liquids is required
for liquid tracking functionality. If a well in a labware hasn't been
assigned a starting volume with load_empty() , load_liquid() , or load_liquid_by_well() ,
the volume it contains is unknown and the well's liquid will not be tracked
throughout the protocol. Parameters: wells ( list [ Well ] | list [ str ] )
          – The list of wells to mark empty. To
mark all wells as empty, pass labware.wells() . You can also specify
wells by their names (for instance, labware.load_empty(['A1', 'A2']) ).


## Labware.parent

官方来源


```python
parent: str | Labware | ModuleTypes | OffDeckType
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） Where the labware is loaded. This corresponds to the physical object that the labware directly rests upon. Returns: str | Labware | ModuleTypes | OffDeckType – If the labware is directly on the robot's deck, the str name of the deck slot,
like "D1" on Flex. See Deck Slots . If the labware is on a module, a module context. If the labware is on a labware or adapter, a Labware . If the labware is off-deck, OFF_DECK . Changed in version 2.14: Return type for module parent changed.
Formerly, the API returned an internal geometry interface. Changed in version 2.15: Returns a Labware if the labware is loaded
    onto a labware/adapter. Returns OFF_DECK if the labware is
    off-deck. Formerly, if the labware was removed by using del on deck , this would return where it was before its removal.


## Labware.child

官方来源


```python
child: Labware | None
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） The labware (if any) present on this labware.


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

官方来源


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


## Well.load_liquid

官方来源


```python
load_liquid(liquid: Liquid, volume: float) -> None
```

参数名 类型 默认值 / 必填 传参方式 liquid Liquid 必填 位置或关键字 volume float 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a liquid into a well. Parameters: liquid ( Liquid )
          – The liquid to load into the well. volume ( float )
          – The volume of liquid to load, in µL. Deprecated in version 2.22: Use Labware.load_liquid() , Labware.load_liquid_by_well() ,
or Labware.load_empty() instead.


## Well.parent

官方来源


```python
parent: Labware
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） The Labware object that the well is a part of.


## Location.move

官方来源


```python
move(point: Point) -> 'Location'
```

参数名 类型 默认值 / 必填 传参方式 point Point 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Alter the point stored in the location while preserving the labware. This returns a new Location and does not alter the current one. It
should be used like loc = Location ( Point ( 1 , 1 , 1 ), None ) new_loc = loc . move ( Point ( 1 , 1 , 1 )) # The new point is the old one plus the given offset. assert new_loc . point == Point ( 2 , 2 , 2 ) # True # The old point hasn't changed. assert loc . point == Point ( 1 , 1 , 1 ) # True

## Well.height_from_volume

官方来源：https://docs.opentrons.com/python-api/reference/wells-liquids/#opentrons.protocol_api.Well.height_from_volume
已保存官方接口文档核对；API 2.24新增，当前技能基线2.30包含此方法。

```python
height_from_volume(volume: LiquidTrackingType) -> LiquidTrackingType
```

volume：必填，可位置或关键字传入；输入该孔液体体积，单位µL，普通已知体积使用数值。返回该体积对应的孔内高度，单位mm；签名保留官方LiquidTrackingType，不把未知跟踪值强制转换为有效数值。本接口不需先把所传体积写入load_liquid，不改变真实液量，也不是液面实测。
用户已允许在最终脚本直接写well.bottom(z=well.height_from_volume(vol))，用作location或end_location。该值为相对孔底高度，不手工再加甲板或耗材绝对Z。仍须遵守本技能所有脚本进行液体可视化初始化的要求。具体耗材定义需支持体积—高度换算；不能用猜测公式替代缺失模型。
