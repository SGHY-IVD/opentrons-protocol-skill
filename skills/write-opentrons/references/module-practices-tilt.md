# 第三方倾斜模块

[模块索引](api-modules.md) · [本设备机制与条件](module-conditions-tilt.md) · [API与加载](api-module-tilt.md)；静态安装唯一查[安装关系](installation.txt)。

### 来源、经验与边界

以下按用户提供的完整洗板案例改写，使用当前[接口](api-module-tilt.md)，按当前必要加载适配改写。机制和动作条件唯一见[module-conditions](module-conditions-tilt.md#第三方倾斜模块)；安装/承载和案例配置证据唯一见installation。原案例证明存在相应代码路径，不代表本项目新验证了实机效果。

- 沿用案例的组织方式：先确认设备与几何基准，再登记/搬入孔板，执行已确认的倾斜步骤，正常结束按任务回水平及搬出。轻量TiltDevice不强制逐连接回零；完整加载层为本连接几何基准要求显式home。硬件home与几何水平可不同，加载前调用level按当前映射调平。
- 优先复用当前默认通讯设置，无需向操作员询问波特率。多台USB设备时只补齐实际设备选择信息，不用芯片相同代替型号核对。
- 当前位置与动作结果不确定时先保留状态并核对；不以finally自动归零、回水平或抓手搬板作为通用恢复。正常收尾与异常释放连接分别处理。
- 暂不推广旧洗板工艺值、Gate路径、混匀角度、流速倍率或板型白名单。倾斜移液仍按实际任务和现有操作规则编写；独立核对枪头/喷嘴、孔壁、真实液面和动作包络，不能因坐标函数可算就认定能安全移液。

### 示例前提

四个片段分别展示轻量设备控制、完整加载、搬入搬出及载板坐标，不是完整洗板protocol，不增加新的模块API。完整tilt.py已内嵌或单独正确部署，含通讯/设备/加载/几何；无需再拼接兄弟源码。完整协议继续补齐本次API、液体初始化、实验步骤与审查，不在客户代码里从技能目录导入。

angle、位置、板名、校准及抓手偏移由实际任务确定；这里只用函数参数表达，原案例数值及适用范围见installation。移动设备前已确认枪头和抓手退出运动包络；搬板片段的前提为模块已处于本次核对的空闲、无故障、水平状态，目标承载位与路径已确认。示例不能代替这些前提，也不据其分析通过宣称实机通过。

### A. 创建、查询与显式运动

官方模拟先隔离真实USB；这不是为倾斜设备提供了仿真后端。正常分支只在任务需要时调用，最后正常回0°与连接释放分开；异常不会再发一次运动。

```python
def tilt_motion_example(protocol, *, angle_deg, speed_deg_s=None):
    if protocol.is_simulating():
        protocol.comment("模拟：跳过倾斜设备控制")
        return None
    with TiltDevice() as tilt:
        tilt.home()  # 本例显式建立基准；不写入Flash。
        tilt.move_to(angle_deg, speed_deg_s)
        # 在此组织已确认的实验步骤及必要等待。
        return tilt.move_to(0.0, speed_deg_s)  # 正常结束回硬件0°。
```

创建与with进入不加载孔板；读取状态用tilt.status()，连接结果用tilt.open()，不混淆为官方模块的加载返回值。需要留在指定倾角时按任务调整正常收尾，不把本例回0°当强制默认。

### B. 完整加载：板预先在模块上

config为已核对的TiltFlexConfig，其中位置、几何和抓手偏移按实际确定；复用原案例配置时按installation核对适用范围。工厂只构造，with进入时选择真实/内存后端并连接；官方模拟自动走内存后端，不打开真实USB。load_labware返回TiltPlate，自带平移、旋转与绑定检查。

```python
def tilt_plate_record_example(protocol, *, config, load_name, angle_deg):
    with load_tilt_module(protocol, config) as module:
        module.home()
        module.level()  # 按几何水平校准；不等同于无条件再做一次运动。
        plate = module.load_labware(load_name, label="倾斜板")
        module.set_angle(angle_deg)
        # 在此按本次任务使用plate；坐标用其bottom/top/location方法。
        module.level()
        return plate.labware
```

返回的是原生Labware；with结束会断连并使倾斜坐标失效。此例不执行移液，原生Labware也不隐含倾斜高度或角度。完整协议通过plate.labware完成实际液体初始化，使用TiltPlate获得当前可信姿态的点。

### C. 抓手搬入、倾斜、正常调平并搬出

plate已在其他已确认位置加载；config中已提供对应抓手取/放Z及必要XY偏移。无需手动调用普通move_labware并维护两套绑定；加载层在成功动作后更新child和labware，搬出成功才解除绑定。动作前仍须真实工具与路径已确认。

```python
def tilt_plate_move_example(protocol, plate, *, config, end_slot, angle_deg):
    with load_tilt_module(protocol, config) as module:
        module.home()
        module.level()
        module.move_labware_onto_module(plate, use_gripper=True)
        module.set_angle(angle_deg)
        # 在此组织已确认的模块上操作；不默认生成洗板或移液策略。
        module.level()
        return module.move_labware_off_module(end_slot, use_gripper=True)
```

异常退出仅释放连接，不在finally自动回水平或搬板。若SDK已经登记/搬入、几何视图构造失败，module.labware仍记录占用，child可为None；不能当空模块继续加载。取得新的有效状态/基准并核对实物后，再显式卸载或搬出；失败状态不猜物理结果。

### D. 直接读取载板补偿坐标

tilt_plate由当前模块load_labware或move_labware_onto_module返回；须仍绑定、连接且有有效姿态。方法完成必要平移及旋转，调用者无需再次手算模块高度或组合Point；它只返回Location，不执行运动。

```python
def tilt_plate_locations_example(tilt_plate, *, well_name, local_z):
    return {
        "bottom": tilt_plate.bottom(well_name, z=local_z),
        "center": tilt_plate.center(well_name),
        "top": tilt_plate.top(well_name),
    }
```

Location仍关联原始Well；没有自动写入官方引擎的倾斜姿态/液面模型。移出或姿态失效后旧TiltPlate会拒绝获取坐标。实际移液路径、液面与边界仍按本次方案核对。
