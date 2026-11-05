# 垃圾桶与垃圾槽加载

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[完整成员索引](api-layout.md)；生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

- [ProtocolContext.load_trash_bin](#protocolcontextload_trash_bin)
- [ProtocolContext.load_waste_chute](#protocolcontextload_waste_chute)

本页仅维护垃圾装置加载契约。项目的垃圾装置选择及drop_tip加载规范唯一见[垃圾处理与夹爪](installation-core.md#一垃圾处理与夹爪官方接口事实--用户生成规范)，称呼消歧与实际配置确认见[硬件确认](protocol-interaction.md#实际硬件描述核对回显确认)。目标API版本分界见[版本索引](api-versions.md#已核对的关键分界)；夹爪使用见[搬运API](api-gripper.md)，不将夹具或垃圾装置加载与夹爪独立加载混同。

## ProtocolContext.load_trash_bin

最低API 2.16。2.15仅支持固定A3垃圾桶；不要调用本方法。

官方来源


```python
load_trash_bin(location: DeckLocation) -> TrashBin
```

参数名 类型 默认值 / 必填 传参方式 location DeckLocation 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a trash bin on the deck of a Flex. See Trash Bin for details. Parameters: location ( DeckLocation )
          – The deck slot where the trash bin is. The
location can be any unoccupied slot in column 1 or 3. If you try to load a trash bin in column 2 or 4, the API will raise an error.


## ProtocolContext.load_waste_chute

最低API 2.16。2.15不支持外置垃圾槽。

官方来源


```python
load_waste_chute() -> WasteChute
```

无调用参数。

官方参数含义、返回值与使用约束（已保存在本文件） Load the waste chute on the deck of a Flex. See Waste Chute for details, including the deck configuration
variants of the waste chute. The deck plate adapter for the waste chute can only go in slot D3. If you try to
load another item in slot D3 after loading the waste chute, or vice versa, the
API will raise an error.
