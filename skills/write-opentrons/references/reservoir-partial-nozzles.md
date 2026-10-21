# 储液槽：部分喷嘴的Y轴定位

## 触发与确认

适用Flex8通道移液器激活1–7个喷嘴，在储液槽类耗材内吸液或排液，包括单槽、4道、12道等。仅此场景按需读本页；不是默认添加偏移。生成前在聊天主动确认一次“官方默认定位”或“保持完整8通道对齐”，已明确指定不重复问。同一耗材定义/朝向、喷嘴布局和策略复用确认；任一改变重新核对。无需自动增加运行参数，用户要求时才用choice。

建议提问：“本次储液槽使用部分喷嘴，采用官方默认居中，还是保持完整8通道时的对齐位置？后者用于控制移液器整体的位置，减少部分喷嘴居中时机身向相邻板位伸出的情况。”若具体定义并不居中，把前一选项改称“官方默认定位”。说明目的不能变成保证不侵占相邻板位或无碰撞。

“保持完整8通道对齐”指：在同一孔和Z高度，机身XY与完整8通道正常定位一致；被激活喷嘴保留其在完整阵列中的对应落点，不把部分喷嘴重新移到孔中心。不能理解为把任意起始喷嘴放到A1喷嘴的落点。

未确认时可完成其他代码，但定位选择标未决，不默认插入偏移，不将含该关键未决项的流程标为通过。

## 先核对官方定位，再计算

不能仅凭“储液槽”或槽道数认定自动居中。读取当前耗材定义的parameters.quirks、ordering、实际槽尺寸与朝向：
- `centerMultichannelOnWells`且为列长槽：官方使用当前激活列的Y_CENTER；单孔槽通常使用当前激活阵列XY_CENTER。
- 横向长槽可能为X_CENTER；无居中quirk时可能按主喷嘴定位。这些情况不直接套下表。
- `offsetPipetteFor96GridSubwells`、`offsetPipetteFor12GridSubwells`还可能带来子槽格点补偿；先核对当前API/动作路径是否启用，不能叠加简表猜算。额外X补偿亦不能忽略。
- 本页不是新增load name的授权，耗材仍须已收录；自定义/旋转/规则缺失时反馈具体缺口。

## 通用推导（生成阶段使用）

以同一机身坐标系的喷嘴Y坐标表示：完整配置实际控制参考点为C8，当前配置参考点为Cn。槽中心为W，官方额外格点等位移为S8/Sn，命令额外偏移为ΔY。
完整配置机身位置：W + S8 − C8。
部分配置机身位置：W + Sn + ΔY − Cn。
使二者相等得到：**ΔY = Cn − C8 + S8 − Sn**。

标准Y居中且无额外补偿时，Cn为激活喷嘴最前与最后Y坐标的中点，C8为完整阵列中点。Y正方向向甲板后方，负方向向前方。Flex8通道喷嘴A→H沿Y负方向排列、间距9mm；以A=0，则H=−63，C8=−31.5。

SINGLE A1：Cn=0，ΔY=+31.5mm。
SINGLE H1：Cn=−63，ΔY=−31.5mm。
PARTIAL_COLUMN当前支持从H1向后连续激活N=2–7个：Cn=−63+9(N−1)/2，**ΔY=−4.5(8−N)mm**。

|激活布局|end|额外Y偏移mm|
|---|---|---:|
|SINGLE A1|不传|+31.5|
|SINGLE H1|不传|−31.5|
|H1起2个|G1|−27|
|H1起3个|F1|−22.5|
|H1起4个|E1|−18|
|H1起5个|D1|−13.5|
|H1起6个|C1|−9|
|H1起7个|B1|−4.5|
|完整8个，参照项|ALL|0|

该表只适用于已核对的标准Y居中、9mm间距、无额外Y补偿和标准朝向。若控制参考点为主喷嘴而非中心，使用通用公式重新核对C值，不套−4.5(8−N)。不由枪头取自枪头盒哪个孔推断喷嘴名称。

## 原子示例与路径衔接

示例：用户选择完整8通道对齐，H1起4喷嘴，已确认标准Y居中且无格点补偿。生成阶段得到y_shift=-18，最终协议写定值。下列volume、asp_flow、entry_speed及等待均由现有规则提供，不是本页新默认。

```python
from opentrons.types import Point

y_shift = -18.0
source_top = source.top().move(Point(x=0, y=y_shift, z=0))
source_bottom = source.bottom(z=0.8).move(Point(x=0, y=y_shift, z=0))
# 已按原规则退出上一孔；跨孔先到目标top，不用入液低速跨孔。
pipette.move_to(source_top)
# 仅待准备且空头时，在此液面外位置显式prepare_to_aspirate。
pipette.move_to(source_bottom, speed=entry_speed)
# 按等待规则插入实际需要的阶段。
pipette.aspirate(volume, source_bottom, flow_rate=asp_flow)
# 吸后等待按原规则。
pipette.move_to(source_top, speed=entry_speed)
```

偏移应用于该槽相关top、入液、吸排位置和退出位置，不能仅改move_to后又用未偏移的Well吸排使其回到默认位置。Location.move保留原well关联，官方居中仍存在，表值是叠加在其上的补偿，不是绝对喷嘴坐标。孔顶与孔内沿用相同XY可保持竖直进出。液面外准备可在该偏移top完成，不回中心再下探。偏移只作用于储液槽步骤，不传播到普通孔板、枪头盒或垃圾桶。

显式end_location时起点与终点使用同一Y偏移；Z终点仍按既有模型/用户指定。动态meniscus偏移必须先核对目标API的Location.move保留液面跟踪及XY支持，不为实现偏移静默改变用户选择的动态/固定策略。资料不足时反馈，不猜接口。

不改变吸排液速度、等待、push_out和液量规则；共享槽的液量仍按实际激活通道合计。检查槽壁空间、有效取液区域、未挂头喷嘴/机身与邻位高度、可达范围。保持机身对齐不是碰撞验证，不能据此擅改布局。

## 审查要点

检查触发时是否已在聊天确认；核对定义、起始喷嘴、数量、朝向、补偿来源；检验符号及机身位置不变量；检查同槽各相关位置一致、没有重复叠加或漏掉吸排/终点；跨孔仍经过各自top。已确认官方默认时，不把没有偏移判为错误。

## 官方依据与维护边界

核对日期2026-10-21。源码路径位于Opentrons/opentrons，具体快照见reservoir-position-sources.json（按git blob标识核对）。
- protocol_engine/state/labware.py：居中quirk及槽方向判定。
- protocol_engine/state/motion.py：get_critical_point_for_wells_in_labware与_get_pipette_offset_for_reservoirs。
- protocol_engine/state/pipettes.py：当前NozzleMap参考点选择。
- hardware_control/nozzle_manager.py：活动阵列中心与完整阵列中心的区别。
- shared-data/pipette/definitions/2/geometry/eight_channel：喷嘴几何。
- https://docs.opentrons.com/python-api/pipettes/partial-tip-pickup/ ：SINGLE A1/H1，PARTIAL_COLUMN H1起与end映射。
- https://docs.opentrons.com/python-api/robot-position/ ：Point与坐标方向。

偏移公式是由上述坐标关系推导出的用户策略实现，不称为官方推荐经验。源码核对不等于全部历史版本适用，目标版本行为不同须先核对；日常机制规则只查此维护资料，不自动联网猜补；具体耗材定义缺失时按operations“耗材几何按需查询”获取官方JSON。
