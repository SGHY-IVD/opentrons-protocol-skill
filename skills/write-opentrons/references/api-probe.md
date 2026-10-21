# 单次液面测量

measure_liquid_height(well: Well) -> LiquidTrackingType

well必填，可位置或关键字传参；返回相对孔底的高度mm，保留官方跟踪类型，不保证任何环境均为普通float。
只按用户指定孔和步骤测一次。用于支持压力探测的Flex配置，核对具体喷嘴布局传感器能力；使用干净干燥枪头，测量后的用户清膜操作规范见operations.md“50µL移液器探测后清膜”；该经验规范不属于API默认动作。空孔报错暂停，不当无错误的空孔测试。测量结果进入跟踪状态供meniscus使用。不默认开启liquid_presence_detection。
来源：API速查表v6，2026-10-12；https://docs.opentrons.com/python-api/reference/instruments/#opentrons.protocol_api.InstrumentContext.measure_liquid_height 及 https://docs.opentrons.com/python-api/building-block-commands/liquids/#measure-liquids 。

## 液面记录与转换

已核对官方安装包10.1.0、目标API2.28：分别保存初始化体积loaded_volume、实测高度probed_height及由实测高度换算的probed_volume，按最近一次load/probe选择有效基准；不是三套独立真值。刚探测后直接使用实测高度；吸排液时删除过时的直接高度、按操作量更新体积，后续由有效体积换算弯月面。探测后未重新load时，仍以探测基准跟踪，不因直接高度被删除而退回旧初始化体积。换算依赖可用孔几何模型及其数值精度。

同孔原位吸V再排V时，体积净变化为0；已核对版本允许账本中间负值，例如10−30+30仍为10µL，不先截零变成30µL。保留探测体积不等于持续实测，也不把孔顶aspirate自动当作AIR；其他引擎版本或异常分支须另核对。来源：官方包protocol_engine/state/{wells,geometry}.py及commands/liquid_probe.py；10µL源孔原位吸排30µL的API2.28模拟已验证。
