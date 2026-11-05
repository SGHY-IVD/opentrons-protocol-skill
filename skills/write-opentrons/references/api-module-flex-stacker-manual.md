# Flex Stacker API · 人工补给与清空

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

[Stacker成员索引](api-module-flex-stacker.md)；模块硬件/机制与必要条件见[Flex Stacker](module-conditions-flex-stacker.md#flex-stacker)，经验与组合示例见[对应经验](module-practices-flex-stacker.md#flex-stacker)，共享加载签名见[共享模块API](api-module-common.md)。

- [FlexStackerContext.fill](#flexstackercontextfill)
- [FlexStackerContext.fill_items](#flexstackercontextfill_items)
- [FlexStackerContext.empty](#flexstackercontextempty)

## FlexStackerContext.fill

类型：方法；最低版本：requires_version(2, 25)。

```python
fill(count: int | None=None, message: str | None=None) -> None
```

版本核对提示（2026-11-04）：以下上游参数文案把count解释为补给后的总量，但官方v10.0.0（commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af）实现将显式count作为本次新增件数；例如已有1件、容量3件时，count=3会触发超容校验。此差异由api/src/opentrons/protocol_api/core/engine/module_core.py的fill、protocol_engine/commands/flex_stacker/fill.py和common.py的_count_from_lw_list_or_initial_count，以及api/tests/opentrons/protocol_engine/commands/flex_stacker/test_fill.py共同核对，不以原文定义替代目标软件实际行为，也不改写下述上游文案。
需要非空仓补指定数量时先核对目标机器人软件；仓内耗尽后fill(count=n)在上述两种解释下结果一致。非空仓确有余量且需补满时，可省略count，按API补到该配置容量。耗尽不会清除原有类型配置，不需为普通补给重新set_stored_labware；本次仅静态源码核查，未作实机验证。

Pause the protocol to add labware to the Flex Stacker.

The labware must be the same type the Stacker is configured to store using
[`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware].
If no labware type has been set, the API will raise an error.

Args:
    count: The amount of labware the Flex Stacker should hold after this command
        is executed. If not specified, the Flex Stacker should be full after this
        command is executed.
    message: A message to display noting what kind of labware to fill the Stacker with.

源码：module_contexts.py L1793–L1806（固定提交）。

## FlexStackerContext.fill_items

类型：方法；最低版本：requires_version(2, 25)。

```python
fill_items(labware: list[Labware], message: str | None=None) -> None
```

Pause the protocol to add a specific list of labware to the Flex Stacker.

Args:
    labware: The list of labware to add. The list must:

        - Contain at least one labware.
        - Have labware of the same kind previously passed to
        [`set_stored_labware_items()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware_items]
        or loaded by [`set_stored_labware()`][opentrons.protocol_api.FlexStackerContext.set_stored_labware].
        - All labware should be loaded [`OFF_DECK`][opentrons.protocol_api.OFF_DECK].
    message: A message to display noting the labware to fill the Stacker with.

源码：module_contexts.py L1809–L1822（固定提交）。

## FlexStackerContext.empty

类型：方法；最低版本：requires_version(2, 25)。

```python
empty(message: str | None=None) -> None
```

Pause the protocol to remove all labware stored in the Flex Stacker.

This method sets the location of all labware currently in the stacker to
[`OFF_DECK`][opentrons.protocol_api.OFF_DECK].

Args:
    message: A message to display to note what should be removed from
        the Flex Stacker.

源码：module_contexts.py L1826–L1839（固定提交）。
