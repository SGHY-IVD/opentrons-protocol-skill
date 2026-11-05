# 原子片段索引

按实际场景直达所需片段；不要求通读所有示例。示例只提供实现参考，先前已确定的权威规则与本次前提直接复用。

|场景/片段|直达|
|---|---|
|dry_run流速赋值|[参数显示与流速选择片段](patterns-parameters.md#dry_run流速赋值)|
|活塞状态跨步骤衔接|[基础移液、路径、活塞与分段排空片段](patterns-common.md#活塞状态跨步骤衔接)|
|跨孔移动分段|[基础移液、路径、活塞与分段排空片段](patterns-common.md#跨孔移动分段)|
|沿壁路径：高度与横向偏移分开|[基础移液、路径、活塞与分段排空片段](patterns-common.md#沿壁路径高度与横向偏移分开)|
|常规一吸一排|[基础移液、路径、活塞与分段排空片段](patterns-common.md#常规一吸一排)|
|磁吸后去上清单批吸液|[磁吸去上清单批吸液片段](patterns-magnetic-supernatant.md#磁吸后去上清单批吸液)|
|加液后原位立即混匀|[混匀衔接与N次手写混匀片段](patterns-mixing.md#加液后原位立即混匀)|
|需要切换模式后混匀|[混匀衔接与N次手写混匀片段](patterns-mixing.md#需要切换模式后混匀)|
|N次手写混匀，保留液与末次排净|[混匀衔接与N次手写混匀片段](patterns-mixing.md#n次手写混匀保留液与末次排净)|
|按体积确定排液终点|[基础移液、路径、活塞与分段排空片段](patterns-common.md#按体积确定排液终点)|
|分段排空：两种路径|[基础移液、路径、活塞与分段排空片段](patterns-common.md#分段排空两种路径)|
|实例路由|[混匀衔接与N次手写混匀片段](patterns-mixing.md#实例路由)|
|交付标识与参数|[参数显示与流速选择片段](patterns-parameters.md#交付标识与参数)|
|二选一参数：choice显示、布尔判断|[参数显示与流速选择片段](patterns-parameters.md#二选一参数choice显示布尔判断)|
|50µL移液器：探测后清膜|[50µL移液器探测后清膜片段](patterns-probe-film-clearing.md#50µl移液器探测后清膜)|

## 片段使用边界

片段不是完整协议，不交付未定义占位。行为依据为已命中的[核心约束](operations.md)及[场景规则](operation-scenarios.md)，混匀模式/派生体积见[混匀规则](operation-mixing.md)，具体流速、等待仍查各自权威数据；已读有效记录直接复用。参数化表达见[参数化指引](parameter-planning.md)。原子模板不封装为通用移液函数，选用片段时按本次状态和前提实例化。

分段资格和行为只见[分段排空规则](operation-dispense.md#分段排空)，实现参考直达[两种路径](patterns-common.md#分段排空两种路径)。未展开的流程骨架不是对适用规则的豁免。
