# Opentrons Flex 安装核验与甲板夹具

关系核验逻辑与夹具表更新：2026-10-29；温控上层关系补充：2026-11-04；适用主线：Flex；范围：当前官方耗材清单与6类Flex模块；用户维护的第三方设备在独立条目注明来源及证据状态。
用途：依据按[布局与耗材确认](protocol-interaction.md#布局与耗材确认)确定的配置核对加载层级及官方明确约束；未经授权不替用户设计台面，不进行完整碰撞模拟。
查询顺序：按下方“统一安装核验”解析位置、匹配夹具与区域，再沿实际承载关系核对上层对象。
状态含义：明确支持=有官方条目；明确禁止=有显式约束；未收录/未确认=不自动判断兼容或不兼容，反馈缺失。
用户经验规则与官方事实分别记录。日常只查询本库，升级经用户提出后再外查。

## 统一安装核验

内部判断唯一入口。
对象与关系：cutout为实体安装点；cutoutFixture为该点的夹具配置；addressableArea为夹具提供的区域。区域承载模块或耗材，模块可承载适配器或耗材，适配器承载耗材，耗材可有盖子或合法上层耗材；按实际组合建立分支，不强制补齐每一层。API加载锚点、用户位置名称、cutout、区域和实物对象分别记录，不因名称含相同坐标就视为同一对象。夹具定义可按组合表达模块，但不改变模块本体的对象身份及搬运限制。
输入：本次设备/软件适用范围、用户布局中的对象类型与位置、已知或按既有默认采用的夹具、实际父子关系及当前占用。配置来源和未知状态沿用[交互与确认](protocol-interaction.md)，不新增装机默认。
步骤：
1. 将用户描述映射为实际对象、API位置及所需区域；硬件→slot表只用于候选定位，不单独作为兼容结论。
2. 从所需区域反查可提供它们的夹具及其mayMountTo。对同一cutout的全部需求联合匹配一个配置；跨cutout组合同时检查fixtureGroup。已知实物配置必须匹配；仅存在候选配置不代表实物已安装。共享一个夹具可有多个合法上层分支，不能把夹具安装点直接等同于普通耗材区域被占用。
3. 从各区域沿实际父子关系检查模块、适配器、耗材与盖子，核对相应支持条件、几何和数量边界。分体定义与组合定义按实际条目加载，不重复创建同一实体。几何重叠记录不替代兼容证据。判断涉及模块自身承载位、内部状态或存取条件时，按api-modules对应设备路由核对；具体机制与条件仍在模块资料中维护。
4. 检查同一时刻的区域占用与父子关系：同一承载位置的独立同层对象为竞争关系，上下层为适配关系；同层但处于不同区域不自动竞争，合法上下层不重复占一个台面位置；不同区域是否冲突由共同底层配置与明确约束决定，不能仅凭坐标相同/相邻或对象类别判断。安装兼容与本次移液/抓手/模块动作的可用性分别核对，不从一种能力推出另一种。
5. 加载、搬运、开盖或移出后更新受影响对象的父层、位置与区域占用，保留未搬动的底层夹具/模块；按新状态复用上述核验，不把不同时刻的占用合并。
输出：明确支持、明确禁止或未确认，并在内部保留对应关系/条件及来源。明确禁止须能定位实际违反的关系或条件；缺关系或关键配置未知时报告具体缺口，不能推成兼容或禁止。结论按本次安装/动作范围给出，不冒充完整碰撞验证。
沟通：用户可按最终设备、耗材与位置自然描述；内部解析后仍按这些名称回显结果。无需纠正可正确映射的说辞，不默认展示cutout/夹具/区域推导；实际冲突只说明受影响的实物、位置及必要调整，影响结论的未知用实物名称集中确认；这些反馈也不默认展开底层夹具链或内部字段，仅用户追问原理/安装细节时再解释。

## 一、垃圾处理与夹爪（官方接口事实 + 用户生成规范）
Flex API 2.15：仅固定A3垃圾桶，不调用垃圾桶或垃圾槽加载接口；布局按A3已占用核对。
官方（API 2.16起）：load_trash_bin(location: DeckLocation) -> TrashBin；location 必填。允许 A1/B1/C1/D1/A3/B3/C3/D3 的空位置；禁止第2、4列。
官方（API 2.16起）：load_waste_chute() -> WasteChute；无参数，固定占用D3，不能与另一件占用D3的设备共占槽位。
官方：夹爪无需独立加载，move_labware/move_lid 通过 use_gripper=True 使用。
用户规范（API 2.16起）：脚本出现 drop_tip() 时加载实际垃圾桶或垃圾槽；默认垃圾桶写作 load_trash_bin(location)，传入实际空槽位置。仅特别说明时选择外置垃圾槽；实际装机描述优先，默认偏好不能用于猜补含糊的实物类型。垃圾桶位置按[布局与耗材确认](protocol-interaction.md#布局与耗材确认)确定。该规范不是对API所有合法调用方式的穷举声明。
AI判断边界：内置垃圾桶是可人工调整安装位置的台面固定装置，不是抓手搬运的耗材，不作为move_labware的labware对象。此说明用于内部硬件判断，正常用户回显只需名称和位置；官方API及movableTrash等内部标识保持原名。

## 二、硬件→API位置（候选索引；须经过统一安装核验）
垃圾桶 | A1/B1/C1/D1/A3/B3/C3/D3
外置垃圾槽 | D3
heaterShakerModuleV1 | A1/B1/C1/D1/A3/B3/C3/D3
temperature module gen2（内部model temperatureModuleV2） | A1/B1/C1/D1/A3/B3/C3/D3
温控安装朝向：排风口、电源及USB口须朝台面外侧，第1列朝左、第3列朝右，保持排风通畅，不朝台面中央。依据官方v10.0.0 commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af，docs/temperature-module/docs/pre-installation.md，blob f8abad6d4dbb5530f5699668668dfb56de5e7f54，2026-11-04核对；侧盖人工准备的场景提醒见module-practices温控节。
thermocycler module gen2 / thermocyclerModuleV2 | 加载锚点B1；实体占用A1+B1
magneticBlockV1 | A1–D3全部12个工作区槽位
absorbanceReaderV1 | A3/B3/C3/D3；同排第4列为专用盖停放区，不得作为普通耗材槽使用
flexStackerModuleV1 | API加载位置A4/B4/C4/D4；底层配置及提供区域见下表
明确限制：第4列仅夹爪可达，移液器不可达。
明确限制：使用常规第4列暂存夹具与同排第3列下沉式通电模块存在夹具冲突。
条件关系：D3垃圾槽与D4普通暂存区可共存，但必须使用对应带暂存区的垃圾槽夹具；96通道/夹爪使用垃圾槽需要无盖配置。
条件关系：shared-data另有磁力架+暂存区、Stacker+磁力架、Stacker+垃圾槽的专用组合夹具；不得用“同排第3/4列一律冲突”替代具体配置规则。

## 二补充、甲板夹具与可用位置（安装依赖）
Flex位置命名：A–D为行，1–4为列；A在后、D在前。第1–3列组成12个工作区位置，第4列为暂存/扩展位置，仅夹爪可达，不用于直接移液。
区分三个层次：cutout=物理安装孔位；cutoutFixture=安装在孔位上的夹具/硬件配置；addressableArea=该配置提供的可寻址区域。第4列暂存区由对应第3列的夹具提供，并非另有一个独立的第4列安装孔位。
官方字段：mayMountTo限定夹具可安装的cutout；providesAddressableAreas按cutout列出提供的区域；fixtureGroup用于关联多孔位配置。以下fixture id均为shared-data内部标识，不是耗材load name，也不是需要生成的load调用。

夹具ID | 可安装cutout | 提供区域 | 组合条件
以下r代表A/B/C/D，c代表1/2/3；替换后才是实际内部ID，不作为API加载名。
singleLeftSlot / singleCenterSlot / singleRightSlot | cutoutr1 / cutoutr2 / cutoutr3 | 对应r1 / r2 / r3普通位置 | 各为独立普通夹具
stagingAreaRightSlot | cutoutr3 | r3 + r4 | 普通位置与暂存区域
trashBinAdapter | cutoutr1或cutoutr3 | movableTrashr1或movableTrashr3 | 不提供同排第4列
wasteChuteRightAdapterCovered | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute | 有盖
wasteChuteRightAdapterNoCover | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute + 96ChannelWasteChute + gripperWasteChute | 无盖
stagingAreaSlotWithWasteChuteRightAdapterCovered | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute + D4 | 有盖
stagingAreaSlotWithWasteChuteRightAdapterNoCover | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute + 96ChannelWasteChute + gripperWasteChute + D4 | 无盖
heaterShakerModuleV1 | cutoutr1或cutoutr3 | heaterShakerV1r1或heaterShakerV1r3 | 模块区域
temperatureModuleV2 | cutoutr1或cutoutr3 | temperatureModuleV2r1或temperatureModuleV2r3 | 模块区域
magneticBlockV1 | cutoutrc | magneticBlockV1rc | 模块区域
stagingAreaSlotWithMagneticBlockV1 | cutoutr3 | magneticBlockV1r3 + r4 | 模块与暂存组合
absorbanceReaderV1 | cutoutr3 | absorbanceReaderV1r3 + absorbanceReaderV1LidDockr4 | 第4列为专用盖停放区域
flexStackerModuleV1 | cutoutr3 | flexStackerModuleV1r4 + r3 | 模块与普通位置
flexStackerModuleV1WithMagneticBlockV1 | cutoutr3 | flexStackerModuleV1r4 + magneticBlockV1r3 | 两模块组合
flexStackerModuleV1WithWasteChuteRightAdapterCovered | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute + flexStackerModuleV1D4 | 有盖
flexStackerModuleV1WithWasteChuteRightAdapterNoCover | cutoutD3 | 1ChannelWasteChute + 8ChannelWasteChute + 96ChannelWasteChute + gripperWasteChute + flexStackerModuleV1D4 | 无盖
thermocyclerModuleV2Rear + thermocyclerModuleV2Front | cutoutA1 + cutoutB1 | 后部不提供独立区域；前部提供thermocyclerModuleV2 | fixtureGroup要求两部分同时存在，API锚点B1不释放A1

本表按官方v10.0.0的deck definition v5核对：shared-data/deck/definitions/5/ot3_standard.json，commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af，blob 82dd9a4882708dab83afbf145aa36f47d7bb8a89。仅列本技能维护的6类模块、垃圾处理和普通/扩展配置；不扩展模块/API范围，不代表其他版本及未列组合已验证。具体上层支持和动作条件继续查各自条目。
普通暂存区域自Flex API 2.16支持；2.15不生成以第4列为location/new_location的暂存操作。经核验为普通暂存区域且目标API支持时，使用用户指定的A4–D4作为load_labware的location或move_labware的new_location，无需另写扩展板位加载接口；模块或专用区域按实际父对象和对应API加载/搬运，不以普通第4列位置替代。引用第4列位置表达所需甲板配置，实际硬件和App/机器人上的deck configuration仍须与之匹配，代码不会自动安装扩展件。
加载边界：夹爪无独立加载调用，通过use_gripper=True使用；垃圾槽仍必须显式load_waste_chute()，不能与“扩展夹具无需加载”混为一谈。
夹具表依据上述固定发布快照，位置语义另核对deck-slots文档。记录内部字段用于核对关系，不凭此擅自增加执行接口；若机器人实际配置涉及未收录组合，则反馈缺失。

上层承载关系按实际对象查[官方关系](installation-official-upper.md)，第三方与普通叠板辅助按[安装关系入口](installation.txt)定位；不展开无关对象。
