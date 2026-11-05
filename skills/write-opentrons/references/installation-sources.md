# Opentrons Flex 官方安装关系来源档案

仅在核对来源、定义版本或维护更新时读取；常规判断回到[统一安装核验](installation-core.md#统一安装核验)与[实际上层关系](installation-official-upper.md)。本文件保留原来源长表，不代表各条目已随机器人软件发布。

## 八、来源与版本
https://docs.opentrons.com/python-api/deck-slots/
https://docs.opentrons.com/python-api/reference/protocols/
https://docs.opentrons.com/python-api/modules/heater-shaker/
https://docs.opentrons.com/python-api/modules/temperature-module/
https://docs.opentrons.com/python-api/modules/absorbance-plate-reader/
https://docs.opentrons.com/python-api/modules/flex-stacker/
https://docs.opentrons.com/python-api/modules/thermocycler/
https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/deck/definitions/5/ot3_standard.json
https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/schemas/2.json
既有关系的几何条目按当时官方仓库各耗材最高可见定义版本提取；本次温控上层关系改按[官方上层关系第四节](installation-official-upper.md#四适配器耗材来自上层耗材的-stackingoffsetwithlabware)注明的固定发布及API2.30默认修订核对。edge快照不等于全部条目已被当前机器人软件发布。模块位置优先采用在线API文档，并与deck的mayMountTo/providesAddressableAreas/fixtureGroup核对。
biorad_96_wellplate_200ul_pcr | definition version=5 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/biorad_96_wellplate_200ul_pcr/5.json
corning_384_wellplate_112ul_flat | definition version=5 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/corning_384_wellplate_112ul_flat/5.json
corning_96_wellplate_330ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/corning_96_wellplate_330ul/1.json
ev_resin_tips_flex_96_tiprack_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/ev_resin_tips_flex_96_tiprack_adapter/1.json
ev_resin_tips_flex_short_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/ev_resin_tips_flex_short_adapter/1.json
ev_resin_tips_flex_tall_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/ev_resin_tips_flex_tall_adapter/1.json
nest_12_reservoir_15ml | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/nest_12_reservoir_15ml/3.json
nest_1_reservoir_195ml | definition version=5 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/nest_1_reservoir_195ml/5.json
nest_96_wellplate_2ml_deep | definition version=5 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/nest_96_wellplate_2ml_deep/5.json
opentrons_12_well_aluminumblock_tough_22ml | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_12_well_aluminumblock_tough_22ml/1.json
opentrons_1_well_aluminumblock_tough_300ml | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_1_well_aluminumblock_tough_300ml/1.json
opentrons_24_aluminumblock_generic_2ml_screwcap | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_generic_2ml_screwcap/3.json
opentrons_24_aluminumblock_nest_0.5ml_screwcap | definition version=4 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_nest_0.5ml_screwcap/4.json
opentrons_24_aluminumblock_nest_1.5ml_screwcap | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_nest_1.5ml_screwcap/3.json
opentrons_24_aluminumblock_nest_1.5ml_snapcap | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_nest_1.5ml_snapcap/3.json
opentrons_24_aluminumblock_nest_2ml_screwcap | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_nest_2ml_screwcap/3.json
opentrons_24_aluminumblock_nest_2ml_snapcap | definition version=3 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_aluminumblock_nest_2ml_snapcap/3.json
opentrons_24_tuberack_nest_1.5ml_snapcap | definition version=2 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_24_tuberack_nest_1.5ml_snapcap/2.json
opentrons_40_aluminumblock_eppendorf_24x2ml_safelock_snapcap_generic_16x0.2ml_pcr_strip | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_40_aluminumblock_eppendorf_24x2ml_safelock_snapcap_generic_16x0.2ml_pcr_strip/1.json
opentrons_4_well_aluminumblock_tough_72ml | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_4_well_aluminumblock_tough_72ml/1.json
opentrons_96_aluminumblock_biorad_wellplate_200ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_aluminumblock_biorad_wellplate_200ul/1.json
opentrons_96_aluminumblock_generic_pcr_strip_200ul | definition version=4 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_aluminumblock_generic_pcr_strip_200ul/4.json
opentrons_96_aluminumblock_nest_wellplate_100ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_aluminumblock_nest_wellplate_100ul/1.json
opentrons_96_deep_well_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_deep_well_adapter/1.json
opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_deep_well_adapter_nest_wellplate_2ml_deep/1.json
opentrons_96_deep_well_temp_mod_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_deep_well_temp_mod_adapter/1.json
opentrons_96_flat_bottom_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_flat_bottom_adapter/1.json
opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_flat_bottom_adapter_nest_wellplate_200ul_flat/1.json
opentrons_96_pcr_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_pcr_adapter/1.json
opentrons_96_pcr_adapter_armadillo_wellplate_200ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_pcr_adapter_armadillo_wellplate_200ul/1.json
opentrons_96_pcr_adapter_nest_wellplate_100ul_pcr_full_skirt | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_pcr_adapter_nest_wellplate_100ul_pcr_full_skirt/1.json
opentrons_96_well_aluminum_block | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_well_aluminum_block/1.json
opentrons_96_wellplate_200ul_pcr_full_skirt | definition version=4 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_96_wellplate_200ul_pcr_full_skirt/4.json
opentrons_aluminum_flat_bottom_plate | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_aluminum_flat_bottom_plate/1.json
opentrons_calibration_adapter_heatershaker_module | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_calibration_adapter_heatershaker_module/1.json
opentrons_calibration_adapter_temperature_module | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_calibration_adapter_temperature_module/1.json
opentrons_calibration_adapter_thermocycler_module | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_calibration_adapter_thermocycler_module/1.json
opentrons_flex_96_filtertiprack_1000ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_filtertiprack_1000ul/1.json
opentrons_flex_96_filtertiprack_200ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_filtertiprack_200ul/1.json
opentrons_flex_96_filtertiprack_20ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_filtertiprack_20ul/1.json
opentrons_flex_96_filtertiprack_50ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_filtertiprack_50ul/1.json
opentrons_flex_96_tiprack_1000ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_tiprack_1000ul/1.json
opentrons_flex_96_tiprack_200ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_tiprack_200ul/1.json
opentrons_flex_96_tiprack_20ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_tiprack_20ul/1.json
opentrons_flex_96_tiprack_50ul | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_tiprack_50ul/1.json
opentrons_flex_96_tiprack_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_96_tiprack_adapter/1.json
opentrons_tough_4_reservoir_72ml | definition version=2 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_tough_4_reservoir_72ml/2.json
opentrons_tough_universal_lid | definition version=2 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_tough_universal_lid/2.json
opentrons_universal_flat_adapter | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_universal_flat_adapter/1.json
opentrons_universal_flat_adapter_corning_384_wellplate_112ul_flat | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_universal_flat_adapter_corning_384_wellplate_112ul_flat/1.json
opentrons_universal_flat_adapter_type_b | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_universal_flat_adapter_type_b/1.json
opentrons_flex_deck_riser | definition version=1 | https://raw.githubusercontent.com/Opentrons/opentrons/edge/shared-data/labware/definitions/2/opentrons_flex_deck_riser/1.json
