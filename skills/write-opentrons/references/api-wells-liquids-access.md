# 孔位、位置与液体API · 孔位访问与对象关系

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[孔位、位置与液体成员索引](api-wells-liquids.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [Labware.wells](#labwarewells)
- [Labware.wells_by_name](#labwarewells_by_name)
- [Labware.rows](#labwarerows)
- [Labware.columns](#labwarecolumns)
- [Labware.parent](#labwareparent)
- [Labware.child](#labwarechild)
- [Well.parent](#wellparent)

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


## Well.parent

官方来源


```python
parent: Labware
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） The Labware object that the well is a part of.
