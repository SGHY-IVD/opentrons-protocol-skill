# 单次液面测量

measure_liquid_height(well: Well) -> LiquidTrackingType

well必填，可位置或关键字传参；返回相对孔底的高度mm，保留官方跟踪类型，不保证任何环境均为普通float。
只按用户指定孔和步骤测一次。用于支持压力探测的Flex配置，核对具体喷嘴布局传感器能力；使用干净干燥枪头，测量后的用户清膜操作规范见operations.md“50µL移液器探测后清膜”；该经验规范不属于API默认动作。空孔报错暂停，不当无错误的空孔测试。测量结果进入跟踪状态供meniscus使用。不默认开启liquid_presence_detection。
来源：API速查表v6，2026-10-12；https://docs.opentrons.com/python-api/reference/instruments/#opentrons.protocol_api.InstrumentContext.measure_liquid_height 及 https://docs.opentrons.com/python-api/building-block-commands/liquids/#measure-liquids 。
