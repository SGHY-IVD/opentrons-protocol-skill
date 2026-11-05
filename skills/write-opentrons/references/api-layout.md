# 布局加载

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

按调用职责选择下列成员或章节；各项签名、参数、返回值、官方约束和版本说明在直达页完整维护。

|职责|成员/章节直达|
|---|---|
|耗材与适配器按名称加载|[ProtocolContext.load_labware](api-layout-labware.md#protocolcontextload_labware)|
|耗材与适配器按名称加载|[ProtocolContext.load_adapter](api-layout-labware.md#protocolcontextload_adapter)|
|耗材与适配器按名称加载|[Labware.load_labware](api-layout-labware.md#labwareload_labware)|
|移液器、模块与模块适配器加载|[ProtocolContext.load_instrument](api-layout-hardware.md#protocolcontextload_instrument)|
|移液器、模块与模块适配器加载|[ProtocolContext.load_module](api-layout-hardware.md#protocolcontextload_module)|
|移液器、模块与模块适配器加载|[HeaterShakerContext.load_adapter](api-layout-hardware.md#heatershakercontextload_adapter)|
|移液器、模块与模块适配器加载|[TemperatureModuleContext.load_adapter](api-layout-hardware.md#temperaturemodulecontextload_adapter)|
|垃圾桶与垃圾槽加载|[ProtocolContext.load_trash_bin](api-layout-trash.md#protocolcontextload_trash_bin)|
|垃圾桶与垃圾槽加载|[ProtocolContext.load_waste_chute](api-layout-trash.md#protocolcontextload_waste_chute)|
|自定义定义加载|[自定义定义加载：已核对的接口](api-layout-definitions.md#自定义定义加载已核对的接口)|
|自定义定义加载|[ProtocolContext.load_labware_from_definition](api-layout-definitions.md#protocolcontextload_labware_from_definition)|
|自定义定义加载|[ProtocolContext.load_adapter_from_definition](api-layout-definitions.md#protocolcontextload_adapter_from_definition)|
|自定义定义加载|[Labware.load_labware_from_definition](api-layout-definitions.md#labwareload_labware_from_definition)|
