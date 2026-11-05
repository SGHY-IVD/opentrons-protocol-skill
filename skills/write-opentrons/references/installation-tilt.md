# 第三方扩展：倾斜模块（用户提供案例的软件承载关系）

查用前应用[统一安装核验](installation-core.md#统一安装核验)；这里只维护本对象的承载表达、案例配置及具体证据缺口。
来源：完整洗板模板，SHA-256 3f8af32d1f0257ef7990e3d68aecb52b16b9dd08fd7a7474b89e32ed3269b193。参考范围为原始TiltFlexModule/TiltPlate的单子对象、加载/搬运及坐标实现；当前单文件加载层已提供这些必要承载包装，接口以api-module-tilt.md为准。不是官方fixture/shared-data记录。
物理关系：用户实际安装夹具/承载区域 -> 倾斜模块 -> 案例所维护的一块孔板；父子关系与同槽位独立对象竞争分开判断，模块上的板不因同名位置而再占一个独立普通槽。单子对象是案例软件模型，不宣称模块物理上只能承载一块板，也不据此允许多板/堆叠。
软件表达：原案例向ProtocolContext.load_labware(name, module_slot)或move_labware(new_location=module_slot)登记的是普通槽位中的Labware；实物位于倾斜模块上的父子关系由当前TiltFlexModule/TiltPlate自定义包装维护。创建TiltDevice只控制设备；load_tilt_module先构造包装，随后显式连接、home、加载或搬入，不会注册成官方ModuleContext。物理父层、官方引擎记录与自定义几何三者分别记账，不将普通槽位坐标直接当成实物高度。
位置候选：原洗板模板开放A2/B2/C2/D2；这是模板范围，不是底层安装兼容或各槽实机验证，不据此禁止其他槽位。真实夹具/cutout适配、固定方式、朝向、占位包络、邻位及抓手路径证据仍未提供；按统一核验保留缺口，不杜撰官方fixture id/addressableArea或继承其他模块的安装表。
案例上层板型：corning_96_wellplate_360ul_flat、corning_24_wellplate_3.4ml_flat、corning_6_wellplate_16.8ml_flat。这里只登记源案例的配置名单，不作为模块通用白名单或实物兼容认证；实际定义/几何仍须匹配，其他板型未列出不等于禁止。
案例配置：以原模板当前实际代码为准，旧数值注释已失效，不再作为校准冲突或额外确认项。模块参考高度65.0mm，轴至板底27.0mm，几何角度符号+1、角度补偿0；模块XY偏移0，抓手取/放XY偏移0、Z偏移均为65.8mm。四个候选槽位共用此案例配置。明确复用同一安装、板型及坐标基准时可采用该配置，不因旧注释重复询问；其他安装或板型仍核对本次适用性，板底至孔底距离按匹配板型确定。代码配置不等于逐槽、逐板实机验证。
证据边界：原VALIDATED_GRIPPER_PLATE_SLOT_PAIRS实际是三板型×四槽位的临时全开放集合，注释说仍待硬件验证，不是12组已验证兼容证据。加载/搬运成功后的父层与占位才按实际动作更新；板移出后模块本体仍占用原位置。水平/动作及模拟条件唯一查module-conditions同名节；接口与使用片段查api-module-tilt和module-practices。
