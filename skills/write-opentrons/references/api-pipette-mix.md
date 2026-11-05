# 移液器API · 内置混匀

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

[移液器成员索引](api-pipette.md)；本页维护以下完整接口契约，生成规范另按SKILL.md及[操作规则](operations.md)执行。

- [InstrumentContext.mix](#instrumentcontextmix)

## InstrumentContext.mix

官方来源


```python
mix(
    repetitions: int = 1,
    volume: float | None = None,
    location: Location | Well | None = None,
    rate: float = 1.0,
    aspirate_flow_rate: float | None = None,
    dispense_flow_rate: float | None = None,
    aspirate_delay: float | None = None,
    dispense_delay: float | None = None,
    final_push_out: float | None = None,
) -> InstrumentContext
```

参数名 类型 默认值 / 必填 传参方式 repetitions int 1 位置或关键字 volume float | None None 位置或关键字 location Location | Well | None None 位置或关键字 rate float 1.0 位置或关键字 aspirate_flow_rate float | None None 位置或关键字 dispense_flow_rate float | None None 位置或关键字 aspirate_delay float | None None 位置或关键字 dispense_delay float | None None 位置或关键字 final_push_out float | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Mix a volume of liquid by repeatedly aspirating and dispensing it in a single
location. See Mix for examples. Parameters: repetitions ( int , default: 1 )
          – Number of times to mix (default is 1). volume ( float , default: None )
          – The volume to mix, measured in µL. If unspecified,
defaults to the maximum volume for the pipette and its attached tip. If mix() is called with a volume of precisely 0, its behavior depends
on the API level of the protocol. On API levels below 2.16, it will
behave the same as a volume of None /unspecified: mix the full working
volume of the pipette. On API levels at or above 2.16, no liquid will
be mixed. location ( Location | Well | None , default: None )
          – The location where the
pipette will mix. If unspecified, the pipette will mix at its current
position. rate ( float , default: 1.0 )
          – How quickly the pipette aspirates and dispenses
liquid while mixing. The aspiration flow rate is calculated as rate multiplied by flow_rate.aspirate .
The dispensing flow rate is calculated as rate multiplied by flow_rate.dispense .
See Pipette Flow Rates . aspirate_flow_rate ( float , default: None )
          – The absolute flow rate for each
aspirate in the mix, in µL/s. If this is specified, rate must not be
set. dispense_flow_rate ( float , default: None )
          – The absolute flow rate for each
dispense in the mix, in µL/s. If this is specified, rate must not be
set. aspirate_delay ( float , default: None )
          – How long to wait after each aspirate in
the mix, in seconds. dispense_delay ( float , default: None )
          – How long to wait after each dispense in
the mix, in seconds. final_push_out ( float , default: None )
          – How much volume to push out after the
final mix repetition. The pipette will not push out after earlier
repetitions. If not specified or None , the pipette will push out the
default non-zero amount. See Push Out After Dispense . Raises: UnexpectedTipRemovalError – If no tip is attached to the pipette. Returns: InstrumentContext ( InstrumentContext )          – This instance. Note All the arguments of mix() are optional. However, if you omit one of them,
all subsequent arguments must be passed as keyword arguments. For instance, pipette.mix(1, location=wellplate['A1']) is a valid call, but pipette.mix(1, wellplate['A1']) is not. Changed in version 2.21 : Does not repeatedly check for liquid presence. New in version 2.24 : Added the aspirate_flow_rate , dispense_flow_rate , aspirate_delay , dispense_delay , and final_push_out parameters.
