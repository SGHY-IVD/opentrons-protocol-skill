# 运行参数与 CSV

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

一般运行参数自API 2.18起；CSV文件参数自2.20起，旧目标不能仅因支持一般参数就使用CSV。版本选择见[版本索引](api-versions.md#已核对的关键分界)。

按调用职责选择下列成员或章节；各项签名、参数、返回值、官方约束和版本说明在直达页完整维护。

|职责|成员/章节直达|
|---|---|
|运行参数声明与输入约束|[参数类型与输入方式](api-parameters-definition.md#参数类型与输入方式)|
|运行参数声明与输入约束|[ParameterContext.add_int](api-parameters-definition.md#parametercontextadd_int)|
|运行参数声明与输入约束|[ParameterContext.add_float](api-parameters-definition.md#parametercontextadd_float)|
|运行参数声明与输入约束|[ParameterContext.add_bool](api-parameters-definition.md#parametercontextadd_bool)|
|运行参数声明与输入约束|[ParameterContext.add_str](api-parameters-definition.md#parametercontextadd_str)|
|运行参数声明与输入约束|[ParameterContext.add_csv_file](api-parameters-definition.md#parametercontextadd_csv_file)|
|运行参数读取与CSV访问|[ProtocolContext.params](api-parameters-csv-access.md#protocolcontextparams)|
|运行参数读取与CSV访问|[CSV：从导入到切片](api-parameters-csv-access.md#csv从导入到切片)|
|运行参数读取与CSV访问|[CSV 的其他访问方式](api-parameters-csv-access.md#csv-的其他访问方式)|
|运行参数读取与CSV访问|[parse_as_csv 的格式参数](api-parameters-csv-access.md#parse_as_csv-的格式参数)|
|运行参数读取与CSV访问|[CSVParameter.parse_as_csv](api-parameters-csv-access.md#csvparameterparse_as_csv)|
|运行参数读取与CSV访问|[CSVParameter.contents](api-parameters-csv-access.md#csvparametercontents)|
|运行参数读取与CSV访问|[CSVParameter.file](api-parameters-csv-access.md#csvparameterfile)|
|运行参数读取与CSV访问|[CSVParameter.file_opened](api-parameters-csv-access.md#csvparameterfile_opened)|
