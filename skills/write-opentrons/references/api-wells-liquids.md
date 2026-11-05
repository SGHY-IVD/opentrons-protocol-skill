# 公共查询 · 孔位、位置与液体

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

按成员职责直接读取完整接口契约；各成员的签名、参数、返回值、官方约束与版本说明在直达页维护。生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

|职责|成员直达|
|---|---|
|液体定义与初始化|[ProtocolContext.define_liquid](api-wells-liquids-initialization.md#protocolcontextdefine_liquid)|
|液体定义与初始化|[Labware.load_liquid](api-wells-liquids-initialization.md#labwareload_liquid)|
|液体定义与初始化|[Labware.load_liquid_by_well](api-wells-liquids-initialization.md#labwareload_liquid_by_well)|
|液体定义与初始化|[Labware.load_empty](api-wells-liquids-initialization.md#labwareload_empty)|
|液体定义与初始化|[Well.load_liquid](api-wells-liquids-initialization.md#wellload_liquid)|
|位置、液面与体积高度|[Well.top](api-wells-liquids-position.md#welltop)|
|位置、液面与体积高度|[Well.bottom](api-wells-liquids-position.md#wellbottom)|
|位置、液面与体积高度|[Well.meniscus](api-wells-liquids-position.md#wellmeniscus)|
|位置、液面与体积高度|[Well.height_from_volume](api-wells-liquids-position.md#wellheight_from_volume)|
|位置、液面与体积高度|[Location.move](api-wells-liquids-position.md#locationmove)|
|孔位访问与对象关系|[Labware.wells](api-wells-liquids-access.md#labwarewells)|
|孔位访问与对象关系|[Labware.wells_by_name](api-wells-liquids-access.md#labwarewells_by_name)|
|孔位访问与对象关系|[Labware.rows](api-wells-liquids-access.md#labwarerows)|
|孔位访问与对象关系|[Labware.columns](api-wells-liquids-access.md#labwarecolumns)|
|孔位访问与对象关系|[Labware.parent](api-wells-liquids-access.md#labwareparent)|
|孔位访问与对象关系|[Labware.child](api-wells-liquids-access.md#labwarechild)|
|孔位访问与对象关系|[Well.parent](api-wells-liquids-access.md#wellparent)|
