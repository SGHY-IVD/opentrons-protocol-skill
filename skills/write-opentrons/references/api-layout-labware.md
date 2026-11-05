# 耗材与适配器按名称加载

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[完整成员索引](api-layout.md)；生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

- [ProtocolContext.load_labware](#protocolcontextload_labware)
- [ProtocolContext.load_adapter](#protocolcontextload_adapter)
- [Labware.load_labware](#labwareload_labware)

## ProtocolContext.load_labware

官方来源


```python
load_labware(
    load_name: str,
    location: DeckLocation | OffDeckType | ModuleFixtureLocation,
    label: str | None = None,
    namespace: str | None = None,
    version: int | None = None,
    adapter: str | None = None,
    lid: str | None = None,
    *,
    adapter_namespace: str | None = None,
    adapter_version: int | None = None,
    lid_namespace: str | None = None,
    lid_version: int | None = None
) -> Labware
```

参数名 类型 默认值 / 必填 传参方式 load_name str 必填 位置或关键字 location DeckLocation | OffDeckType | ModuleFixtureLocation 必填 位置或关键字 label str | None None 位置或关键字 namespace str | None None 位置或关键字 version int | None None 位置或关键字 adapter str | None None 位置或关键字 lid str | None None 位置或关键字 adapter_namespace str | None None 仅关键字 adapter_version int | None None 仅关键字 lid_namespace str | None None 仅关键字 lid_version int | None None 仅关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a labware onto a location. For Opentrons-verified labware, this is a convenient way
to collapse the two stages of labware initialization (creating
the labware and adding it to the protocol) into one. This function returns the created and initialized labware for use
later in the protocol. Parameters: load_name ( str )
          – A string to use for looking up a labware definition.
You can find the load_name for any Opentrons-verified labware on the Labware Library . location ( Union[int, str, `OFF_DECK`] )
          – Either a deck slot ,
like "D1" , or the special value OFF_DECK . Changed in version 2.15: You can now specify a deck slot as a coordinate, like "D1" . label ( str | None , default: None )
          – An optional special name to give the labware. If specified,
this is how the labware will appear in the run log, Labware Position
Check, and elsewhere in the Opentrons App and on the touchscreen. namespace ( str | None , default: None )
          – The namespace that the labware definition belongs to.
If unspecified, the API will automatically search two namespaces: "opentrons" , to load standard Opentrons labware definitions. "custom_beta" , to load custom labware definitions created with the Custom Labware Creator . You might need to specify an explicit namespace if you have a custom
definition whose load_name is the same as an Opentrons-verified
definition, and you want to explicitly choose one or the other. version ( int | None , default: None )
          – The version of the labware definition. You should normally
leave this unspecified to let load_labware() choose a version automatically. adapter ( str | None , default: None )
          – The load name of an adapter to load the labware on top of. Accepts
the same values as the load_name parameter of load_adapter() . New in version 2.15. adapter_namespace ( str | None , default: None )
          – The namespace of the adapter being loaded.
Applies to adapter the same way that namespace applies to load_name . New in version 2.26: adapter_namespace may now be specified explicitly.
Also, when you've specified namespace but not adapter_namespace , adapter_namespace will now independently follow the same search rules
described in namespace . Formerly, it took namespace 's exact value. adapter_version ( int | None , default: None )
          – The version of the adapter being loaded.
Applies to adapter the same way that version applies to load_name . New in version 2.26: adapter_version may now be specified explicitly.
When unspecified, the API uses the newest version available for your protocol's API level. lid ( str | None , default: None )
          – A lid to load on the top of the main labware.
Accepts the same values as the load_name parameter of load_lid_stack() .
The lid will use the same namespace as the labware, and the API will choose
the lid's version automatically. New in version 2.23 lid_namespace ( str | None , default: None )
          – The namespace of the lid being loaded.
Applies to lid the same way that namespace applies to load_name . New in version 2.26: lid_namespace may now be specified explicitly.
Also, when you've specified namespace but not lid_namespace , lid_namespace will now independently follow the same search rules
described in namespace . Formerly, it took namespace 's exact value. lid_version ( int | None , default: None )
          – The version of the adapter being loaded.
Applies to lid the same way that version applies to load_name . New in version 2.26: lid_version may now be specified explicitly.
When unspecified, the API uses the newest version available for your protocol's API level.


## ProtocolContext.load_adapter

官方来源


```python
load_adapter(
    load_name: str,
    location: DeckLocation | OffDeckType | ModuleFixtureLocation,
    namespace: str | None = None,
    version: int | None = None,
) -> Labware
```

参数名 类型 默认值 / 必填 传参方式 load_name str 必填 位置或关键字 location DeckLocation | OffDeckType | ModuleFixtureLocation 必填 位置或关键字 namespace str | None None 位置或关键字 version int | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load an adapter onto a location. For adapters already defined by Opentrons, this is a convenient way
to collapse the two stages of adapter initialization (creating
the adapter and adding it to the protocol) into one. This function returns the created and initialized adapter for use
later in the protocol. Parameters: load_name ( str )
          – A string to use for looking up a labware definition for the adapter.
You can find the load_name for any standard adapter on the Opentrons Labware Library . location ( int | str | OffDeckType | ModuleFixtureLocation )
          – Either a deck slot , like "D1" , or the special value OFF_DECK . namespace ( str | None , default: None )
          – The namespace that the labware definition belongs to.
If unspecified, the API will automatically search two namespaces: "opentrons" , to load standard Opentrons labware definitions. "custom_beta" , to load custom labware definitions created with the Custom Labware Creator . You might need to specify an explicit namespace if you have a custom
definition whose load_name is the same as an Opentrons standard
definition, and you want to explicitly choose one or the other. version ( int | None , default: None )
          – The version of the labware definition. You should normally
leave this unspecified to let load_adapter() choose a version automatically.


## Labware.load_labware

官方来源


```python
load_labware(
    name: str,
    label: str | None = None,
    lid: str | None = None,
    namespace: str | None = None,
    version: int | None = None,
    *,
    lid_namespace: str | None = None,
    lid_version: int | None = None
) -> Labware
```

参数名 类型 默认值 / 必填 传参方式 name str 必填 位置或关键字 label str | None None 位置或关键字 lid str | None None 位置或关键字 namespace str | None None 位置或关键字 version int | None None 位置或关键字 lid_namespace str | None None 仅关键字 lid_version int | None None 仅关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a compatible labware onto the labware using its load parameters. The parameters of this function behave like those of ProtocolContext.load_labware() (which loads labware directly onto the deck). Note that the parameter name here corresponds to load_name on the ProtocolContext function. Returns: Labware – The initialized and loaded labware object.
