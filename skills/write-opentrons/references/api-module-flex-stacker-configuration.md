# Flex Stacker API · 库存类型与初始配置

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

[Stacker成员索引](api-module-flex-stacker.md)；模块硬件/机制与必要条件见[Flex Stacker](module-conditions-flex-stacker.md#flex-stacker)，经验与组合示例见[对应经验](module-practices-flex-stacker.md#flex-stacker)，共享加载签名见[共享模块API](api-module-common.md)。

- [FlexStackerContext.set_stored_labware](#flexstackercontextset_stored_labware)
- [FlexStackerContext.set_stored_labware_items](#flexstackercontextset_stored_labware_items)

## FlexStackerContext.set_stored_labware

类型：方法；最低版本：requires_version(2, 25)。

```python
set_stored_labware(load_name: str, namespace: str | None=None, version: int | None=None, adapter: str | None=None, lid: str | None=None, count: int | None=None, stacking_offset_z: float | None=None, *, adapter_namespace: str | None=None, adapter_version: int | None=None, lid_namespace: str | None=None, lid_version: int | None=None) -> None
```

Configure the type and starting quantity of labware the Flex Stacker will store during a protocol. This is the
only type of labware you'll be able to store in the Stacker until it's reconfigured.

You must use this method to load a labware stack stored inside the Stacker before you're able to
[`retrieve()`][opentrons.protocol_api.FlexStackerContext.retrieve] or
[`store()`][opentrons.protocol_api.FlexStackerContext.store] additional labware.

Args:
    load_name (str): A string to use for looking up a labware definition.
        You can find the `load_name` for any Opentrons-verified labware on the
        [Labware Library](https://labware.opentrons.com).

    namespace (str): The namespace that the labware definition belongs to.
        If unspecified, the API will automatically search two namespaces:

        - `"opentrons"`, to load standard Opentrons labware definitions.
        - `"custom_beta"`, to load custom labware definitions created with the
        [Custom Labware Creator](https://labware.opentrons.com/create).

        You might need to specify an explicit `namespace` if you have a custom
        definition whose `load_name` is the same as an Opentrons-verified
        definition, and you want to explicitly choose one or the other.

    version (int): The version of the labware definition. You should normally
        leave this unspecified to let the method choose a version
        automatically.

    adapter (str): An adapter to load the labware on top of. Accepts the same
        values as the `load_name` parameter of
        [`load_adapter()`][opentrons.protocol_api.ProtocolContext.load_adapter].

    adapter_namespace (str): Applies to `adapter` the same way that `namespace`
        applies to `load_name`.

        *Changed in version 2.26:* `adapter_namespace` may now be specified explicitly.
        When you've specified `namespace` for `load_name` but not `adapter_namespace`,
        `adapter_namespace` now independently follows the same search rules described
        in `namespace`. Formerly, it took the exact `namespace` value.

    adapter_version (int): Applies to `adapter` the same way that `version`
        applies to `load_name`.

        *Changed in version 2.26:* `adapter_version` may now be specified explicitly.
        When unspecified, improved search rules prevent selecting a version that does
        not exist.

    lid (str): A lid to load on top of the main labware. Accepts the same
        values as the `load_name` parameter of
        [`load_lid_stack()`][opentrons.protocol_api.ProtocolContext.load_lid_stack].
        The lid will use the same namespace as the labware, and the API will
        choose the lid's version automatically.

        *New in version 2.23*

    lid_namespace (str): The namespace of the lid being loaded.
        Applies to lid the same way that namespace applies to load_name.

        *Changed in version 2.26:* `lid_namespace` may now be specified explicitly.
        When you've specified `namespace` for `load_name` but not `lid_namespace`,
        `lid_namespace` now independently follows the same search rules
        described in `namespace`. Formerly, it took the exact `namespace` value.

    lid_version (int): Applies to `lid` the same way that `version`
        applies to `load_name`.

        *Changed in version 2.26:* `lid_version` may now be specified explicitly.
        When unspecified, improved search rules prevent selecting a version that does
        not exist.

    count (int): The number of labware that the Flex Stacker should store. If not specified,
        this will be the maximum amount of this kind of labware that the Flex Stacker is
        capable of storing.

    stacking_offset_z (float): Stacking `z` offset in mm of stored labware. If specified, this
        overrides the calculated value in the labware definition.

        !!! note
            The stacking offset is the amount of vertical overlap (in mm) between the bottom side of a
            labware unit and the top side of the unit below. This offset is used to determine how many
            units can fit in the Stacker and calculates the `z` position of the shuttle when retrieving
            or storing labware.

            There are four possible stacking configurations, each with a different method of calculating
            the stacking offset:

            - Bare labware: labware (bottom side) overlaps with the top side of the labware below.
            - Labware on adapter: the adapter (bottom side) of the upper labware unit overlaps with the
            top side of the labware below.
            - Labware with lid: the labware (bottom side) of the upper unit overlaps with the lid (top
            side) of the unit below.
            - Labware with lid and adapter: the adapter (bottom side) of the upper unit overlaps with
            the lid (top side) of the unit below.

源码：module_contexts.py L1622–L1789（固定提交）。

## FlexStackerContext.set_stored_labware_items

类型：方法；最低版本：requires_version(2, 25)。

```python
set_stored_labware_items(labware: list[Labware], stacking_offset_z: float | None=None) -> None
```

Configure the labware the Flex Stacker will store during a protocol by
providing an initial list of stored labware objects. The start of the list
represents the bottom of the Stacker, and the end of the list represents the
top of the Stacker.

The kind of labware stored by the Flex Stacker will be calculated from the
list of labware specified here. You can use this to store labware objects
that you have already created so that, for instance, you can set their
liquid state or nicknames.

Args:
    labware: A list of labware to load into the Stacker.

        - The list must have at least one element.
        - All labware must be loaded [`OFF_DECK`][opentrons.protocol_api.OFF_DECK].
        - All labware must be of the same kind. If any of them have lids, they
        must all have lids, and the lids must be the same. If any of them are
        on adapters, they all must be on adapters, and the adapters must be
        the same. All lids and adapters must be compatible with the Stacker.
        - The number of labware objects must fit in the Stacker physically. To
        make sure the labware will fit, use the return value of
        [`get_max_storable_labware_from_list()`][opentrons.protocol_api.FlexStackerContext.get_max_storable_labware_from_list].

    stacking_offset_z: Stacking `z` offset in mm of stored labware. If
        specified, this overrides the calculated value from labware
        definitions.

!!! note
    The stacking offset is the amount of vertical overlap (in mm) between
    the bottom side of a labware unit and the top side of the unit below.
    This offset is used to determine how many units can fit in the stacker
    and calculates the `z` position of the shuttle when retrieving or
    storing labware.

    There are four possible stacking configurations, each with a different
    method of calculating the stacking offset:

    - Bare labware: labware (bottom side) overlaps with the top side of
      the labware below.
    - Labware on adapter: the adapter (bottom side) of the upper labware
      unit overlaps with the top side of the labware below.
    - Labware with lid: the labware (bottom side) of the upper unit
      overlaps with the lid (top side) of the unit below.
    - Labware with lid and adapter: the adapter (bottom side) of the
      upper unit overlaps with the lid (top side) of the unit below.

源码：module_contexts.py L1563–L1618（固定提交）。
