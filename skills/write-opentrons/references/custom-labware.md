# 自定义耗材：AI构建与复用经验

仅在询问自定义耗材的创建/修改/复用/交付，或实验耗材核对时缺少匹配定义时读取；不加入首次硬件引导。单独制作耗材文件按本次定义需求收集资料，不重跑完整protocol的开局确认；用于具体协议时仍核对其实际配置。核心规则、加载API及审查仍归原有资料。

## 接入与复用

保持原有硬件→实验方案流程。用户提供确切JSON、指定成品或明确自定义时直接复用相应信息；其余先按catalog完成官方常用项/Flex范围索引与同款定义查找。仍缺匹配定义时，再按品牌、货号和安装组合查`assets/labware/`并引导创建。第三方品牌不等于没有官方定义，常用表或某发布索引缺项也不等于实物不受支持。普通已支持耗材不扫描成品库。

匹配同款成品就复用，省去重建和重复测量；相似容量/孔数不能当同款。没有匹配定义时，说明可自定义并在当前方案中集中确认是否创建；已明确要求则直接推进。用户不创建时保留受影响部分未决，不擅换耗材。

成品目录用于共享可复用成果；仅以实际文件判断已收录内容。按用户明确要求收录原始文件及其具体使用结论，不强制索引、登记表或另建版本体系；本次客户生成物不自动加入共享库。库文件不承担教学示例职责，格式参考优先官方定义/schema。

## 成品命名与数据约定

沿用官方Labware JSON schema，不另加包装层；保留必需字段与原物理数据。文件用UTF-8、两空格缩进、末尾换行。
- 文件名＝`parameters.loadName`＋`.json`；采用小写ASCII和下划线：`品牌_孔数_类别_容量ul_必要特征`。孔板类别用wellplate；底形用u_bottom、v_bottom或flat；有准确货号或需区分同规格产品时追加，不编造货号。
- `metadata.displayName`供人阅读：品牌＋孔数/孔形/底形＋容量；统一`brand.brand`品牌写法，中文名、旧名称可保留在metadata.tags帮助检索。已有估算、近似及用途限制说明保留；状态/日期不强塞进加载身份。
- 本库比克曼品牌键用bkmamlab，品牌写BKMAMLAB，中文别名“比克曼”。例如`bkmamlab_96_wellplate_1300ul_u_bottom.json`，另一款为`bkmamlab_96_wellplate_300ul_v_bottom.json`。
- namespace/version保留原值，不另建管理体系；内部模型ID保持稳定并核对逐孔引用。命名调整不改坐标、尺寸、容量、模型或安装/抓手限制；修改loadName需告知旧脚本引用的变化，旧名作为检索说明不等于API加载别名。

## 创建思路与数据准备

向客户说明“可以自定义，准确的物理数据是基础”，按已有资料选路引导，不逐字段盘问：
- 复用准确货号的厂家图纸/规格；或在相近官方定义副本上按明确差异定向修改；或由客户测量、AI计算生成。规则、等间距同形孔也可用官方Labware Creator；完整JSON能表达的范围比图形工具广。
- 按本次用途取得外形长宽高、行列/孔名、首孔与边缘的相对位置、孔间距或逐孔坐标、孔深/孔底高度、孔形尺寸、容量、方向和支撑方式。已有可靠资料直接复用；目测辨结构，不猜最终定位尺寸。管类说明固定它的管架及有效位置。
- AI批量生成孔坐标/ordering并核对方向、首末孔与边界；可描述不等间距、不同孔高/孔形的非标结构。固定牢靠仍需检查可达性及机身空间，多通道并行另核喷嘴与实际孔位。修改孔径/孔深/底形时联动检查体积模型，改支撑时检查有效高度。

## 有用字段速查

以下为本次核对的**schema 2**字段，AI按需查用。JSON自身必需的schemaVersion、namespace、version、loadName等保留/由AI填写；不同实物采用可区分的身份，避免覆盖另一耗材，不要求客户管理命名空间体系。

|用途|字段|关键含义|
|---|---|---|
|外形/基准|dimensions；cornerOffsetFromSlot|外形及槽位基准，单位mm；外形高不等于孔底高度。|
|孔排列|ordering；wells|孔访问顺序与逐孔数据，核对真实方向。|
|孔位置|wells.<孔>.x/y/z|相对耗材左前下基准的孔底中心；z不是孔深。|
|尺寸/容量|shape、diameter或xDimension/yDimension、depth、totalLiquidVolume|孔形、尺寸、深度；容量单位µL。|
|显示|metadata；groups|名称/分组；展示用wellBottomShape不建立内腔模型。|
|用途/枪头|allowedRoles；parameters.format/isTiprack/tipLength/tipOverlap|角色、排列及枪头属性；改标签不建立物理兼容性。|
|体积模型|geometryDefinitionId；innerLabwareGeometry|逐孔引用对应内腔模型，见下节。|
|堆叠|stackingOffsetWithLabware；stackingOffsetWithModule|父件对应的重叠量；schema 2前者正z表示向下嵌入，不是垫高。|
|抓手|gripHeightFromLabwareBottom；gripForce；gripperOffsets|夹持高度/力度；gripperOffsets通常修正放在本耗材上的子件取放位置。|
|特殊关系|isDeckSlotCompatible（parameters内）；compatibleParentLabware；stackLimit；quirks（parameters内）|直接上甲板、父子组合/堆叠及特例，需核对具体执行校验。|

schema 3另有extents、features、gripHeightFromLabwareOrigin等结构/基准，不能混套schema 2；保持原文件结构，按匹配schema和目标环境核对，不自动迁移或提升API基线。

## 体积模型与使用边界

数学液面跟随meniscus、height_from_volume及相关换算须核对实际参与孔的模型和调用范围。已知固定坐标间移动排液不因“移动”就必须建模型；初始化/账本沿用operations。

本次核对的入口：每孔geometryDefinitionId指向innerLabwareGeometry同名条目。容量、孔径/depth、平/U/V底展示标签不能替代模型；只存在一个顶层模型字段也不证明所有孔有有效引用。

模型可采用可靠内腔尺寸构建sections，或采用有依据的heightToVolumeMap。前者含conical/cuboidal/spherical/squaredcone/roundedcuboid分段；圆柱用等直径conical段，不编造cylinder枚举。后者至少两个{height, volume}点。两类按从高到低排列，检查接续/单调性、几何合理性及实际体积范围，包括混匀和F−T/F。不能由名义容量反推未知内形或虚构测量点。

缺数据时指出具体缺口，可补数据建模，或采用用户明确选择的固定位置；不静默套meniscus或猜换算。官方型号和成品同样依据实际定义/已有适用核对记录判断，不以名称代替证据。

## 堆叠、复合件与抓手

按实物说明谁承载谁、嵌入关系与能否分离，再核对加载层级和有效高度。过滤板+收集板、适配器/磁力架上的板、盖等可作为思路，不能泛化为任意组合可行。

schema 2堆叠需对应父件关系；compatibleParentLabware在盖和默认堆叠等分支有特定用途，不是所有耗材的通用严格白名单。isDeckSlotCompatible=false只限制直接上甲板；filterPlate等quirk及具体父件限制要结合实际软件/同类官方定义核对，不能只加字段就宣称“只能装在某块板上”。抓手按实物夹持区域确定高度/力度/取放位置，不提供通用安全数值。可加载、可模拟、位置检查和实际搬运分别报告。

## 交付选择

采用或创建自定义定义后，交付时提示两种方式：**独立JSON供接收者导入App＋protocol**，或**完整JSON内容内嵌protocol**；可询问是否需要内嵌版，已指定不重问。区别由模型按客户场景简述，不预设长篇话术；未选择可先交付分离文件及导入说明。

内嵌使用完整Python字典或json.loads解析脚本内字符串，调用已维护的from_definition接口；签名/接收对象查api-layout及api-module-common。读取客户电脑/技能目录的外部JSON路径不算内嵌。保留必要字段，正确处理JSON的true/false/null；自定义适配器等相关定义也按所选交付方式提供，不能因内嵌省略真实安装层级。

## 检查与来源

检查JSON及匹配schema、孔名/ordering、方向/单位/边界，以及本次用到的模型、安装、搬运和定义交付。schema通过不代表实物准确或实机验证；最终协议按protocol-review检查同一份定义。经验用于提示构建思路，硬件/API限制和缺口仍按原规则处理。

2026-10-28定向核对官方发布v10.0.0，commit `e8c6d0a424c25fff1604e2a02e4ccaedac95b9af`，不改变其他接口基线：
- [schema 2](https://github.com/Opentrons/opentrons/blob/e8c6d0a424c25fff1604e2a02e4ccaedac95b9af/shared-data/labware/schemas/2.json)及同目录3.json：字段与模型结构。
- [定义/Creator范围](https://docs.opentrons.com/flex/labware/definitions/)、[自定义定义分发](https://docs.opentrons.com/python-api/labware/#custom-labware)。
- 上述commit的api/src/opentrons/protocol_engine/state/labware.py（get_well_geometry、raise_if_labware_cannot_be_stacked）、state/geometry.py（液面/体积换算）、resources/labware_validation.py及commands/load_labware.py（堆叠/直接上甲板）。

本次用户经验：同款成品复用、厂家尺寸/实测/相近定义差异驱动AI构建、非标孔位及实际组合按需考虑、共享成品为辅。具体客户特例不自动成为默认。
