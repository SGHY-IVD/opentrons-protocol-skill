# 第三方正压模块

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-positive-pressure.md) · [API与加载](api-module-positive-pressure.md)；静态安装唯一查[安装关系](installation.txt)。

### 来源、经验与边界

以下按用户提供的过滤程序摘取组织方式，使用当前[API](api-module-positive-pressure.md)。机制/动作条件唯一见[module-conditions](module-conditions-positive-pressure.md#第三方正压模块)，案例安装及偏移唯一见installation；未收录整份DDM处理流程、样本映射、震荡条件或专用移液参数。

- 模块作为完整单文件使用：已包含USB通讯、命令控制和模拟处理。普通协议只创建PPMDevice(protocol)，不要求使用者选择通讯层或手动拼装类。
- 复位是独立的准备操作，按本次初始状态与实验需要选择；不把源程序的可选复位改为每次连接或每次加压的必做动作。
- 正常流程可按“搬入组合耗材→发送本次加压设置→确认可搬出条件后搬回”组织；异常释放连接与正常搬出分开，不在finally中补发复位或搬板。
- 压力与时长依据实际过滤需求和已确认设备范围设定。源程序的两次处理及参数选项不是通用工艺默认；多次调用是多条独立指令，不据C帧的保留字段声称已提供双段压力API。

### 示例前提

完整positive_pressure.py已内嵌在协议中；下列是调用片段，不是完整实验protocol。完整协议仍需本次metadata/requirements/run、硬件与液体初始化。源码注释供编写者阅读，运行comment只描述操作进度。官方模拟自动隔离USB，不在片段中再套dry_run跳过正压。

### A. 创建并执行一次定压计时

```python
def positive_pressure_example(protocol, *, pressure_kpa, seconds):
    with PPMDevice(protocol) as ppm:
        ppm.send_pressure_time(pressure=pressure_kpa, seconds=seconds)
```

with进入时连接、退出时释放连接，不隐含复位。压力单位为kPa，此设备入口的时间单位为秒；不与低层PPMController的毫秒参数混用。真实流程等待指令应答，模拟仅记录并等待计划时长。

### B. 独立复位

前提为本次已确认需要复位、模块承载位为空且工具退出动作包络；片段本身不负责检测这些实物状态。

```python
def positive_pressure_reset_example(protocol):
    with PPMDevice(protocol) as ppm:
        ppm.reset_x_and_z()  # 沿用方法名；当前只确认发送D指令。
```

### C. 整体搬入、加压、正常搬回

assembly为已加载并核对真实几何的组合体；位置和两端抓手偏移已按本次安装确认。当前固件的ok语义及随后可搬出状态已有依据，模块交互位为空、路径和工具状态满足动作条件。未确认这些前提时先补足，不用延时或应答代替压力/机械状态证据。

```python
def positive_pressure_transfer_example(
    protocol, assembly, *, pressure_slot, return_slot,
    source_pick_up_offset, pressure_drop_offset,
    pressure_pick_up_offset, destination_drop_offset,
    pressure_kpa, seconds,
):
    protocol.move_labware(
        assembly, new_location=pressure_slot, use_gripper=True,
        pick_up_offset=source_pick_up_offset,
        drop_offset=pressure_drop_offset,
    )
    with PPMDevice(protocol) as ppm:
        ppm.send_pressure_time(pressure=pressure_kpa, seconds=seconds)
    # 正常搬出：依赖上述已核对的固件应答及可搬出条件。
    protocol.move_labware(
        assembly, new_location=return_slot, use_gripper=True,
        pick_up_offset=pressure_pick_up_offset,
        drop_offset=destination_drop_offset,
    )
```

加压抛异常时不会执行后面的正常搬回；连接释放也不发送停止或复位。这里不固化B4、C1或案例偏移，数值与复用范围继续查installation。
