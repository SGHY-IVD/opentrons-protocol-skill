# Flex Stacker API · 供料、回收与库存读取

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

[Stacker成员索引](api-module-flex-stacker.md)；模块硬件/机制与必要条件见[Flex Stacker](module-conditions-flex-stacker.md#flex-stacker)，经验与组合示例见[对应经验](module-practices-flex-stacker.md#flex-stacker)，共享加载签名见[共享模块API](api-module-common.md)。

- [FlexStackerContext.get_stored_labware](#flexstackercontextget_stored_labware)
- [FlexStackerContext.retrieve](#flexstackercontextretrieve)
- [FlexStackerContext.store](#flexstackercontextstore)
- [FlexStackerContext.serial_number](#flexstackercontextserial_number)

## FlexStackerContext.get_stored_labware

类型：方法；最低版本：requires_version(2, 25)。

```python
get_stored_labware() -> list[Labware]
```

Get the list of labware currently stored inside the Stacker.

This function returns a list of all labware stored in the Stacker based on
the labware initially stored using
[`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware]
and any labware added or removed during the protocol.

The first element of the list occupies the bottom-most position in the
labware stack and would be the labware retrieved by a call to
[`retrieve()`][opentrons.protocol_api.FlexStackerContext.retrieve].

源码：module_contexts.py L1842–L1854（固定提交）。

## FlexStackerContext.retrieve

类型：方法；最低版本：requires_version(2, 25)。

```python
retrieve() -> Labware
```

Retrieve a labware from the Flex Stacker and move it onto the shuttle.

The Stacker will retrieve the bottom-most labware in the stack.

Returns:
    The retrieved [`Labware`][opentrons.protocol_api.labware.Labware] object. This will always
        be the main labware, even if the Flex Stacker contains labware on an adapter. To get the
        adapter object, call [`Labware.parent`][opentrons.protocol_api.labware.Labware.parent] on
        the returned labware.

源码：module_contexts.py L1412–L1431（固定提交）。

## FlexStackerContext.store

类型：方法；最低版本：requires_version(2, 25)。

```python
store() -> None
```

Move a labware currently on the Flex Stacker shuttle into the Flex Stacker.

The labware must be the same type the Stacker is configured to store using
[`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware].
If labware is currently stacked inside the module, this method moves the new
labware to the bottom-most position of the stack.

源码：module_contexts.py L1435–L1443（固定提交）。

## FlexStackerContext.serial_number

类型：只读属性；最低版本：requires_version(2, 25)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L1406–L1408（固定提交）。
