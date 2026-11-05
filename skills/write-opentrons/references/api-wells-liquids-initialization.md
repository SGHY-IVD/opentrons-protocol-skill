# 孔位、位置与液体API · 液体定义与初始化

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[孔位、位置与液体成员索引](api-wells-liquids.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [ProtocolContext.define_liquid](#protocolcontextdefine_liquid)
- [Labware.load_liquid](#labwareload_liquid)
- [Labware.load_liquid_by_well](#labwareload_liquid_by_well)
- [Labware.load_empty](#labwareload_empty)
- [Well.load_liquid](#wellload_liquid)

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
