# 实验场景与流程策略索引

本节维护用户已确认的流程策略；独立维度与组合校验仍是依据。模板只能实例化这些策略，不另行定义流速、等待、准备或push_out规则。

只定位命中的场景页；任务已直接定位到目标页时，不必再读本索引或其他场景。常规位置、液量、枪头、活塞及跨维度条件仍见[操作规则](operations.md)。

|触发|权威规则|
|---|---|
|常规移液、非零push_out排空分段、移除液体至指定去向|[排液与液体移除](operation-dispense.md)：分别读取对应小节|
|任何手写混匀|[混匀策略](operation-mixing.md)|
|明确一吸多分|[一吸多分](operation-multi-dispense.md)|
|磁分离后将当前上清全量送往废液|[磁吸后去上清](operation-magnetic-supernatant.md)|
|Flex50µL明确单次液面探测|[探测后清膜](operation-probe-film-clearing.md)|
|长孵育采用阻塞delay|[长孵育分段](operation-incubation.md)|
|明确沿壁路径或touch_tip|[特殊运动路径](operation-motion-special.md)|
