# Opentrons Flex 官方上层承载关系

安装核验、夹具匹配与占位更新先应用[统一安装核验](installation-core.md#统一安装核验)，本文件只维护上层关系与其证据边界。

按实际模块、父适配器或上层 `load_name` 检索，再读取命中关系所在完整小节及其来源/边界；不必通读所有对象。来源追溯再查[完整来源与定义版本](installation-sources.md)，不用在常规加载时展开长表。

|要核对的关系|本文件定位|
|---|---|
|热震荡、温控模块上的独立适配器；台面适配器|三、模块→独立适配器|
|父适配器与孔板/枪头盒；温控隐藏存量关系|四、适配器→耗材|
|温控24孔铝块+管组合；热循环、磁力架直接承载；读板机选板|五、模块→耗材直接叠放|
|板盖、同类堆叠、兼容父层与数量上限|六、板盖、同类堆叠及其他父层关系|
|缺关系、未确认名称与更新范围|七、未收录/未确认|

## 三、模块→独立适配器（官方文档明确支持）
heaterShakerModuleV1 -> opentrons_universal_flat_adapter
heaterShakerModuleV1 -> opentrons_universal_flat_adapter_type_b
heaterShakerModuleV1 -> opentrons_96_pcr_adapter
heaterShakerModuleV1 -> opentrons_96_deep_well_adapter
heaterShakerModuleV1 -> opentrons_96_flat_bottom_adapter
temperatureModuleV2 -> opentrons_aluminum_flat_bottom_plate
temperatureModuleV2 -> opentrons_96_well_aluminum_block
temperatureModuleV2 -> opentrons_96_deep_well_temp_mod_adapter
台面直接加载：opentrons_flex_96_tiprack_adapter、opentrons_flex_deck_riser。
热震荡模块需搬入搬出孔板时，使用独立适配器与独立孔板定义；不要使用一体组合定义代替。
以上是已收录关系，不把模块文档未列出的适配器自动判为禁止。

## 四、适配器→耗材（来自上层耗材的 stackingOffsetWithLabware）
下面每条包含上层耗材定义版本和官方坐标重叠量；这些数值不是需要用户另加的校准偏移。
opentrons_96_well_aluminum_block -> biorad_96_wellplate_200ul_pcr | 子定义v5 | overlap={"x": 0, "y": 0, "z": 15.41}
opentrons_96_pcr_adapter -> biorad_96_wellplate_200ul_pcr | 子定义v5 | overlap={"x": 0, "y": 0, "z": 10.16}
opentrons_universal_flat_adapter -> corning_384_wellplate_112ul_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 8.32}
opentrons_aluminum_flat_bottom_plate -> corning_384_wellplate_112ul_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 4.4}
opentrons_96_deep_well_adapter -> nest_96_wellplate_2ml_deep | 子定义v5 | overlap={"x": 0, "y": 0, "z": 16.3}
opentrons_96_deep_well_temp_mod_adapter -> nest_96_wellplate_2ml_deep | 子定义v5 | overlap={"x": 0, "y": 0, "z": 16.1}
opentrons_96_pcr_adapter -> opentrons_96_wellplate_200ul_pcr_full_skirt | 子定义v4 | overlap={"x": 0, "y": 0, "z": 10.95}
opentrons_96_well_aluminum_block -> opentrons_96_wellplate_200ul_pcr_full_skirt | 子定义v4 | overlap={"x": 0, "y": 0, "z": 11.91}
opentrons_aluminum_flat_bottom_plate -> corning_6_wellplate_16.8ml_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 4.5}
opentrons_aluminum_flat_bottom_plate -> corning_12_wellplate_6.9ml_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 4.5}
opentrons_aluminum_flat_bottom_plate -> corning_24_wellplate_3.4ml_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 4.15}
opentrons_aluminum_flat_bottom_plate -> corning_48_wellplate_1.6ml_flat | 子定义v6 | overlap={"x": 0, "y": 0, "z": 4.4}
opentrons_aluminum_flat_bottom_plate -> corning_96_wellplate_360ul_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 5.45}
opentrons_aluminum_flat_bottom_plate -> nest_96_wellplate_200ul_flat | 子定义v5 | overlap={"x": 0, "y": 0, "z": 5.55}
opentrons_96_well_aluminum_block -> nest_96_wellplate_100ul_pcr_full_skirt | 子定义v5 | overlap={"x": 0, "y": 0, "z": 12.66}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_filtertiprack_1000ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_filtertiprack_200ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_filtertiprack_20ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_filtertiprack_50ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_tiprack_1000ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_tiprack_200ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_tiprack_20ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_flex_96_tiprack_adapter -> opentrons_flex_96_tiprack_50ul | 子定义v1 | overlap={"x": 0, "y": 0, "z": 121}
opentrons_4_well_aluminumblock_tough_72ml -> opentrons_tough_4_reservoir_72ml | 子定义v2 | overlap={"x": 0, "y": 0, "z": 23.75}
opentrons_flex_deck_riser -> opentrons_tough_universal_lid | 子定义v2 | overlap={"x": 0, "y": 0, "z": 34}

温控隐藏存量关系（按catalog隐藏项调查规则查用，不混入普通推荐候选；隐藏不等于Python不兼容）：
opentrons_96_well_aluminum_block -> armadillo_96_wellplate_200ul_pcr_full_skirt | 子定义v3 | overlap={"x": 0, "y": 0, "z": 11.91} | hidden_from_ui

温控上层关系来源与边界（2026-11-04核对）：官方v10.0.0 commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af，完整definitions树878767d05ffaff87c79da80d29990297332e4e69。扫描该树全部293份schema2/3版本定义，47个历史文件命中三个温控父适配器；按同提交API2.30默认策略收敛为11条公开关系及1条隐藏存量关系，排除测试条目。12份正式上层默认定义均定向重取并核对blob；本次新增公开7条、隐藏1条，原4条保持。模块→三个适配器仍依据第五节所引温控模块文档；上层关系来自各子定义的stackingOffsetWithLabware，不作为任意热性能、多通道可达或抓手搬运已验证的证明。
默认策略：api/src/opentrons/protocol_api/core/engine/_default_labware_versions.py，blob ca39a9f89176bdd85824ec398f35e834cad75a53；隐藏策略：shared-data/js/getLabware.ts，blob 2cb268bf4e31aac8014b05443e9febf77ae21f71。后者将Armadillo隐藏并注明由opentrons_96_wellplate_200ul_pcr_full_skirt替代，不因此替用户更换实物。
新增子定义路径统一为shared-data/labware/definitions/2/<上层load_name>/<上述v>.json，固定提交中的blob如下；其他目标API仍核对实际默认修订：
corning_6_wellplate_16.8ml_flat | blob b048d951efd68c5e7588d6e8b22b9e63b894a800
corning_12_wellplate_6.9ml_flat | blob 915fa2e29c6200c488aa1486866705030f2efd9c
corning_24_wellplate_3.4ml_flat | blob fda8ec1616990e49351f18bb81a73fce139f57c4
corning_48_wellplate_1.6ml_flat | blob 1cdacbb0ce0bc79e3ee3c55ae1f2dbfe6753c709
corning_96_wellplate_360ul_flat | blob d322da9c33853bd6b736c9388c12be13022ef626
nest_96_wellplate_200ul_flat | blob 16289560820cb6507a6f8aa761b7fdab58bc9cff
nest_96_wellplate_100ul_pcr_full_skirt | blob c26b422af66b381c7512c4687ae10fd458c644bd
armadillo_96_wellplate_200ul_pcr_full_skirt | blob faaed462f588923da582643d60a4bbb9c816971e

## 五、模块→耗材直接叠放

温控24孔铝块+管组合（依据官方模块文档，不是从几何偏移推定）：
temperatureModuleV2 -> opentrons_24_aluminumblock_generic_2ml_screwcap
temperatureModuleV2 -> opentrons_24_aluminumblock_nest_0.5ml_screwcap
temperatureModuleV2 -> opentrons_24_aluminumblock_nest_1.5ml_screwcap
temperatureModuleV2 -> opentrons_24_aluminumblock_nest_1.5ml_snapcap
temperatureModuleV2 -> opentrons_24_aluminumblock_nest_2ml_screwcap
temperatureModuleV2 -> opentrons_24_aluminumblock_nest_2ml_snapcap
代码用temp_mod.load_labware(<组合名>)；组合定义已包含铝块与管的几何，不再加载独立铝块或叠一层管。不能因API≥2.15通常推荐适配器分体加载，就强拆这组没有独立铝块定义的组合；96孔铝块已有独立适配器时按对应分体层级加载。名称与实物匹配只证明相应组合；搬运、液面模型和多通道可达性仍查实际定义及当前用途，不推定整套可由抓手搬运。
来源：官方v10.0.0 commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af，docs/python-api/docs/modules/temperature-module.md（blob a22e93904c6b1fae185421950f1bd11e7c3d7187），2026-10-28核对“Block-and-tube combinations”与“Standalone adapters”；当前官方页面交叉核对 https://docs.opentrons.com/python-api/modules/temperature-module/ 。没有新增定义或API。另核对同提交API2.30默认修订：generic 2mL及NEST 1.5/2mL四项为v3，NEST 0.5mL为v4；6项均为24孔、无独立adapter角色，parameters.quirks含gripperIncompatible。路径/blob已在labware-index.json，不重复抄几何；其他目标API仍按实际选中定义检查。

以下来自 stackingOffsetWithModule，仅表示该定义显式记录的关系：
thermocyclerModuleV2 -> biorad_96_wellplate_200ul_pcr | 子定义v5 | overlap={"x": 0, "y": 0, "z": 10.75}
magneticBlockV1 -> biorad_96_wellplate_200ul_pcr | 子定义v5 | overlap={"x": 0, "y": 0, "z": 3.87}
magneticBlockV1 -> nest_96_wellplate_2ml_deep | 子定义v5 | overlap={"x": 0, "y": 0, "z": 2.66}
magneticBlockV1 -> opentrons_96_wellplate_200ul_pcr_full_skirt | 子定义v4 | overlap={"x": 0, "y": 0, "z": 3.54}
thermocyclerModuleV2 -> opentrons_96_wellplate_200ul_pcr_full_skirt | 子定义v4 | overlap={"x": 0, "y": 0, "z": 10.7}
thermocyclerModuleV2 -> opentrons_calibration_adapter_thermocycler_module | 子定义v1 | overlap={"x": 0, "y": 0, "z": 11.0}

读板机上层板（用户推荐及官方板型范围核对，不是逐品牌光学认证）：
absorbanceReaderV1 -> corning_96_wellplate_360ul_flat | 推荐候选；API2.30默认定义v5
absorbanceReaderV1 -> nest_96_wellplate_200ul_flat | 推荐候选；API2.30默认定义v5
官方产品说明支持ANSI/SBS标准96孔平底板；固定v10.0.0引擎的板型检查要求恰为96孔、定义总高≤16mm。两款上述默认定义分别为14.22/14.3mm高，并包含抓取参数；按实际货号确认孔底透光、测定适用性与抓手结构，不把几何门槛通过等同于实测光学兼容。其他品牌可按相同条件和实际定义核对，推荐名单不是品牌白名单。
两份板定义没有stackingOffsetWithModule字段，不补造偏移；按官方读板流程用模块对象直接承载孔板，不新增适配器。corning_96_wellplate_330ul仍为另一加载名，不自动替换为上述360ul_flat。
来源：用户2026-11-04确认的选板经验；官方[产品规格及FAQ](https://opentrons.com/products/opentrons-flex-absorbance-plate-reader-module-gen1)于同日核对，在线页未固定修订；定义与软件校验依据官方v10.0.0 commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af：
- shared-data/labware/definitions/2/corning_96_wellplate_360ul_flat/5.json，blob d322da9c33853bd6b736c9388c12be13022ef626。
- shared-data/labware/definitions/2/nest_96_wellplate_200ul_flat/5.json，blob 16289560820cb6507a6f8aa761b7fdab58bc9cff。
- api/src/opentrons/protocol_engine/state/labware.py，blob dedeee6786ddde009280527ccdc6c969bf633d16，raise_if_labware_incompatible_with_plate_reader及_PLATE_READER_MAX_LABWARE_Z_MM。

## 六、板盖、同类堆叠及其他父层关系（保持原始字段语义）
biorad_96_wellplate_200ul_pcr -> biorad_96_wellplate_200ul_pcr | stackingOffsetWithLabware | 子定义v5 | overlap={"x": 0, "y": 0, "z": 3.32}
nest_96_wellplate_2ml_deep -> nest_96_wellplate_2ml_deep | stackingOffsetWithLabware | 子定义v5 | overlap={"x": 0, "y": 0, "z": 2.75}
opentrons_96_wellplate_200ul_pcr_full_skirt -> opentrons_96_wellplate_200ul_pcr_full_skirt | stackingOffsetWithLabware | 子定义v4 | overlap={"x": 0, "y": 0, "z": 3.68}
opentrons_flex_tiprack_lid -> opentrons_flex_96_filtertiprack_1000ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_filtertiprack_200ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_filtertiprack_20ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_filtertiprack_50ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_tiprack_1000ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_tiprack_200ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_tiprack_20ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
opentrons_flex_tiprack_lid -> opentrons_flex_96_tiprack_50ul | stackingOffsetWithLabware | 子定义v1 | overlap={"x": 0, "y": 0, "z": 0.25}
default -> opentrons_tough_universal_lid | stackingOffsetWithLabware | 子定义v2 | overlap={"x": 0, "y": 0, "z": 7.1} | 特殊键，不是普通耗材load name
opentrons_96_wellplate_200ul_pcr_full_skirt -> opentrons_tough_universal_lid | stackingOffsetWithLabware | 子定义v2 | overlap={"x": 0, "y": 0, "z": 6.1}
protocol_engine_lid_stack_object -> opentrons_tough_universal_lid | stackingOffsetWithLabware | 子定义v2 | overlap={"x": 0, "y": 0, "z": 0} | 特殊键，不是普通耗材load name
opentrons_tough_universal_lid -> opentrons_tough_universal_lid | stackingOffsetWithLabware | 子定义v2 | overlap={"x": 0, "y": 0, "z": 1}
opentrons_96_wellplate_200ul_pcr_full_skirt | compatibleParentLabware=["opentrons_96_wellplate_200ul_pcr_full_skirt"]
opentrons_96_wellplate_200ul_pcr_full_skirt | stackLimit=4
opentrons_tough_universal_lid | stackLimit=5
default 是默认几何条目，不作为“所有耗材兼容”的证明。外部父项若尚未收录其定义，不能据一条几何记录自动补全其全部能力。
字段解释：stackingOffsetWithLabware 的键为下层对象；记录位于上层耗材定义中。stackingOffsetWithModule 同理。compatibleParentLabware 需按其字段语义保留，不能与几何偏移简单互换。

## 七、未收录/未确认
仅维护Flex安装约束；不得用未收录旧代模块替代已确认型号。24孔温控组合依据见第五节，三个温控独立适配器的上层扩充见第四节；其他关系未随本次批量更新。
没有显式关系的组合均保持未确认；例如 corning_96_wellplate_330ul 未提取到适配器叠放记录，不因此判定不可安装。本次明确的corning_96_wellplate_360ul_flat是另一加载名，不据相同品牌/孔数替换330ul定义。
EV Resin适配器、部分Tough储液槽铝块的模块安装关系尚未由本轮模块文档确认；保持名称已收录、对应安装关系未确认。
尚未覆盖官方耗材库全部耗材；本库只涵盖当前名称清单的关系与直接引用。
