# FlexStackerContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/flex-stacker/

本类成员：empty, fill, fill_items, get_current_storable_labware, get_current_storable_labware_from_list, get_max_storable_labware, get_max_storable_labware_from_list, get_stored_labware, retrieve, serial_number, set_stored_labware, set_stored_labware_items, store。

共享成员（签名及参数见api-module-common.md）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

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

## FlexStackerContext.fill

类型：方法；最低版本：requires_version(2, 25)。

```python
fill(count: int | None=None, message: str | None=None) -> None
```

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

## FlexStackerContext.serial_number

类型：只读属性；最低版本：requires_version(2, 25)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L1406–L1408（固定提交）。

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

