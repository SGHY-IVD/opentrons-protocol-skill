# Flex Stacker API · 容量与可存储列表

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

[Stacker成员索引](api-module-flex-stacker.md)；模块硬件/机制与必要条件见[Flex Stacker](module-conditions-flex-stacker.md#flex-stacker)，经验与组合示例见[对应经验](module-practices-flex-stacker.md#flex-stacker)，共享加载签名见[共享模块API](api-module-common.md)。

- [FlexStackerContext.get_current_storable_labware](#flexstackercontextget_current_storable_labware)
- [FlexStackerContext.get_current_storable_labware_from_list](#flexstackercontextget_current_storable_labware_from_list)
- [FlexStackerContext.get_max_storable_labware](#flexstackercontextget_max_storable_labware)
- [FlexStackerContext.get_max_storable_labware_from_list](#flexstackercontextget_max_storable_labware_from_list)

## FlexStackerContext.get_current_storable_labware

类型：方法；最低版本：requires_version(2, 25)。

```python
get_current_storable_labware() -> int
```

Get the number of labware that the Flex Stacker currently has space for.

Use this function to return the total number of labware that the Flex Stacker
can store. A Stacker has a limited amount of internal space and calculates the
number of labware that can be stored based on the `z` height of the labware
and the amount they overlap when stacked.

The number is calculated based on the labware definition for the type of
labware the Stacker is currently configured to store using
[`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware].
This function returns a number based on the current storage conditions of the
Stacker, and will change as labware is added or removed. To get the overall
maximum number of labware the Flex Stacker can store, use
[`get_max_storable_labware()`][opentrons.protocol_api.FlexStackerContext.get_max_storable_labware].

源码：module_contexts.py L1544–L1560（固定提交）。

## FlexStackerContext.get_current_storable_labware_from_list

类型：方法；最低版本：requires_version(2, 25)。

```python
get_current_storable_labware_from_list(labware: list[Labware]) -> list[Labware]
```

Limit a list of labware instances to the number that the Flex Stacker currently has space for,
based on the labware that is already stored in the Flex Stacker. Items will be taken from the
head of the list.

A Flex Stacker has a limited amount of internal space and computes the number of labware that
it can store based on the `z` height of the labware and the amount they overlap when stacked.

!!! note
    The number of elements in the returned list will change as labware is added or removed from
    the Flex Stacker. To get a list limited to the overall maximum number of labware the Flex
    Stacker can store, use
    [`get_max_storable_labware_from_list()`][opentrons.protocol_api.FlexStackerContext.get_max_storable_labware_from_list].

Args:
    labware: A list of labware to limit. The returned list takes from the front of the provided
        list, and it is guaranteed to be suitable for passing to
        [`fill_items()`][opentrons.protocol_api.FlexStackerContext.fill_items].

源码：module_contexts.py L1499–L1525（固定提交）。

## FlexStackerContext.get_max_storable_labware

类型：方法；最低版本：requires_version(2, 25)。

```python
get_max_storable_labware() -> int
```

Get the maximum number of labware that the Flex Stacker can store.

Use this function to return the total number of labware that the Flex Stacker can store. A Stacker has a limited
amount of internal space and calculates the total number of labware that can be stored based on the `z` height
of the labware and the amount they overlap when stacked.

The total number is calculated based on the labware definition for the type of labware the Stacker is currently
configured to store using [`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware].
This number is the overall maximum and will not change as labware is added or removed. To get the number of
labware that can be stored in the Flex Stacker based on its current conditions, use
[`get_current_storable_labware()`][opentrons.protocol_api.FlexStackerContext.get_current_storable_labware].

源码：module_contexts.py L1528–L1541（固定提交）。

## FlexStackerContext.get_max_storable_labware_from_list

类型：方法；最低版本：requires_version(2, 25)。

```python
get_max_storable_labware_from_list(labware: list[Labware], stacking_offset_z: float | None=None) -> list[Labware]
```

Limit a list of labware instances to the number that can be stored in a Flex Stacker.
Items will be taken from the head of the list.

A Flex Stacker has a limited amount of internal space and computes the number of labware
(or labware with lids or adapters) that it can store based on the `z` heights of the labware
and the amount they overlap when stacked. To calculate how many of a given
labware the Stacker can store, the labware type must be specified.

Provide a list of labware to this function to return the maximum number of labware of the given type that the
Stacker can store. The returned list is guaranteed to be suitable
for passing to [`set_stored_labware_items()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware_items].

This function limits the list of labware based on the overall maximum number the Stacker
can hold and will not change as labware is added or removed. To limit a list of labware to
the amount that will currently fit in the Flex Stacker, use
[`get_current_storable_labware_from_list()`][opentrons.protocol_api.FlexStackerContext.get_current_storable_labware_from_list].

!!! note
    If a `z` stacking offset is provided, be sure to specify the same value when
    configuring the Flex Stacker with
    [`set_stored_labware_items()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware_items].

    See [`set_stored_labware_items()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware_items]
    for more details on stacking offset.

源码：module_contexts.py L1461–L1496（固定提交）。
