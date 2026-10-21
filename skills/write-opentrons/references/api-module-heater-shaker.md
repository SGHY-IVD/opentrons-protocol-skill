# HeaterShakerContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/heater-shaker/

本类成员：close_labware_latch, current_speed, current_temperature, deactivate_heater, deactivate_shaker, labware_latch_status, open_labware_latch, serial_number, set_and_wait_for_shake_speed, set_and_wait_for_temperature, set_shake_speed, set_target_temperature, speed_status, target_speed, target_temperature, temperature_status, wait_for_temperature。

共享成员（签名及参数见api-module-common.md）：labware, load_adapter, load_adapter_from_definition, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

## HeaterShakerContext.close_labware_latch

类型：方法；最低版本：requires_version(2, 13)。

```python
close_labware_latch() -> None
```

Closes the labware latch.

The labware latch needs to be closed using this method before sending a shake command,
even if the latch was manually closed before starting the protocol.

源码：module_contexts.py L1241–L1247（固定提交）。

## HeaterShakerContext.current_speed

类型：只读属性；最低版本：requires_version(2, 13)。

```python
current_speed: int
```

The current speed of the Heater-Shaker's plate in rpm.

源码：module_contexts.py L1068–L1070（固定提交）。

## HeaterShakerContext.current_temperature

类型：只读属性；最低版本：requires_version(2, 13)。

```python
current_temperature: float
```

The current temperature of the Heater-Shaker's plate in °C.

Returns `23` in simulation if no target temperature has been set.

源码：module_contexts.py L1059–L1064（固定提交）。

## HeaterShakerContext.deactivate_heater

类型：方法；最低版本：requires_version(2, 13)。

```python
deactivate_heater() -> None
```

Stops heating.

The module will passively cool to room temperature.
The Heater-Shaker does not have active cooling.

源码：module_contexts.py L1260–L1266（固定提交）。

## HeaterShakerContext.deactivate_shaker

类型：方法；最低版本：requires_version(2, 13)。

```python
deactivate_shaker() -> None
```

Stops shaking.

Decelerating to 0 rpm typically only takes a few seconds.

源码：module_contexts.py L1251–L1256（固定提交）。

## HeaterShakerContext.labware_latch_status

类型：只读属性；最低版本：requires_version(2, 13)。

```python
labware_latch_status: str
```

One of six possible latch statuses:

- `opening`: The latch is currently opening (in motion).
- `idle_open`: The latch is open and not moving.
- `closing`: The latch is currently closing (in motion).
- `idle_closed`: The latch is closed and not moving.
- `idle_unknown`: The default status upon reset, regardless of physical latch position.
  Use [`close_labware_latch()`][opentrons.protocol_api.HeaterShakerContext.close_labware_latch] before other commands
  requiring confirmation that the latch is closed.
- `unknown`: The latch status can't be determined.

源码：module_contexts.py L1111–L1123（固定提交）。

## HeaterShakerContext.open_labware_latch

类型：方法；最低版本：requires_version(2, 13)。

```python
open_labware_latch() -> None
```

Open the Heater-Shaker's labware latch.

The labware latch needs to be closed before:

- Shaking
- Pipetting to or from the labware on the Heater-Shaker
- Pipetting to or from labware to the left or right of the Heater-Shaker

Attempting to open the latch while the Heater-Shaker is shaking will raise an error.

!!! note
    Before opening the latch, this command will retract the pipettes upward
    if they are parked adjacent to the left or right of the Heater-Shaker.

源码：module_contexts.py L1222–L1237（固定提交）。

## HeaterShakerContext.serial_number

类型：只读属性；最低版本：requires_version(2, 14)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L1044–L1046（固定提交）。

## HeaterShakerContext.set_and_wait_for_shake_speed

类型：方法；最低版本：requires_version(2, 13)。

```python
set_and_wait_for_shake_speed(rpm: int) -> None
```

核对修正：阻塞至目标转速，返回None；源码docstring中返回Task的句子不准确。并发版本为set_shake_speed。

Sets the Heater-Shaker's shake speed in RPM and waits until the target speed is reached.

!!! note
    Before shaking, this command retracts pipettes upward if they are adjacent
    to the Heater-Shaker Module.

Args:
    rpm: A value between 200 and 3000, representing the target shake speed in
        revolutions per minute.

源码：module_contexts.py L1189–L1201（固定提交）。

## HeaterShakerContext.set_and_wait_for_temperature

类型：方法；最低版本：requires_version(2, 13)。

```python
set_and_wait_for_temperature(celsius: float) -> None
```

Set a target temperature and wait until the module reaches the target.

No other protocol commands will execute while waiting for the temperature.

*Changed in version 2.25:* Removed the minimum temperature limit of 37 °C.
Note that temperatures under ambient are not achievable.

Args:
    celsius: A value under 95, representing the target temperature in °C.
        Values are automatically truncated to two decimal places, and the
        Heater-Shaker module has a temperature accuracy of ±0.5 °C.

源码：module_contexts.py L1126–L1140（固定提交）。

## HeaterShakerContext.set_shake_speed

类型：方法；最低版本：requires_version(2, 27)。

```python
set_shake_speed(rpm: int) -> Task
```

Sets the Heater-Shaker's shake speed in RPM and returns a [`Task`][opentrons.protocol_api.Task] that represents concurrent shaking.

!!! note
    Before shaking, this command will retract the pipettes upward if they are
    parked adjacent to the Heater-Shaker.

Args:
    rpm: A value between 200 and 3000, representing the target shake speed in
        revolutions per minute.

源码：module_contexts.py L1205–L1218（固定提交）。

## HeaterShakerContext.set_target_temperature

类型：方法；最低版本：requires_version(2, 13)。

```python
set_target_temperature(celsius: float) -> Task
```

Set target temperature and return immediately.

Sets the Heater-Shaker's target temperature and returns immediately without
waiting for the target to be reached. Allows the protocol to proceed while the module reaches the target temperature.


Use [`wait_for_temperature()`][opentrons.protocol_api.HeaterShakerContext.wait_for_temperature]
to delay protocol execution for API levels below 2.27.

*Changed in version 2.25:* Removed the minimum temperature limit of 37 °C.
Note that temperatures under ambient are not achievable.

*Changed in version 2.27:* Returns a [`Task`][opentrons.protocol_api.Task] object that represents concurrent
heating. Pass the task object to
[`wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
to wait for the module to reach the target temperature.

Args:
    celsius: A value under 95, representing the target temperature in °C.
        Values are automatically truncated to two decimal places, and the
        Heater-Shaker module has a temperature accuracy of ±0.5 °C.

源码：module_contexts.py L1144–L1175（固定提交）。

## HeaterShakerContext.speed_status

类型：只读属性；最低版本：requires_version(2, 13)。

```python
speed_status: str
```

One of five possible shaking statuses:

- `holding at target`: The module has reached its target shake speed
  and is actively maintaining that speed.
- `speeding up`: The module is increasing its shake speed towards a target.
- `slowing down`: The module was previously shaking at a faster speed
  and is currently reducing its speed to a lower target or to deactivate.
- `idle`: The module is not shaking.
- `error`: The shaking status can't be determined.

源码：module_contexts.py L1096–L1107（固定提交）。

## HeaterShakerContext.target_speed

类型：只读属性；最低版本：requires_version(2, 13)。

```python
target_speed: Optional[int]
```

Target speed of the Heater-Shaker's plate in rpm.

源码：module_contexts.py L1074–L1076（固定提交）。

## HeaterShakerContext.target_temperature

类型：只读属性；最低版本：requires_version(2, 13)。

```python
target_temperature: Optional[float]
```

The target temperature of the Heater-Shaker's plate in °C.

Returns `None` if no target has been set.

源码：module_contexts.py L1050–L1055（固定提交）。

## HeaterShakerContext.temperature_status

类型：只读属性；最低版本：requires_version(2, 13)。

```python
temperature_status: str
```

One of five possible temperature statuses:

- `holding at target`: The module has reached its target temperature
  and is actively maintaining that temperature.
- `cooling`: The module has previously heated and is now passively cooling.
  *The Heater-Shaker does not have active cooling.*
- `heating`: The module is heating to a target temperature.
- `idle`: The module has not heated since the beginning of the protocol.
- `error`: The temperature status can't be determined.

源码：module_contexts.py L1080–L1092（固定提交）。

## HeaterShakerContext.wait_for_temperature

类型：方法；最低版本：requires_version(2, 13)。

```python
wait_for_temperature() -> None
```

Delays protocol execution until the Heater-Shaker has reached its target
temperature.

Raises an error if no target temperature was previously set.

源码：module_contexts.py L1179–L1185（固定提交）。

