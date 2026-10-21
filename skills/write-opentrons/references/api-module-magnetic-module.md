# MagneticModuleContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/magnetic-module/

本类成员：disengage, engage, serial_number, status。

共享成员（签名及参数见api-module-common.md）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

仅OT-2主动磁力模块；Flex使用MagneticBlockContext，不得套engage/disengage。旧height参数已移除，见engage说明。

## MagneticModuleContext.disengage

类型：方法；最低版本：requires_version(2, 0)。

```python
disengage() -> None
```

Lower the magnets back into the Magnetic Module.

源码：module_contexts.py L644–L646（固定提交）。

## MagneticModuleContext.engage

类型：方法；最低版本：requires_version(2, 0)。

```python
engage(height: Optional[float]=None, offset: Optional[float]=None, height_from_base: Optional[float]=None) -> None
```

Raise the Magnetic Module's magnets. You can specify how high the magnets
should move:

- No parameter: Move to the default height for the loaded labware. If
  the loaded labware has no default, or if no labware is loaded, this will
  raise an error.

- `height_from_base`: Move this many millimeters above the bottom
  of the labware. Acceptable values are between `0` and `25`.

    This is the recommended way to adjust the magnets' height.

    *New in version 2.2*

- `offset`: Move this many millimeters above (positive value) or below
  (negative value) the default height for the loaded labware. The sum of
  the default height and `offset` must be between 0 and 25.

- `height`: Intended to move this many millimeters above the magnets'
  home position. However, depending on the generation of module and the loaded
  labware, this may produce unpredictable results. You should normally use
  `height_from_base` instead.

    *Removed in version 2.14*

You shouldn't specify more than one of these parameters. However, if you do,
their order of precedence is `height`, then `height_from_base`, then `offset`.

源码：module_contexts.py L583–L640（固定提交）。

## MagneticModuleContext.serial_number

类型：只读属性；最低版本：requires_version(2, 14)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L558–L560（固定提交）。

## MagneticModuleContext.status

类型：只读属性；最低版本：requires_version(2, 0)。

```python
status: str
```

The status of the module, either `engaged` or `disengaged`.

源码：module_contexts.py L650–L652（固定提交）。


## 源码补充成员

以下在固定源码存在，但当前公开参考页未列出；不会因此成为默认调用。calibrate在2.14+不可用，其余仅排查/有明确用途时查。

## MagneticModuleContext.calibrate

类型：方法；最低版本：requires_version(2, 0)。

```python
calibrate() -> None
```

Calibrate the Magnetic Module.

*Deprecated in version 2.14:* This method is unnecessary; remove any usage.

源码：module_contexts.py L564–L579（固定提交）。

