# AbsorbanceReaderContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/absorbance-plate-reader/

本类成员：close_lid, initialize, is_lid_on, open_lid, read, serial_number。

共享成员（签名及参数见api-module-common.md）：labware, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

## AbsorbanceReaderContext.close_lid

类型：方法；最低版本：requires_version(2, 21)。

```python
close_lid() -> None
```

Use the Flex Gripper to close the lid of the Absorbance Plate Reader.

You must call this method before initializing the reader, even if the reader was
in the closed position at the start of the protocol.

源码：module_contexts.py L1301–L1307（固定提交）。

## AbsorbanceReaderContext.initialize

类型：方法；最低版本：requires_version(2, 21)。

```python
initialize(mode: ABSMeasureMode, wavelengths: List[int], reference_wavelength: Optional[int]=None) -> None
```

Prepare the Absorbance Plate Reader to read a plate.

See [Initialization](https://docs.opentrons.com/v2/modules/absorbance-plate-reader.html#initialization) for examples.

Args:
    mode: Either `"single"` or `"multi"`.

        - In single measurement mode, [`read()`][opentrons.protocol_api.AbsorbanceReaderContext.read]
        uses one sample wavelength and an optional reference wavelength.
        - In multiple measurement mode, [`read()`][opentrons.protocol_api.AbsorbanceReaderContext.read]
        uses a list of up to six sample wavelengths.
    wavelengths: A list of wavelengths, in nm, to measure.

        - In the default hardware configuration, each wavelength must be one of
        `450` (blue), `562` (green), `600` (orange), or `650` (red). In custom
        hardware configurations, the module may accept other integers between
        `350` and `1000`.
        - The list must contain only one item when initializing a single measurement.
        - The list can contain one to six items when initializing a multiple measurement.
    reference_wavelength: An optional reference wavelength, in nm. If provided,
        [`read()`][opentrons.protocol_api.AbsorbanceReaderContext.read] will read at the
        reference wavelength and then subtract the reference wavelength values from the
        measurement wavelength values. Can only be used with single measurements.

源码：module_contexts.py L1320–L1352（固定提交）。

## AbsorbanceReaderContext.is_lid_on

类型：方法；最低版本：requires_version(2, 21)。

```python
is_lid_on() -> bool
```

Return `True` if the Absorbance Plate Reader's lid is currently closed.

源码：module_contexts.py L1315–L1317（固定提交）。

## AbsorbanceReaderContext.open_lid

类型：方法；最低版本：requires_version(2, 21)。

```python
open_lid() -> None
```

Use the Flex Gripper to open the lid of the Absorbance Plate Reader.

源码：module_contexts.py L1310–L1312（固定提交）。

## AbsorbanceReaderContext.read

类型：方法；最低版本：requires_version(2, 21)。

```python
read(export_filename: Optional[str]=None) -> Dict[int, Dict[str, float]]
```

Read a plate on the Absorbance Plate Reader.

This method always returns a dictionary of measurement data. It optionally will
save a CSV file of the results to the Flex filesystem, which you can access from
the Recent Protocol Runs screen in the Opentrons App. These files are *only* saved
if you specify `export_filename`.

In simulation, the values for each well key in the dictionary are set to zero, and
no files are written.

!!! note
    Avoid divide-by-zero errors when simulating and using the results of this
    method later in the protocol. If you divide by any of the measurement
    values, use [`is_simulating()`][opentrons.protocol_api.ProtocolContext.is_simulating]
    to use alternate dummy data or skip the division step.

Args:
    export_filename: An optional file basename. If provided, this method
        will write a CSV file for each measurement in the read operation. File
        names will use the value of this parameter, the measurement wavelength
        supplied in [`initialize()`][opentrons.protocol_api.AbsorbanceReaderContext.initialize],
        and a `.csv` extension. For example, when reading at wavelengths 450 and 562
        with `export_filename="my_data"`, there will be two output files:
        `my_data_450.csv` and `my_data_562.csv`.

        See [CSV Data](https://docs.opentrons.com/v2/modules/absorbance-plate-reader.html#csv-data)
        for information on working with these CSV files.

Returns:
    A dictionary of wavelengths to dictionary of values ordered by well name.

源码：module_contexts.py L1355–L1390（固定提交）。

## AbsorbanceReaderContext.serial_number

类型：只读属性；最低版本：requires_version(2, 21)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L1296–L1298（固定提交）。


## ABSMeasureMode 配套类型

initialize的mode使用字符串字面量`"single"`或`"multi"`；无需为调用导入内部类型。范围与参考波长互斥条件见initialize。
