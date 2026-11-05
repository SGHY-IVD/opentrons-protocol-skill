# 执行命令 · 移液器

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

按本次动作直接读取对应成员；各成员的签名、参数、返回值、官方约束及版本说明在直达页完整维护。生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

|动作/任务|成员直达|
|---|---|
|取头、弃头与回头|[InstrumentContext.pick_up_tip](api-pipette-tips.md#instrumentcontextpick_up_tip)|
|取头、弃头与回头|[InstrumentContext.drop_tip](api-pipette-tips.md#instrumentcontextdrop_tip)|
|取头、弃头与回头|[InstrumentContext.return_tip](api-pipette-tips.md#instrumentcontextreturn_tip)|
|吸液与活塞准备|[InstrumentContext.prepare_to_aspirate](api-pipette-aspirate.md#instrumentcontextprepare_to_aspirate)|
|吸液与活塞准备|[InstrumentContext.aspirate](api-pipette-aspirate.md#instrumentcontextaspirate)|
|排液|[InstrumentContext.dispense](api-pipette-dispense.md#instrumentcontextdispense)|
|内置混匀|[InstrumentContext.mix](api-pipette-mix.md#instrumentcontextmix)|
|吹空与空气间隙|[InstrumentContext.blow_out](api-pipette-air.md#instrumentcontextblow_out)|
|吹空与空气间隙|[InstrumentContext.air_gap](api-pipette-air.md#instrumentcontextair_gap)|
|体积模式与喷嘴布局|[InstrumentContext.configure_for_volume](api-pipette-configuration.md#instrumentcontextconfigure_for_volume)|
|体积模式与喷嘴布局|[InstrumentContext.configure_nozzle_layout](api-pipette-configuration.md#instrumentcontextconfigure_nozzle_layout)|
|移动与触壁|[InstrumentContext.move_to](api-pipette-motion.md#instrumentcontextmove_to)|
|移动与触壁|[InstrumentContext.touch_tip](api-pipette-motion.md#instrumentcontexttouch_tip)|
