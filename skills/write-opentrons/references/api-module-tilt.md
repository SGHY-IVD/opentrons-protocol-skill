# 第三方倾斜模块 API 与加载

目录：[范围与来源](#范围与来源) · [单文件与Flex加载](#单文件与flex加载) · [设备核心](#创建与连接) · [设备方法与属性](#设备方法与属性) · [状态与几何](#状态与几何) · [低层接口](#低层接口) · [耗材加载与原案例差异](#耗材加载与原案例差异)

## 范围与来源

接口以当前[倾斜模块源码](../assets/python/devices/tilt.py)为准，通讯依赖见[扩展入口](extensions.md)。这是用户维护的第三方 Python 类，不是官方 ModuleContext，也没有官方 load_module 名称或官方 Task。Flex 协议仍按本次机器人软件选择目标 API；源码可导入不证明机器人具备 PyUSB、USB后端或设备权限。

原始依据为用户提供的完整洗板模板（源码指纹见扩展文件头）；当前单文件包含通讯、设备控制、必要的Flex加载/承载及几何；完整洗板与自动移液/路径策略没有整体并入。当前硬件/动作条件见[module-conditions](module-conditions-tilt.md#第三方倾斜模块)，安装及承载唯一见[installation](installation.txt)，[示例](module-practices-tilt.md#第三方倾斜模块)提供当前接口的改写参考。

## 单文件与Flex加载

[tilt.py](../assets/python/devices/tilt.py)是完整模块实现，已包含通讯及Flex适配，没有技能内的相对导入或兄弟源码依赖。普通协议生成按此完整入口取用，不再手动拼类。它本身不是实验protocol；生成时将实现完整内嵌，再按任务写metadata/requirements/run。PyUSB及USB后端、实际使用的Opentrons环境仍须可用，单文件不表示把这些环境依赖也打包。外部Python部署另核对机器人导入环境，不能默认App上传旁边文件即可import。

维护源码分层与生成校验见[扩展入口](extensions.md)，不是客户protocol的运行步骤。

```text
config = TiltFlexConfig(
    location=module_slot,
    module_height_mm=measured_translation_z,
    axis_to_plate_bottom_mm=measured_axis_to_plate_bottom,
    plate_bottom_to_well_bottom_mm=matched_plate_bottom_offset,
    geometry_angle_sign=confirmed_geometry_sign,
)
module = load_tilt_module(protocol, config)
```

五个配置均为必填，原案例代码配置及适用范围见installation的第三方条目；创建工厂仅返回TiltFlexModule，不连接、不回零、不加载板。位置/几何是实物配置，通讯默认已封装；这不要求用户填写波特率或把所有字段做成运行参数。

|TiltFlexConfig字段|契约|
|---|---|
|location|实际普通槽位名称；本类仅检查非空，安装兼容另按installation核验|
|module_height_mm|相对普通槽位板坐标的正向Z平移，正有限数；当前承载模型以普通槽位为基准|
|axis_to_plate_bottom_mm / plate_bottom_to_well_bottom_mm|非负有限距离；按匹配实物和定义确定|
|geometry_angle_sign|明确为-1或+1；不是根据默认猜方向|
|module_offset_x_mm / module_offset_y_mm / geometry_angle_offset_deg|默认0，均须有限，与上述基准一致|
|gripper_drop_x/y_mm / gripper_pick_up_x/y_mm|默认0的额外偏移分量|
|gripper_drop_z_mm / gripper_pick_up_z_mm|默认None；使用对应抓手动作时须显式配置有限值，取值依据及原案例复用条件见installation，不按模块高度猜|
|hardware_enabled|默认True；官方模拟自动使用内存后端。显式False也只模拟倾斜设备，不会阻止真实ProtocolContext执行其他机器人动作，不当成整体模拟或dry_run|
|default_speed_deg_s / max_angle_deg / max_speed_deg_s|默认2/30/30；本Flex配置保留来源中上限不超过30的校验，不当作新厂家认证|
|response_timeout_s / home_timeout_s / motion_timeout_margin_s|默认5/45/5秒，传入真实后端；不能与直接TiltDevice的构造字段混写|
|angle_tolerance_deg / level_tolerance_deg|默认0.15/0.25度，前者用于动作完成，后者用于水平加载/搬运；来自源码|
|completion_verify_timeout_s / completion_poll_interval_s / require_homed|默认2秒/0.05秒/True，传入设备层；本加载层另需home建立本连接的几何基准|

配置为frozen dataclass。数值合法性不代表安装与校准已验证；改变承载定义或几何模型时重新核对，不把已经含模块高度的坐标再加一次。

|TiltFlexModule调用|返回与行为|
|---|---|
|connect()|TiltStatus；选择后端并连接，不自动回零|
|disconnect() / close()|None；断连并使姿态无效，不发送停止或回水平|
|with module|进入时connect、退出disconnect，异常继续传播|
|status() / get_status()|TiltStatus；读取状态并按有效基准更新pose|
|home(*, timeout=None)|TiltStatus；成功建立本连接几何基准|
|set_angle(angle_deg, speed_deg_s=None, *, timeout=None)|TiltStatus；绝对角度移动|
|change_angle(delta_deg, speed_deg_s=None, *, timeout=None)|TiltStatus；相对移动，以当前可信状态计算目标|
|level(speed_deg_s=None)|TiltStatus；回到几何0°，硬件目标为-offset/sign；已在水平容差内不新增运动，目标超界或调平后仍超水平容差则拒绝|
|calibrate_zero()|TiltStatus；显式写Flash，无confirm参数；之后清除几何基准，须重新home后才能取坐标|
|load_labware(load_name, *, label=None)|TiltPlate；登记已人工放在模块上的一块板，不进行抓手搬运|
|unload_labware()|原生Labware；以官方人工搬运到OFF_DECK记录移除，再解除绑定|
|move_labware_onto_module(labware, *, use_gripper=True, source_pick_up_offset=None)|TiltPlate；以普通槽位move_labware搬入并绑定；抓手放板用config.drop偏移|
|move_labware_off_module(new_location, *, use_gripper=True, destination_drop_offset=None)|原生Labware；搬出成功才解除绑定；抓手取板用config.pick_up偏移|

只读属性：connected、device_info、homed、angle、pose、geometry_angle_sign、labware、child、tilt_plate；labware记录已登记的原生耗材占用，child/tilt_plate为可选TiltPlate。几何构造失败仍保留labware，不能因child为None就当承载位为空。angle是缓存，只有pose.valid时才可用于几何。TiltPose是frozen dataclass，字段hardware_angle_deg、geometry_angle_deg、valid、revision。加载层的homed表示本连接显式home成功；与下文设备核心只按设备状态控制的含义分别维护。

模块运动、标定、读取异常及断连使姿态失效，成功确认后才恢复；搬板失败不冒充已完成解除绑定。层内会检查空闲、几何基准、几何角水平和单板占用，但没有检测移液器/抓手退出的安全互锁，也没有完整碰撞分析。操作条件仍按module-conditions核对。

|TiltPlate调用/属性|含义|
|---|---|
|labware|原生SDK Labware，用于孔访问及液体初始化，不隐含倾斜坐标|
|location(well_name, *, origin="bottom", x=0, y=0, z=0)|先在板局部坐标偏移，再做平移/Y旋转，返回Location；origin可bottom/center/top|
|bottom(well_name, z=0, *, x=0, y=0)|倾斜补偿后的孔底相对Location|
|center(well_name, *, x=0, y=0, z=0)|倾斜补偿后的孔中心相对Location|
|top(well_name, z=0, *, x=0, y=0)|倾斜补偿后的孔顶相对Location|
|attached / pose / hardware_angle_deg / geometry_angle_deg|绑定/姿态快照；已移出、断连或无有效几何基准时坐标方法拒绝使用|

TiltPlate不是原生Labware，也不提供TiltPipette/Gate、沿壁/低侧自动移液、液面模型或路径。由模块成功绑定返回，不能仅创建一个几何对象就假定实物已加载。

## 创建与连接

```text
TiltDevice(
    *, usb_bus=None, usb_address=None, usb_port_numbers=None,
    default_speed_deg_s=2.0, max_angle_deg=30.0, max_speed_deg_s=30.0,
    response_timeout=5.0, motion_timeout=30.0, motion_timeout_margin=5.0,
    angle_tolerance_deg=0.15, completion_verify_timeout=2.0,
    completion_poll_interval=0.05, require_homed=True,
)
```

普通调用使用 `TiltDevice()` 即可；通讯实现内部固定115200/8N1，没有波特率参数，不要求用户填写这些实现细节。只有实际设备选择、实测校准或维护需要才调整对应选项，不能把所有构造参数机械地做成 protocol 运行参数。

|参数组|含义与当前契约|
|---|---|
|usb_bus / usb_address / usb_port_numbers|可选USB物理筛选；port_numbers为整数tuple；多件匹配时拒绝猜选，身份不等于厂家序列号|
|default_speed_deg_s|省略运动速度时使用；正有限数且不超过配置上限|
|max_angle_deg / max_speed_deg_s|当前默认对应±30°、速度(0,30]°/s；配置上限本身须正有限。源码没有把可配置上限硬锁为30，但提高配置不等于硬件能力得到确认|
|response_timeout / motion_timeout|单次回复等待；后者作为home默认等待。均为正有限秒数|
|motion_timeout_margin|普通移动预估时间余量，非负有限秒数；省略移动timeout时用max(response_timeout, abs(travel)/speed + margin)，不是统一套用motion_timeout|
|angle_tolerance_deg|完成确认的角度容差，正有限数|
|completion_verify_timeout / completion_poll_interval|动作回复后的状态同步窗口与查询间隔，均为正有限秒数；内部单次状态查询另受回复/USB等待约束，不宣传为严格总时限|
|require_homed|True时，设备报告state=2则拒绝普通运动；不是“每次连接必先home”的流程开关；状态1/3仍拒绝普通运动|

所有默认值来自提供的源码，不标为本次新核实的厂家规格。导入、构造不枚举或连接USB。`open()`执行连接及只读握手，不自动回零或标定；可用 `with TiltDevice() as tilt:`管理连接。首次Ping超时仅允许重新连接后的只读握手重试，不重放运动。

## 设备方法与属性

下表是 `TiltDevice` 的公开调用入口；除标明项外无其他位置参数。

|调用|返回|语义|
|---|---|---|
|open() / connect()|TiltConnectionInfo|连接并执行Ping→原始设备信息→状态握手|
|close() / disconnect()|None|释放连接并清空会话缓存；不发送停止、回零或回水平命令|
|ping()|True|收到合法回复则返回True；失败抛异常，不返回False|
|refresh_device_info()|dict副本|更新raw_payload_hex、printable_ascii、note；字段布局仍待厂家确认，不能据此宣称已验证设备型号|
|status()|TiltStatus|新查询的设备状态|
|home(*, timeout=None)|TiltStatus|发送回零，确认状态及0°完成；成功记录本会话homed|
|move_to(angle_deg, speed_deg_s=None, *, timeout=None)|TiltStatus|绝对角度移动并确认完成|
|move_by(delta_deg, speed_deg_s=None, *, timeout=None)|TiltStatus|相对移动；增量本身和预计最终角度均检查配置范围|
|calibrate_zero()|TiltStatus|显式写Flash零点并重新查询状态；无confirm参数，不作为普通初始化|

`__enter__()`先open并返回对象，`__exit__()`执行close且不吞异常。

|只读属性|类型与含义|
|---|---|
|connected|bool；传输对象存在且打开，不替代型号或全流程验证|
|active_transport|Optional[str]；当前实现为pyusb，未连接可为None|
|last_status|Optional[TiltStatus]；已连接时最后一次记录，非实时监测；断连为None|
|homed|bool；当前已连接且本会话成功home；False不自动等于硬件报告state=2|
|device_info|Optional[dict]；已连接时缓存副本，否则None|

`controller`是所包装的低层对象，`default_speed_deg_s`保存默认速度。常规流程优先使用上表，不需要直接改内部状态。

动作按提供的设备协议等待运动回复，再确认状态空闲及目标角度；返回不是官方并发Task。失败的字节交换会断连、使缓存失效并抛异常；断连不证明机械已停止。无stop/wait等未实现方法，异常收尾不自动补发运动。通讯异常为TiltCommunicationError，其子类为TiltTimeoutError；TiltStateError和TiltCalibrationError分别直接继承TiltError；TiltOutOfRangeError继承ValueError，CRC错误可直接为ValueError，USB异常也可能原样传播，不能只捕获TiltError就宣称覆盖所有失败。

## 状态与几何

`TiltStatus(state, state_text, angle_deg, raw_payload_hex="")`是frozen dataclass；state值0=空闲且在位、1=运动中、2=未回零、3=堵转或故障。只读属性is_idle/is_moving/needs_home/has_fault分别对应这些值；as_dict()返回四个字段的字典，不额外生成计算属性。查询拒绝未知状态码及非有限角度。

`TiltConnectionInfo(transport, device_info, status, usb_identity=None, stale_handle_released=False)`是frozen dataclass；usb_identity包含bus/address/port_numbers，stale_handle_released只表示本次恢复了同物理身份的失效句柄。

```text
TiltGeometry(axis_x: float, axis_z: float)
rotate(point: Point, angle_deg: float) -> Point
```

axis_x/axis_z必填，须与输入Point处于同一坐标系及单位；旋转角为几何角度。返回新Point，绕平行于台面Y轴的轴旋转，Y不变；只有使用rotate时才需要Opentrons Point。类不推断安装平移、轴心、硬件角度正负对应、液面、耗材父层或运动路径，也没有输入有限数或安全角度校验。实际输入及空间有效性按模块条件核对。

## 低层接口

仅在通讯维护或排错时读取 `TiltController`。构造选项与TiltDevice相同，但没有default_speed_deg_s；connect()只打开传输并返回None，不执行设备完整握手。

|调用|返回|
|---|---|
|connect() / disconnect()|None|
|ping()|含payload_hex的dict|
|get_status()|state/state_text/angle_deg/raw_payload_hex字典|
|get_fm_info()|原始设备信息字典|
|home(*, timeout=None)|含ack和status的dict|
|move_absolute(angle_deg, speed_deg_s, *, timeout=None)|含ack和status的dict|
|move_relative(delta_deg, speed_deg_s, *, timeout=None)|含ack和status的dict|
|calibrate_zero()|含ack和status的dict|

设备帧、命令码和CRC算法仍由源码唯一维护，不在模块资料复制第二份实现。通用通讯层只负责字节传输。

## 耗材加载与原案例差异

当前已提供load_tilt_module、TiltFlexConfig、TiltFlexModule、TiltPlate及真实/内存后端；这是必要加载适配的改写，不是将整份旧案例直接复制。当前配置必须显式给出几何，抓手偏移不再回退到猜测高度；工厂与构造不隐藏连接或回零。

|原案例内容|当前边界|
|---|---|
|TiltPipette、bind_pipette、Gate/吸排目标/自动路径|未收录，不能当作当前模块能力|
|默认C2、原案例安装配置、板型×槽位全开放|不单独证明当前安装兼容或校准；配置复用范围见installation|
|calibrate_zero(confirm=True)、save_logs|当前无该参数/日志方法，不照搬旧调用|
|普通槽位加载/搬运再自定义绑定|保留该软件表达；物理父子关系与官方引擎记录分别核对|

正常home回硬件0°，level回几何0°；有非零几何偏移时两者不同。写Flash标定另行处理。当前模拟后端只处理设备状态及几何流程，不证明真实安装、抓手、移液精度或碰撞。
