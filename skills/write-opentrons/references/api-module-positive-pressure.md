# 第三方正压模块 API 与创建

目录：[范围与来源](#范围与来源) · [完整单文件与创建](#完整单文件与创建) · [构造选项](#构造选项) · [方法与属性](#方法与属性) · [指令与应答](#指令与应答) · [模拟与异常](#模拟与异常) · [原案例差异与边界](#原案例差异与边界)

## 范围与来源

接口以当前[完整正压模块源码](../assets/python/devices/positive_pressure.py)为准。这是用户维护的第三方 Python 类，不是官方 ModuleContext，没有官方 `load_module` 名称或官方 Task。当前仅实现原案例的单段正压 `C` 和复位 `D`；不提供压力实测反馈、状态查询、停止、双段正压或自动搬板接口。

原始依据是用户提供的 `DDM血浆过滤正压_API_2.22.py`，SHA-256 为 `625bcbcdd06a46650d457f4eb767e0263cad52188116a63d152d5aff33cdf098`。原协议的 API 2.22 是该案例的目标，不是扩展要求所有新协议固定采用的版本。安装及承载唯一见[installation](installation.txt)，动作条件见[module-conditions](module-conditions-positive-pressure.md#第三方正压模块)，操作经验与官方搬运调用示例见[module-practices](module-practices-positive-pressure.md#第三方正压模块)。

## 完整单文件与创建

[positive_pressure.py](../assets/python/devices/positive_pressure.py)已完整包含 USB 控制、通讯和设备类；正常使用不拆出通讯层，也不另导入技能目录下的文件。它本身不是实验 protocol。生成完整协议时，将该实现完整内嵌，再编写本次任务的 metadata、requirements 和 run。PyUSB、USB 后端及设备访问权限仍是实机环境依赖，单文件不表示已将这些依赖打包；不能默认上传旁边的 Python 文件就能 import。

沿用原案例的 `PPMDevice(protocol)` 创建方式，不增加加载工厂或 Flex 模块门面。以下片段放在完整实现之后；压力与时间来自本次已确定的实验参数：

```python
ppm = PPMDevice(protocol)
try:
    ppm.connect()
    ppm.send_pressure_time(pressure=pressure_kpa, seconds=pressure_seconds)
finally:
    ppm.disconnect()
```

也可用 `with PPMDevice(protocol) as ppm:` 管理连接。构造不枚举、连接、复位或操作 USB；`PPMDevice` 仅读取当前 `ProtocolContext.is_simulating()` 标记。连接不自动发送复位，断连不发送停止或复位。`reset_x_and_z()` 保留原方法名，但原文名称与注释的轴说明不一致；当前只能确认它发送 `D`，不能据此确定实际复位轴。

耗材仍通过官方 SDK 加载与 `protocol.move_labware()` 搬运；本类没有耗材绑定、占位、坐标或抓手包装。安装关系和搬入、搬出时的条件须分别核对，不由 `connect()` 或 `send_pressure_time()` 检查。

## 构造选项

```text
PPMDevice(context, **kwargs)
PPMController(
    *, transport=None, usb_bus=None, usb_address=None, usb_port_numbers=None,
    response_timeout=5.0, reset_timeout=None, usb_timeout_ms=50,
    max_line_bytes=4096, max_response_bytes=65536,
)
```

`PPMDevice` 将关键字选项传给 `PPMController`。常规协议使用 `PPMDevice(protocol)` 即可；不要机械地把所有通讯选项做成运行参数。直接使用 `PPMController` 时不具备官方模拟隔离。

|选项|含义与当前契约|
|---|---|
|usb_bus / usb_address / usb_port_numbers|可选 USB 物理筛选；多件 CH340 匹配时拒绝猜选。筛选身份不是厂家序列号或正压模块型号识别|
|response_timeout|正有限秒数，默认5；`C` 的总等待期限为发送的毫秒时长换算秒数加此余量，不是每读一行重新计时|
|reset_timeout|默认 None，即采用 response_timeout；显式设置须正有限。`D` 使用此总等待期限，来源未给出复位时长规格|
|usb_timeout_ms|正整数值，默认50毫秒；USB 读取等待还受本次指令剩余期限约束|
|max_line_bytes / max_response_bytes|正整数值，默认4096／65536；限制单行及本次指令累计收到的字节，超限使连接失效|
|transport|默认 None，使用内置 USB 控制；仅维护或离线验证时注入自定义传输。注入实现须自行保证读写有界，不能据此宣称总墙钟时间绝对受限|

USB 控制保留本设备来源中的初始化，不要求用户填写波特率或通讯配置。CH340 的 VID/PID 仅用于查找 USB 芯片，不能证明已识别正压设备型号。导入成功也不证明实机依赖、权限或连接可用。

## 方法与属性

除设备层以秒为单位的正压调用外，`PPMDevice` 继承下列控制器入口。所有列出的动作方法成功时均返回 `None`，不返回状态对象或 Task。

|调用|语义|
|---|---|
|connect()|连接传输；已连接时不重复打开。无型号握手、状态查询或自动复位|
|disconnect() / close()|释放连接；不证明设备停止或泄压|
|with ppm|进入时 connect 并返回本对象；退出时 disconnect，异常继续传播|
|PPMDevice.send_pressure_time(pressure: int, seconds: float)|按秒输入并记录 Opentrons 日志；实机发送 `C`，官方模拟仅日志与 delay|
|PPMController.send_pressure_time(pressure: int, duration_ms: int)|直接按毫秒发送 `C`；不感知 ProtocolContext 模拟标记|
|reset_x_and_z()|发送 `D` 并等应答；官方模拟中仅记录复位日志|

`pressure` 是非负整数值，单位沿用原案例的 kPa；拒绝 bool、非整数值和非有限数。`duration_ms` 是至少1的整数值；上述整数校验允许 `80.0` 这类整值实数。设备层 `seconds` 须为正有限实数，按 `int(seconds * 1000)` 转换，截去小数毫秒；转换不足1毫秒或转换结果非有限时拒绝。源码没有确定固件可接受的压力、时长上限；原协议 UI 的实验范围不构成厂家能力限制，合法数值也不证明适合当前硬件或实验。

|属性|类型与含义|
|---|---|
|connected|只读 bool；实机表示传输当前打开。官方模拟中仅跟踪显式 connect／disconnect，不表示硬件连接|
|last_response|str 缓存；每次真实指令开始时清空，记录收到的有效 UTF-8 文本，包括 busy 行及超时时可解码的末尾片段。不是实时状态或压力读数|

## 指令与应答

只发送以下两个原始指令；每条以 CRLF 结束：

```text
C {pressure} {duration_ms} 0 0\r\n
D\r\n
```

`C` 第二段固定为 `0 0`，没有第二段参数入口。应答须完整接收到 LF 终止的一行；该行去掉两端空白后必须恰为 `ok`，因此接受 LF、CRLF 和两端空白，不接受 `nok`、`okay` 或仅在文本中包含 `ok`。`echo:busy` 行不作为成功依据，也不延长本次固定总期限；没有换行的 `ok` 片段不算成功。

`C` 的期限包括输入清理、写入和等应答，为 `duration_ms / 1000 + response_timeout`；`D` 使用 `reset_timeout`。这是源码的单调时钟期限，不是厂家动作完成时间保证，也不承诺消除 USB 毫秒粒度及系统调度造成的时间偏差。收到 `ok` 只能按现有协议视为应答成功，当前没有独立状态或压力反馈复核。

## 模拟与异常

`PPMDevice` 在官方模拟中不访问 USB；连接、断连和复位仅更新模拟连接标记或日志，正压调用记录日志并执行 `context.delay(seconds=seconds)`，保留完整输入秒数，不缩短正压时间。为保持原案例兼容，模拟正压和模拟复位不要求先 connect；常规协议仍按上面的连接结构组织。官方模拟不证明真实正压、安装或搬板安全。

协议自己的 `dry_run` 不等于官方模拟。当前类不读取 dry_run；真实执行中即使该参数为 True，仍会连接并实际加压。原案例的 dry_run 仅缩短震荡等待，保留正压参数，不应据此新增自动缩时。

参数无效时抛 `ValueError`。通讯错误使用 `PPMCommunicationError`（继承 `TransportError`），应答失败类型为其子类 `AckError`，总期限到期使用 `PPMTimeoutError`（继承 `AckError`）；后两者含 cmd、response 诊断字段。连接阶段也可能传播底层 USB／传输异常，不能只捕获一个设备异常就宣称覆盖所有失败。

任一指令交换失败会关闭并使当前连接失效。未收到 `ok` 不代表命令未执行，`C` 和 `D` 均不自动重发；关闭连接也不证明设备停止或泄压。异常应保留并核实实际设备状态，不能在 finally 中自动复位、重发加压或搬走板。当前没有 `uncertain` 状态查询属性，也没有用于消除这种不确定性的设备查询指令。

## 原案例差异与边界

|原案例内容|当前实现|
|---|---|
|PPMDevice(context)、秒转毫秒、官方模拟 delay、C／D 指令|保留；完整 USB 控制已包含在同一运行文件中|
|应答失败后最多重放3次 C／D|改为只发送一次；失败断连并报告可能已执行，避免 ACK 丢失造成重复动作|
|逐次读取窗口及包含式 ok 判断|改为每条指令固定总期限、完整行去两端空白后精确匹配 ok，并限制应答大小|
|压力／时间直接拼入指令|新增整数值、有限值与最小毫秒检查；不将原 UI 范围升级为厂家上下限|
|复位日志写 XY，方法名写 x_and_z|保留方法名，日志及说明仅称模块复位；实际复位轴仍待核实|
|整份 DDM 加液、震荡、板型代用及抓手偏移|不随设备类自动继承；按本次实验需求、安装与操作经验分别确认|

本接口不推断固件是否在加压结束后才回复、不提供实时压力或机械互锁，也不将 ACK 或模拟通过等同于实机验证。
