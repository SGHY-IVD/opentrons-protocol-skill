# 磁吸去上清单批吸液片段

仅实现参考，按已命中的权威规则与本次前提使用；已读取内容直接复用。

## 磁吸后去上清单批吸液

场景、分批公式与默认参数唯一见[去上清场景](operation-magnetic-supernatant.md#磁吸后去上清)。本片段只处理已经预检的一批(body_volume, tail_volume)，两者为每通道量；空头、配置/路径/液量已核对。高度、局部速度与稳定等待按场景及本次覆盖赋值，入退速度和其余等待按原规则取值；body_flow/tail_flow已按正式或dry_run分支解析。变量需在实际协议中赋值，不能原样交付。prepare_needed来自原有待准备状态，不因批次变化机械置真。

```python
if body_volume + tail_volume > 0:
    pipette.move_to(source.top())
    if prepare_needed:
        pipette.prepare_to_aspirate()
    pipette.move_to(source.bottom(z=body_height), speed=source_entry_speed)

    if body_volume > 0:
        if before_aspirate_delay > 0:
            protocol.delay(seconds=before_aspirate_delay)
        pipette.aspirate(body_volume, source.bottom(z=body_height),
                         flow_rate=body_flow)
        if after_aspirate_delay > 0:
            protocol.delay(seconds=after_aspirate_delay)

    if tail_volume > 0:
        pipette.move_to(source.bottom(z=tail_height), speed=low_move_speed)
        low_wait = max(before_aspirate_delay if body_volume == 0 else 0,
                       low_settle_delay)
        if low_wait > 0:
            protocol.delay(seconds=low_wait)
        pipette.aspirate(tail_volume, source.bottom(z=tail_height),
                         flow_rate=tail_flow)
        if after_aspirate_delay > 0:
            protocol.delay(seconds=after_aspirate_delay)
        pipette.move_to(source.bottom(z=body_height), speed=low_move_speed)

    pipette.move_to(source.top(), speed=source_exit_speed)
    if after_aspirate_retract_delay > 0:
        protocol.delay(seconds=after_aspirate_retract_delay)
```

终态为本批液体仍在枪头内；外层必须按已确认废液流程实际排出，再开始下一批。本片段不包含磁吸计时、排液、弃头或批间循环，不把省略部分视为已执行；不因本场景而调用分段排空的排液参数。
