# ThermocyclerContext

来源：Opentrons开源module_contexts.py，提交`05b494ba81636978fb79f08bbc20468f94464d5c`；核对日期2026-10-16。签名/类型/默认值与说明按源码提取；公开成员集合与官方参考页核对。仅API 2.30范围，不把edge新增2.31接口带入。Optional[X]表示X或None；未带默认值参数必填。源码中的文档链接为上游引用，离线使用先查本技能。

官方参考：https://docs.opentrons.com/python-api/reference/thermocycler/

本类成员：block_target_temperature, block_temperature, block_temperature_status, close_lid, deactivate, deactivate_block, deactivate_lid, execute_profile, lid_position, lid_target_temperature, lid_temperature, lid_temperature_status, open_lid, serial_number, set_block_temperature, set_lid_temperature, start_execute_profile, start_set_block_temperature, start_set_lid_temperature。

共享成员（签名及参数见api-module-common.md）：labware, load_labware, load_labware_by_name, load_labware_from_definition, model, parent, type。

## ThermocyclerContext.block_target_temperature

类型：只读属性；最低版本：requires_version(2, 0)。

```python
block_target_temperature: Optional[float]
```

The target temperature of the well block in °C.

源码：module_contexts.py L961–L963（固定提交）。

## ThermocyclerContext.block_temperature

类型：只读属性；最低版本：requires_version(2, 0)。

```python
block_temperature: Optional[float]
```

The current temperature of the well block in °C.

源码：module_contexts.py L955–L957（固定提交）。

## ThermocyclerContext.block_temperature_status

类型：只读属性；最低版本：requires_version(2, 0)。

```python
block_temperature_status: str
```

One of five possible temperature statuses:

- `holding at target`: The block has reached its target temperature
  and is actively maintaining that temperature.
- `cooling`: The block is cooling to a target temperature.
- `heating`: The block is heating to a target temperature.
- `idle`: The block is not currently heating or cooling.
- `error`: The temperature status can't be determined.

源码：module_contexts.py L925–L935（固定提交）。

## ThermocyclerContext.close_lid

类型：方法；最低版本：requires_version(2, 0)。

```python
close_lid() -> str
```

Close the lid.

源码：module_contexts.py L680–L682（固定提交）。

## ThermocyclerContext.deactivate

类型：方法；最低版本：requires_version(2, 0)。

```python
deactivate() -> None
```

Turn off both the well block temperature controller and the lid heater.

源码：module_contexts.py L906–L908（固定提交）。

## ThermocyclerContext.deactivate_block

类型：方法；最低版本：requires_version(2, 0)。

```python
deactivate_block() -> None
```

Turn off the well block temperature controller.

源码：module_contexts.py L900–L902（固定提交）。

## ThermocyclerContext.deactivate_lid

类型：方法；最低版本：requires_version(2, 0)。

```python
deactivate_lid() -> None
```

Turn off the lid heater.

源码：module_contexts.py L894–L896（固定提交）。

## ThermocyclerContext.execute_profile

类型：方法；最低版本：requires_version(2, 0)。

```python
execute_profile(steps: List[ThermocyclerStep], repetitions: int, block_max_volume: Optional[float]=None) -> None
```

Execute a Thermocycler profile, defined as a cycle of
`steps`, for a given number of `repetitions`.

Args:
    steps: List of steps that make up a single cycle.
        Each list item should be a dictionary that maps to the parameters
        of the [`set_block_temperature()`][opentrons.protocol_api.ThermocyclerContext.set_block_temperature]
        method. The dictionary's keys must be `temperature` and one or both of
        `hold_time_seconds` and `hold_time_minutes`.
    repetitions: The number of times to repeat the cycled steps.
    block_max_volume: The greatest volume of liquid contained in any
        individual well of the loaded labware, in µL. If not specified,
        the default is 25 µL.

*Changed in version 2.21:* Fixed run log listing number of steps instead of
number of repetitions.

源码：module_contexts.py L825–L855（固定提交）。

## ThermocyclerContext.lid_position

类型：只读属性；最低版本：requires_version(2, 0)。

```python
lid_position: Optional[str]
```

One of these possible lid statuses:

- `closed`: The lid is closed.
- `in_between`: The lid is neither open nor closed.
- `open`: The lid is open.
- `unknown`: The lid position can't be determined.

源码：module_contexts.py L912–L921（固定提交）。

## ThermocyclerContext.lid_target_temperature

类型：只读属性；最低版本：requires_version(2, 0)。

```python
lid_target_temperature: Optional[float]
```

The target temperature of the lid in °C.

源码：module_contexts.py L973–L975（固定提交）。

## ThermocyclerContext.lid_temperature

类型：只读属性；最低版本：requires_version(2, 0)。

```python
lid_temperature: Optional[float]
```

The current temperature of the lid in °C.

源码：module_contexts.py L967–L969（固定提交）。

## ThermocyclerContext.lid_temperature_status

类型：只读属性；最低版本：requires_version(2, 0)。

```python
lid_temperature_status: Optional[str]
```

One of five possible temperature statuses:

- `holding at target`: The lid has reached its target temperature
  and is actively maintaining that temperature.
- `cooling`: The lid has previously heated and is now passively cooling.
    *The Thermocycler lid does not have active cooling.*
- `heating`: The lid is heating to a target temperature.
- `idle`: The lid has not heated since the beginning of the protocol.
- `error`: The temperature status can't be determined.

源码：module_contexts.py L939–L951（固定提交）。

## ThermocyclerContext.open_lid

类型：方法；最低版本：requires_version(2, 0)。

```python
open_lid() -> str
```

Open the lid.

源码：module_contexts.py L674–L676（固定提交）。

## ThermocyclerContext.serial_number

类型：只读属性；最低版本：requires_version(2, 14)。

```python
serial_number: str
```

Get the module's unique hardware serial number.

源码：module_contexts.py L668–L670（固定提交）。

## ThermocyclerContext.set_block_temperature

类型：方法；最低版本：requires_version(2, 0)。

```python
set_block_temperature(temperature: float, hold_time_seconds: Optional[float]=None, hold_time_minutes: Optional[float]=None, ramp_rate: Optional[float]=None, block_max_volume: Optional[float]=None) -> None
```

Set the target temperature for the well block, in °C.

Args:
    temperature: A value between 4 and 99, representing the target
        temperature in °C.
    hold_time_minutes: The number of minutes to hold, after reaching
        `temperature`, before proceeding to the next command. If
        `hold_time_seconds` is also specified, the times are added
        together.
    hold_time_seconds: The number of seconds to hold, after reaching
        `temperature`, before proceeding to the next command. If
        `hold_time_minutes` is also specified, the times are added
        together.
    block_max_volume: The greatest volume of liquid contained in any
        individual well of the loaded labware, in µL. If not specified,
        the default is 25 µL.
    ramp_rate: The rate to heat or cool the Thermocycler Module's block,
        in °C/second. The acceptable range is 0.01–2 °C/second
        to cool the block, and 0.01–4.25 °C/second to heat the block. If not specified,
        the block will heat or cool as quickly as possible to reach the set temperature.

        *Changed in version 2.27:* In API version
        2.27 and newer, the API will first attempt to use the liquid tracking in labware, then default to 25 µL if the protocol lacks probed or loaded
        liquid information.

*Changed in version 2.28:* Use the optional `ramp_rate` parameter to control how quickly
the block heats or cools.

!!! note
    If `hold_time_minutes` and `hold_time_seconds` are not specified,
    the Thermocycler will proceed to the next command immediately after
    `temperature` is reached.

源码：module_contexts.py L686–L743（固定提交）。

## ThermocyclerContext.set_lid_temperature

类型：方法；最低版本：requires_version(2, 0)。

```python
set_lid_temperature(temperature: float) -> None
```

Set the target temperature for the heated lid, in °C.

Args:
    temperature: A value between 37 and 110, representing the target
        temperature in °C.

!!! note
    The Thermocycler will proceed to the next command immediately after
    `temperature` is reached.

源码：module_contexts.py L792–L804（固定提交）。

## ThermocyclerContext.start_execute_profile

类型：方法；最低版本：requires_version(2, 27)。

```python
start_execute_profile(steps: List[ThermocyclerStep], repetitions: int, block_max_volume: Optional[float]=None) -> Task
```

Starts a defined Thermocycler Module profile and returns a [`Task`][opentrons.protocol_api.Task] representing its concurrent execution.
Profile is defined as a cycle of `steps`, for a given number of `repetitions`.

Pass the task object to [`ProtocolContext.wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
to wait for the profile to complete.

Args:
    steps: List of steps that make up a single cycle.
        Each list item should be a dictionary that maps to the parameters
        of the [`set_block_temperature()`][opentrons.protocol_api.ThermocyclerContext.set_block_temperature]
        method. The dictionary's keys must be `temperature` and one or both of
        `hold_time_seconds` and `hold_time_minutes`.
    repetitions: The number of times to repeat the cycled steps.
    block_max_volume: The greatest volume of liquid contained in any
        individual well of the loaded labware, in µL. If not specified, the
        default is 25 µL.

源码：module_contexts.py L859–L890（固定提交）。

## ThermocyclerContext.start_set_block_temperature

类型：方法；最低版本：requires_version(2, 27)。

```python
start_set_block_temperature(temperature: float, ramp_rate: Optional[float]=None, block_max_volume: Optional[float]=None) -> Task
```

Sets the target temperature for the Thermocycler Module's well block, in °C.

Returns a [`Task`][opentrons.protocol_api.Task] object that represents concurrent heating.
Pass the task object to [`ProtocolContext.wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
to wait for the preheat to complete.

Args:
    temperature: A value between 4 and 99, representing the target
        temperature in °C.
    block_max_volume: The greatest volume of liquid contained in any
        individual well of the loaded labware, in µL. If not specified,
        the default is 25 µL.
    ramp_rate: The rate to heat or cool the Thermocycler Module's block,
        in °C/second. The acceptable range is 0.01–2 °C/second
        to cool the block, and 0.01–4.25 °C/second to heat the block. If not specified,
        the block will heat or cool as quickly as possible to reach the set temperature.

*Changed in version 2.27:* In API version 2.27 and newer, the API will first attempt to use the liquid tracking in labware, then default to 25 µL if the protocol lacks probed or loaded
liquid information.

*Changed in version 2.28:* Use the optional `ramp_rate` parameter to control how quickly
the block heats or cools.

源码：module_contexts.py L747–L788（固定提交）。

## ThermocyclerContext.start_set_lid_temperature

类型：方法；最低版本：requires_version(2, 27)。

```python
start_set_lid_temperature(temperature: float) -> Task
```

Sets a target temperature to heat the Thermocycler Module's lid, in °C.

Returns a [`Task`][opentrons.protocol_api.Task] object that represents concurrent heating.
Pass the task object to [`wait_for_tasks()`][opentrons.protocol_api.ProtocolContext.wait_for_tasks]
to wait for the lid to reach the target temperature.

Args:
    temperature: A value between 37 and 110, representing the target
        temperature in °C.

源码：module_contexts.py L808–L821（固定提交）。


## 源码补充成员

以下在固定源码存在，但当前公开参考页未列出；不会因此成为默认调用。calibrate在2.14+不可用，其余仅排查/有明确用途时查。

## ThermocyclerContext.ramp_rate

类型：只读属性；最低版本：requires_version(2, 0)。

```python
ramp_rate: Optional[float]
```

The current ramp rate in °C/s.

源码：module_contexts.py L979–L981（固定提交）。

## ThermocyclerContext.hold_time

类型：只读属性；最低版本：requires_version(2, 0)。

```python
hold_time: Optional[float]
```

Remaining hold time in seconds.

源码：module_contexts.py L985–L987（固定提交）。

## ThermocyclerContext.total_cycle_count

类型：只读属性；最低版本：requires_version(2, 0)。

```python
total_cycle_count: Optional[int]
```

Number of repetitions for current set cycle

源码：module_contexts.py L991–L993（固定提交）。

## ThermocyclerContext.current_cycle_index

类型：只读属性；最低版本：requires_version(2, 0)。

```python
current_cycle_index: Optional[int]
```

Index of the current set cycle repetition

源码：module_contexts.py L997–L999（固定提交）。

## ThermocyclerContext.total_step_count

类型：只读属性；最低版本：requires_version(2, 0)。

```python
total_step_count: Optional[int]
```

Number of steps within the current cycle

源码：module_contexts.py L1003–L1005（固定提交）。

## ThermocyclerContext.current_step_index

类型：只读属性；最低版本：requires_version(2, 0)。

```python
current_step_index: Optional[int]
```

Index of the current step within the current cycle

源码：module_contexts.py L1009–L1011（固定提交）。


## ThermocyclerStep 配套类型

来源：固定提交api/src/opentrons/protocols/api_support/types.py。用普通字典传steps，不需要实例化此类型。temperature必填，hold字段至少指定一个；ramp_rate是源码类型的可选字段，仍核对具体API版本及执行方法支持。

```python
class ThermocyclerStepBase(TypedDict):
    temperature: float

class ThermocyclerStep(ThermocyclerStepBase, total=False):
    hold_time_seconds: float
    hold_time_minutes: float
    ramp_rate: Optional[float]
```

状态类属性中的None是未设定/不可用等状态，不能转成默认0继续判断。
