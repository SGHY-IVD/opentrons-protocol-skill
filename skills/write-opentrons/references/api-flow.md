# 执行命令 · 流程控制
来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

提示、暂停、延时、归位和灯光。
ProtocolContext.home ProtocolContext.comment ProtocolContext.pause ProtocolContext.delay ProtocolContext.set_rail_lights

## ProtocolContext.home

官方来源


```python
home() -> None
```

无调用参数。

官方参数含义、返回值与使用约束（已保存在本文件） Home the movement system of the robot.


## ProtocolContext.comment

官方来源


```python
comment(msg: str) -> None
```

参数名 类型 默认值 / 必填 传参方式 msg str 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Add a user-readable message to the run log. The message is visible anywhere you can view the run log, including the Opentrons App and the touchscreen on Flex. Note The value of the message is computed during protocol analysis,
so comment() can't communicate real-time information during the
actual protocol run.


## ProtocolContext.pause

官方来源


```python
pause(msg: str | None = None) -> None
```

参数名 类型 默认值 / 必填 传参方式 msg str | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Pause execution of the protocol until it's resumed. A human can resume the protocol in the Opentrons App or on the touchscreen. Note In Python Protocol API version 2.13 and earlier, the pause will only
take effect on the next function call that involves moving the robot. Parameters: msg ( str , default: None )
          – An optional message to show in the run log entry for the pause step.


## ProtocolContext.delay

官方来源


```python
delay(seconds: float = 0, minutes: float = 0, msg: str | None = None) -> None
```

参数名 类型 默认值 / 必填 传参方式 seconds float 0 位置或关键字 minutes float 0 位置或关键字 msg str | None None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Delay protocol execution for a specific amount of time. Parameters: seconds ( float , default: 0 )
          – The time to delay in seconds. minutes ( float , default: 0 )
          – The time to delay in minutes. If both seconds and minutes are specified, they will be added together.


## ProtocolContext.set_rail_lights

官方来源


```python
set_rail_lights(on: bool) -> None
```

参数名 类型 默认值 / 必填 传参方式 on bool 必填 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Controls the robot's ambient lighting (rail lights). Parameters: on ( bool )
          – If True , turn on the lights; otherwise, turn them off.
