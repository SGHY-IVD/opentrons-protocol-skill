# 布局加载

条目目录（可用rg按名称定位）：
- ProtocolContext.load_trash_bin
- ProtocolContext.load_waste_chute
- ProtocolContext.load_labware
- ProtocolContext.load_instrument
- ProtocolContext.load_module
- ProtocolContext.load_adapter
- Labware.load_labware
- HeaterShakerContext.load_adapter
- TemperatureModuleContext.load_adapter

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

垃圾处理与夹爪：加载约定 默认使用 protocol.load_trash_bin(location)，location 必填，允许第1或第3列的空槽位。实际位置按operations的硬件描述/回显确认确定；未提供时保留待核对，不按实验推荐推定D3已装垃圾桶。 仅特别说明时使用 protocol.load_waste_chute()；它无参数，固定占用D3。两者是硬件加载接口，不是耗材 load name。夹爪无需独立加载。 用户经验/生成规范：协议出现 drop_tip() 时须加载垃圾桶或垃圾槽；不将此项目规范表述为API所有调用方式的绝对限制。 安装层级及明确约束另查installation.txt；不擅自重新设计用户台面。
加载移液器、模块、垃圾桶、耗材和适配器。
ProtocolContext.load_trash_bin ProtocolContext.load_waste_chute ProtocolContext.load_labware ProtocolContext.load_instrument ProtocolContext.load_module ProtocolContext.load_adapter Labware.load_labware HeaterShakerContext.load_adapter TemperatureModuleContext.load_adapter

## ProtocolContext.load_trash_bin

官方来源


```python
load_trash_bin(location: DeckLocation) -> TrashBin
```

参数名 类型 默认值 / 必填 传参方式 location DeckLocation 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a trash bin on the deck of a Flex. See Trash Bin for details. If you try to load a trash bin on an OT-2, the API will raise an error. Parameters: location ( DeckLocation )
          – The deck slot where the trash bin is. The
location can be any unoccupied slot in column 1 or 3. If you try to load a trash bin in column 2 or 4, the API will raise an error.


## ProtocolContext.load_waste_chute

官方来源


```python
load_waste_chute() -> WasteChute
```

无调用参数。

官方参数含义、返回值与使用约束（已保存在本文件） Load the waste chute on the deck of a Flex. See Waste Chute for details, including the deck configuration
variants of the waste chute. The deck plate adapter for the waste chute can only go in slot D3. If you try to
load another item in slot D3 after loading the waste chute, or vice versa, the
API will raise an error.


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
like 1 , "1" , or "D1" , or the special value OFF_DECK . Changed in version 2.15: You can now specify a deck slot as a coordinate, like "D1" . label ( str | None , default: None )
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


## ProtocolContext.load_instrument

官方来源


```python
load_instrument(
    instrument_name: str,
    mount: Mount | str | None = None,
    tip_racks: list[Labware] | None = None,
    replace: bool = False,
    liquid_presence_detection: bool | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 instrument_name str 必填 位置或关键字 mount Mount | str | None None 位置或关键字 tip_racks list[Labware] | None None 位置或关键字 replace bool False 位置或关键字 liquid_presence_detection bool | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a specific instrument for use in the protocol. When analyzing the protocol on the robot, instruments loaded with this method
are compared against the instruments attached to the robot. You won't be able to
start the protocol until the correct instruments are attached and calibrated. Currently, this method only loads pipettes. You do not need to load the Flex
Gripper to use it in protocols. See Automatic vs Manual Moves . Parameters: instrument_name ( str )
          – The instrument to load.
See API Load Names for the valid values. mount ( Mount or str or None , default: None )
          – The mount where the instrument should
be attached. This can either be an instance of Mount or one of the strings "left" or "right" . When loading a Flex 96-Channel Pipette
( instrument_name="flex_96channel_1000" ), you can leave this
unspecified, since it always occupies both mounts; if you do specify
a value, it will be ignored. tip_racks ( list [ Labware ] , default: None )
          – A list of tip
racks from which to pick tips when calling pick_up_tip() without arguments. replace ( bool , default: False )
          – If True , replace the currently loaded instrument in mount , if any. This is intended for advanced control applications. You cannot replace an instrument in the middle of a
protocol being run from the Opentrons App or touchscreen. liquid_presence_detection ( bool , default: None )
          – If True , enable automatic liquid presence detection for Flex 1-, 8-, or 96-channel pipettes. New in version 2.20.


## ProtocolContext.load_module

官方来源


```python
load_module(
    module_name: str,
    location: DeckLocation | None = None,
    configuration: str | None = None,
) -> ModuleTypes
```

参数名 类型 默认值 / 必填 传参方式 module_name str 必填 位置或关键字 location DeckLocation | None None 位置或关键字 configuration str | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load a module onto the deck, given its name or model. This is the function to call to use a module in your protocol, like load_instrument() is the method to call to use an instrument in your protocol. It returns the
created and initialized module context, which will be a different class
depending on the kind of module loaded. After loading modules, you can access a map of deck positions to loaded modules
with loaded_modules . Parameters: module_name ( str )
          – The name or model of the module.
See Available Modules for possible values. location ( DeckLocation | None , default: None )
          – The location of the module. This is usually the name or number of the slot on the deck where you
will be placing the module, like 1 , "1" , or "D1" . See Deck Slots . The Thermocycler is only valid in one deck location.
You don't have to specify a location when loading it, but if you do,
it must be 7 , "7" , or "B1" . See Thermocycler Module . Changed in version 2.15: You can now specify a deck slot as a coordinate, like "D1" . configuration ( str | None , default: None )
          – Configure a Thermocycler to be in the semi position.
This parameter does not work. Do not use it. Removed in version 2.14: This parameter dangerously modified the protocol's geometry system,
and it didn't function properly, so it was removed. Returns: ModuleTypes – The loaded and initialized module: a AbsorbanceReaderContext , FlexStackerContext , HeaterShakerContext , MagneticBlockContext , MagneticModuleContext , TemperatureModuleContext ,
or ThermocyclerContext ,
depending on what you requested with module_name . Changed in version 2.13: Added HeaterShakerContext return value. Changed in version 2.15: Added MagneticBlockContext return value. Changed in version 2.21: Added AbsorbanceReaderContext return value. Changed in version 2.23: Added FlexStackerModuleContext return value.


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
          – Either a deck slot , like 1 , "1" , or "D1" , or the special value OFF_DECK . namespace ( str | None , default: None )
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


## HeaterShakerContext.load_adapter

官方来源


```python
load_adapter(
    name: str, namespace: str | None = None, version: int | None = None
) -> Labware
```

参数名 类型 默认值 / 必填 传参方式 name str 必填 位置或关键字 namespace str | None None 位置或关键字 version int | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load an adapter onto the module using its load parameters. The parameters of this function behave like those of load_adapter() (which loads adapters directly onto the deck). Note that the parameter name here corresponds to load_name on the ProtocolContext function. Returns: Labware – The initialized and loaded adapter object.


## TemperatureModuleContext.load_adapter

官方来源


```python
load_adapter(
    name: str, namespace: str | None = None, version: int | None = None
) -> Labware
```

参数名 类型 默认值 / 必填 传参方式 name str 必填 位置或关键字 namespace str | None None 位置或关键字 version int | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Load an adapter onto the module using its load parameters. The parameters of this function behave like those of load_adapter() (which loads adapters directly onto the deck). Note that the parameter name here corresponds to load_name on the ProtocolContext function. Returns: Labware – The initialized and loaded adapter object.
