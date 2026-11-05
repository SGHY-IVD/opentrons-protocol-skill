# 自定义定义加载

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[完整成员索引](api-layout.md)；生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

- [自定义定义加载：已核对的接口](#自定义定义加载已核对的接口)
- [ProtocolContext.load_labware_from_definition](#protocolcontextload_labware_from_definition)
- [ProtocolContext.load_adapter_from_definition](#protocolcontextload_adapter_from_definition)
- [Labware.load_labware_from_definition](#labwareload_labware_from_definition)

## 自定义定义加载：已核对的接口

本节定向核对官方发布v10.0.0，commit `e8c6d0a424c25fff1604e2a02e4ccaedac95b9af`的`api/src/opentrons/protocol_api/protocol_context.py`和`labware.py`，2026-10-28；未改变文档API基线2.30。创建及交付策略见custom-labware.md。

### ProtocolContext.load_labware_from_definition

```python
load_labware_from_definition(labware_def: LabwareDefinition, location: DeckLocation | OffDeckType, label: str | None = None) -> Labware
```

最低API 2.0；labware_def与location必填，label可选。把完整定义加入本协议并在指定甲板槽/非甲板位置加载；此location不接收任意模块或父耗材对象。Flex槽位写法等限制仍按目标版本核对。

### ProtocolContext.load_adapter_from_definition

```python
load_adapter_from_definition(adapter_def: LabwareDefinition, location: DeckLocation | OffDeckType) -> Labware
```

最低API 2.15；两个参数必填。在甲板槽/非甲板位置加载定义中的适配器，返回Labware；没有label参数。

### Labware.load_labware_from_definition

```python
load_labware_from_definition(definition: LabwareDefinition, label: str | None = None) -> Labware
```

最低API 2.15；在本Labware代表的兼容父件上加载子耗材，definition必填，label可选；不再传甲板location。适用关系与占位仍核对，不推导任意层叠可用。模块上的同名方法/适配器加载已维护在api-module-common.md，使用模块接收对象及其签名。
