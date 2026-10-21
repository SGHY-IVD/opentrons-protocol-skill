# TemperatureModuleContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/temperature-module/

本类成员：deactivate, serial_number, set_temperature, start_set_temperature, status, target, temperature。

共享成员（签名及参数见api-module-common.md）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

## TemperatureModuleContext.deactivate

类型：方法；最低版本：requires_version(2, 0)。

```python
deactivate() -> None
```

Stop heating or cooling, and turn off the fan.

源码：module_contexts.py L508–L510（固定提交）。

## TemperatureModuleContext.serial_number

类型：只读属性；最低版本：requires_version(2, 14)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L456–L458（固定提交）。

## TemperatureModuleContext.set_temperature

类型：方法；最低版本：requires_version(2, 0)。

```python
set_temperature(celsius: float) -> None
```

Set a target temperature and wait until the module reaches the target.

No other protocol commands will execute while waiting for the temperature.

Args:
    celsius: A value between 4 and 95, representing the target temperature in °C.

源码：module_contexts.py L462–L471（固定提交）。

## TemperatureModuleContext.start_set_temperature

类型：方法；最低版本：requires_version(2, 3)。

```python
start_set_temperature(celsius: float) -> Task
```

Sets the Temperature Module's target temperature and returns immediately without waiting for the module to reach the target. Allows the protocol to proceed while the Temperature Module heats.

*Changed in version 2.27:* Returns a task object that represents
concurrent heating. Pass the task object to
[`wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
to wait for the module to finish heating.

In API version 2.26 or below, this function returns `None`.

Args:
    celsius: A value between 4 and 95, representing the target
        temperature in °C.

源码：module_contexts.py L475–L493（固定提交）。

## TemperatureModuleContext.status

类型：只读属性；最低版本：requires_version(2, 3)。

```python
status: str
```

One of four possible temperature statuses:

- `holding at target`: The module has reached its target temperature
  and is actively maintaining that temperature.
- `cooling`: The module is cooling to a target temperature.
- `heating`: The module is heating to a target temperature.
- `idle`: The module has been deactivated.

源码：module_contexts.py L532–L541（固定提交）。

## TemperatureModuleContext.target

类型：只读属性；最低版本：requires_version(2, 0)。

```python
target: Optional[float]
```

The target temperature of the Temperature Module's deck in °C.

Returns `None` if no target has been set.

源码：module_contexts.py L523–L528（固定提交）。

## TemperatureModuleContext.temperature

类型：只读属性；最低版本：requires_version(2, 0)。

```python
temperature: float
```

The current temperature of the Temperature Module's deck in °C.

Returns `0` in simulation if no target temperature has been set.

源码：module_contexts.py L514–L519（固定提交）。


## 源码补充成员

以下在固定源码存在，但当前公开参考页未列出；不会因此成为默认调用。calibrate在2.14+不可用，其余仅排查/有明确用途时查。

## TemperatureModuleContext.await_temperature

类型：方法；最低版本：requires_version(2, 3)。

```python
await_temperature(celsius: float) -> None
```

Wait until module reaches temperature.

Args:
    celsius: A value between 4 and 95, representing the target temperature
        in °C.

源码：module_contexts.py L497–L504（固定提交）。

