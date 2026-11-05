# 移液器API · 体积模式与喷嘴布局

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.configure_for_volume](#instrumentcontextconfigure_for_volume)
- [InstrumentContext.configure_nozzle_layout](#instrumentcontextconfigure_nozzle_layout)

## InstrumentContext.configure_for_volume

官方来源


```python
configure_for_volume(volume: float) -> None
```

参数名 类型 默认值 / 必填 传参方式 volume float 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Configure a pipette to handle a specific volume of liquid, measured in µL.
The pipette enters a volume mode depending on the volume provided. Changing
pipette modes alters properties of the instance of InstrumentContext , such as
default flow rate, minimum volume, and maximum volume. The pipette remains in
the mode set by this function until it is called again. The Flex 1-Channel 50 µL and Flex 8-Channel 50 µL pipettes must operate in a
low-volume mode to accurately dispense very small volumes of liquid. Low-volume
mode can only be set by calling configure_for_volume() . See Volume Modes . Note Changing a pipette's mode will reset its flow rates . This function will raise an error if called when the pipette's tip contains
liquid. It won't raise an error if a tip is not attached, but changing modes may
affect which tips the pipette can subsequently pick up without raising an error. This function will also raise an error if volume is outside of the minimum and maximum capacities of the pipette (e.g.,
setting volume=1 for a Flex 1000 µL pipette). Parameters: volume ( float )
          – The volume, in µL, that the pipette will prepare to handle.


## InstrumentContext.configure_nozzle_layout

官方来源


```python
configure_nozzle_layout(
    style: NozzleLayout,
    start: str | None = None,
    end: str | None = None,
    front_right: str | None = None,
    back_left: str | None = None,
    tip_racks: list[Labware] | None = None,
) -> None
```

参数名 类型 默认值 / 必填 传参方式 style NozzleLayout 必填 位置或关键字 start str | None None 位置或关键字 end str | None None 位置或关键字 front_right str | None None 位置或关键字 back_left str | None None 位置或关键字 tip_racks list[Labware] | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Configure how many tips the 8-channel or 96-channel pipette will pick up. Changing the nozzle layout will affect gantry movement for all subsequent
pipetting actions that the pipette performs. It also alters the pipette's
behavior for picking up tips. The pipette will continue to use the specified
layout until this function is called again. Note When picking up fewer than 96 tips at once, the tip rack must not be
placed in a tip rack adapter in the deck. If you try to pick up fewer than 96
tips from a tip rack that is in an adapter, the API will raise an error. Parameters: style ( NozzleLayout or None )
          – The shape of the nozzle layout.
You must import the layout constant in order to use it. ALL resets the pipette to use all of its nozzles. Calling configure_nozzle_layout() with no arguments also resets the pipette. COLUMN sets a 96-channel pipette to use 8 nozzles, aligned from front to back
with respect to the deck. This corresponds to a column of wells on labware.
For 8-channel pipettes, use ALL instead. PARTIAL_COLUMN sets an 8-channel pipette to use 2–7 nozzles, aligned from front to back
with respect to the deck. Not compatible with the 96-channel pipette. ROW sets a 96-channel pipette to use 12 nozzles, aligned from left to right
with respect to the deck. This corresponds to a row of wells on labware.
Not compatible with 8-channel pipettes. SINGLE sets the pipette to use 1 nozzle. This corresponds to a single well on labware. start ( str or None , default: None )
          – The primary nozzle of the layout, which the robot uses
to determine how it will move to different locations on the deck. The string
should be of the same format used when identifying wells by name.
Required unless setting style=ALL . Note If possible, don't use both start="A1" and start="A12" to pick up
tips from the same rack . Doing so can affect positional accuracy. end ( str or None , default: None )
          – The nozzle at the end of a linear layout, which is used
to determine how many tips will be picked up by a pipette. The string
should be of the same format used when identifying wells by name.
Required when setting style=PARTIAL_COLUMN . tip_racks ( list [ Labware ] , default: None )
          – Behaves the same as setting the tip_racks parameter of load_instrument() . If not specified,
the new configuration resets tip_racks and you must specify the location every time you call pick_up_tip() . Changed in version 2.20 : Added partial column, row, and single layouts.
