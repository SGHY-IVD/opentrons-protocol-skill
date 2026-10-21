# 模块共享API

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

用于各模块继承成员；具体模块是否公开此成员以对应模块文件索引为准。

## ModuleContext.labware

类型：只读属性；最低版本：requires_version(2, 0)。

```python
labware: Optional[Labware]
```

The labware (if any) present on this module.

源码：module_contexts.py L401–L404（固定提交）。

## ModuleContext.load_adapter

类型：方法；最低版本：requires_version(2, 15)。

```python
load_adapter(name: str, namespace: Optional[str]=None, version: Optional[int]=None) -> Labware
```

Load an adapter onto the module using its load parameters.

The parameters of this function behave like those of
[`load_adapter()`][opentrons.protocol_api.ProtocolContext.load_adapter]
(which loads adapters directly onto the deck). Note that the parameter
`name` here corresponds to `load_name` on the `ProtocolContext`
function.

Returns:
    The initialized and loaded adapter object.

源码：module_contexts.py L340–L378（固定提交）。

## ModuleContext.load_adapter_from_definition

类型：方法；最低版本：requires_version(2, 15)。

```python
load_adapter_from_definition(definition: LabwareDefinition) -> Labware
```

Load an adapter onto the module using an inline definition.

Args:
    definition: The labware definition.

Returns:
    The initialized and loaded labware object.

源码：module_contexts.py L381–L397（固定提交）。

## ModuleContext.load_labware

类型：方法；最低版本：见成员说明/类版本。

```python
load_labware(name: str, label: Optional[str]=None, namespace: Optional[str]=None, version: Optional[int]=None, adapter: Optional[str]=None, lid: Optional[str]=None, *, adapter_namespace: Optional[str]=None, adapter_version: Optional[int]=None, lid_namespace: Optional[str]=None, lid_version: Optional[int]=None) -> Labware
```

Load a labware onto the module using its load parameters.

The parameters of this function behave like those of
[`load_labware()`][opentrons.protocol_api.ProtocolContext.load_labware]
(which loads labware directly onto the deck). Note that the parameter
`name` here corresponds to `load_name` on the `ProtocolContext`
function.

Returns:
    The initialized and loaded labware object.

*New in version 2.1:* The `label`, `namespace`, and `version` parameters.

*New in version 2.26:* The `adapter_namespace`, `adapter_version`,
`lid_namespace`, and `lid_version` parameters.

源码：module_contexts.py L135–L293（固定提交）。

## ModuleContext.load_labware_by_name

类型：方法；最低版本：requires_version(2, 1)。

```python
load_labware_by_name(name: str, label: Optional[str]=None, namespace: Optional[str]=None, version: Optional[int]=None) -> Labware
```

*Deprecated in version 2.0:*
    Use `load_labware` instead.

源码：module_contexts.py L320–L337（固定提交）。

## ModuleContext.load_labware_from_definition

类型：方法；最低版本：requires_version(2, 0)。

```python
load_labware_from_definition(definition: LabwareDefinition, label: Optional[str]=None) -> Labware
```

Load a labware onto the module using an inline definition.

Args:
    definition: The labware definition.
    label (str): An optional special name to give the labware. If
        specified, this is the name the labware will appear as in the
        run log and the calibration view in the Opentrons App.

Returns:
    The initialized and loaded labware object.

源码：module_contexts.py L296–L317（固定提交）。

## ModuleContext.model

类型：只读属性；最低版本：requires_version(2, 14)。

```python
model: ModuleModel
```

Get the module's model identifier.

源码：module_contexts.py L89–L91（固定提交）。

## ModuleContext.parent

类型：只读属性；最低版本：requires_version(2, 14)。

```python
parent: str
```

The name of the slot the module is on.

On a Flex, this will be like `"D1"`. On an OT-2, this will be like `"1"`.
See [Deck Slots](https://docs.opentrons.com/v2/deck_slots.html).

源码：module_contexts.py L408–L414（固定提交）。

## ModuleContext.type

类型：只读属性；最低版本：requires_version(2, 14)。

```python
type: ModuleType
```

Get the module's general type identifier.

源码：module_contexts.py L95–L97（固定提交）。

