# 50µL移液器探测后清膜片段

仅实现参考，按已命中的权威规则与本次前提使用；已读取内容直接复用。

## 50µL移液器：探测后清膜

通用规则见[50µL移液器探测后清膜](operation-probe-film-clearing.md#50µl移液器探测后清膜)，跟踪原理见api-probe“液面记录与转换”。下例只演示本次已确认实例：API2.28、Flex50µL配50µL枪头、SINGLE H1，已在液面外configure_for_volume(2)，新干燥空枪头已取好；从有机相母液取2µL、液面下1mm跟随吸液。清膜水相流速、正式取液流速及等待均已按本例配置查好；其他体积/模式/位置/液体须按规则重新确定，不把2µL和-1mm推广为默认。

```python
# protocol、pipette、source由实际协议提供，dry_run为已解析的布尔值。
aspirate_rate = 33.777778 if dry_run else 7.333333
pipette.move_to(source.top())
pipette.prepare_to_aspirate()
pipette.measure_liquid_height(source)

pipette.move_to(source.top(z=2), speed=10)
# 低体积模式清膜30µL；正式/试运行均按水相，原位吸排不传location。
pipette.aspirate(30, flow_rate=29.5)
protocol.delay(seconds=0.2)
pipette.dispense(30, flow_rate=40, push_out=0)
protocol.delay(seconds=0.2)

# 此时无需重复准备；以保留的探测体积换算液面。
pipette.move_to(source.meniscus(z=-1, target="start"), speed=10)
pipette.aspirate(2, location=source.meniscus(z=-1, target="dynamic"),
                 flow_rate=aspirate_rate)
protocol.delay(seconds=0.2)
pipette.move_to(source.top(), speed=10)
protocol.delay(seconds=0.5)
```

本例探测前已准备，之后无模式切换/非零push_out，因此清膜前及正式取液前不重复准备；其他前置状态按operations检查。模板止于离开源孔，2µL仍在枪头中，交由后续加样流程处理。原官方10.1.0/API2.28模拟记录对应修改前片段；当前清膜排速40µL/s版本仅完成参数及语法核对，本次未重新官方模拟，未实机验证。
