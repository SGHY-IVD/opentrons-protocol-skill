# 移液器、模块与模块适配器加载

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[完整成员索引](api-layout.md)；生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

- [ProtocolContext.load_instrument](#protocolcontextload_instrument)
- [ProtocolContext.load_module](#protocolcontextload_module)
- [HeaterShakerContext.load_adapter](#heatershakercontextload_adapter)
- [TemperatureModuleContext.load_adapter](#temperaturemodulecontextload_adapter)

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
will be placing the module, like "D1" . See Deck Slots . The Thermocycler is only valid in one deck location.
You don't have to specify a location when loading it, but if you do,
it must be "B1" . See Thermocycler Module . Changed in version 2.15: You can now specify a deck slot as a coordinate, like "D1" . configuration ( str | None , default: None )
          – Configure a Thermocycler to be in the semi position.
This parameter does not work. Do not use it. Removed in version 2.14: This parameter dangerously modified the protocol's geometry system,
and it didn't function properly, so it was removed. Returns: ModuleTypes – The loaded and initialized module: a AbsorbanceReaderContext , FlexStackerContext , HeaterShakerContext , MagneticBlockContext , TemperatureModuleContext ,
or ThermocyclerContext ,
depending on what you requested with module_name . Changed in version 2.13: Added HeaterShakerContext return value. Changed in version 2.15: Added MagneticBlockContext return value. Changed in version 2.21: Added AbsorbanceReaderContext return value. Changed in version 2.23: Added FlexStackerModuleContext return value.


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
