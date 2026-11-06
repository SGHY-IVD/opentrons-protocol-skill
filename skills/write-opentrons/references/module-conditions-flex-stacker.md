# Flex Stacker

[模块索引](api-modules.md) · [API与加载](api-module-flex-stacker.md) · [本设备经验](module-practices-flex-stacker.md)；静态安装及已收录适配关系唯一查[安装关系](installation.txt)，[来源与覆盖边界](module-conditions-common.md#来源与边界)按需查证。

### 硬件与机制

Flex Stacker由仓体（hopper）和穿梭托盘（shuttle）组成。仓体装在Flex机身右侧外部，耗材在仓内垂直堆叠。穿梭托盘负责在仓体与抓手之间交接，归位时对齐模块在第4列的加载位置（A4、B4、C4或D4）。retrieve()把仓内最底层一件送到托盘，store()把托盘上的匹配耗材送入仓内底部。

操作员可经装料门预装耗材。set_stored_labware()和set_stored_labware_items()登记初始库存，实物装载由操作员确认。库存列表首项为下一次取出对象。

### 易混淆点

- **托盘与同排工作位。** 托盘是第4列的模块承载位，通过模块对象表达托盘上耗材的加载与搬运位置。用户说“A4装Stacker，A4放枪头盒”时，按枪头盒放在该模块托盘上核对。标准Stacker夹具保留同排第3列的独立普通工作位，两处分别记录占用，具体台面配置按安装关系核对。
- **托盘临时承载与仓内库存。** 暂不执行仓内存取时，可在托盘上单独放一件兼容耗材，类型可与仓内不同。仓内每次配置一种主耗材及相应盖/适配器组合。托盘可承载的耗材能否存入仓内，按当前仓内组合核对。用户明确说“仓内”时按库存核对，仓内库存和托盘当前耗材分别记录。

### 条件约束

- 本节仓内存取/库存专属接口最低API2.25；模块加载及继承的共享成员按各自契约核对，不将2.25概括成全部加载能力的统一下限。库存声明的型号、数量、盖/适配器组合必须与实物一致。实际同质性按定义身份及完整组合核对，不能只凭“都是枪头盒/孔板”视为同类。
- 配置仓内库存前移走原先当普通承载位加载在托盘上的耗材，按官方指南组织顺序；重新配置类型前，仓内须已知为空，不能用重新声明掩盖原有库存。未配置库存不妨碍按共享API使用适用的托盘承载能力，但不能retrieve/store。
- retrieve前须已配置、有至少一件仓内库存且托盘为空；取出后仓内减一、托盘被占用。retrieve返回主耗材；若带适配器，用返回对象的parent识别适配器。只搬走主耗材、底层适配器仍在托盘时，托盘仍被占用；仅在所有占用对象均搬离后才记为空。即使托盘上的耗材与库存同型，也不能在仍占用时继续取出。
- store前须已配置、有剩余仓内容量，且托盘上的主耗材、盖/适配器整套组合与声明一致；缺盖、缺适配器或类型/定义不匹配均不能按该配置存入。存入成功后仓内加一、托盘清空；仅把物品移到托盘不代表已经存入。
- Flex枪头盒进入仓内堆叠存储时，按官方正确装载要求配置并实物带上兼容盖子，包括拟存回的空盒；交互时可简短提醒备盖、带盖装仓，后续取头前按搬运/板盖API处理。此条件不泛化为“所有临时放在shuttle的耗材必须带盖”。官方指南要求带盖；本次核对v10.0.0源码未发现一律拒绝无盖声明的校验，不将该要求表述为所有API版本必报错。
- 容量按实际主耗材/盖/适配器高度与堆叠重叠量核对，不统一写死最大件数。fill/empty是暂停后的人工补入/移出，不是store/retrieve的自动动作替代；变更后按实际结果更新库存，已有无关状态不凭空清除。具体参数与count含义继续查API。
- 仓内可双向存取；不得将“供料常用取出”推成只能取不能存。完整搬运、抓手/盖、当前托盘占用和后续动作仍按各自条件核对，不把安装可放等同于立即可执行存取。

Stacker增补来源（2026-10-29核对；API范围≤2.30）：官方v10.0.0，commit e8c6d0a424c25fff1604e2a02e4ccaedac95b9af：
- docs/python-api/docs/modules/flex-stacker.md，blob 17608d7e6128ce5c2d9dc8d351f22daef801742a：结构、声明、托盘临时使用、带盖及示例。
- api/src/opentrons/protocol_api/module_contexts.py，blob 62aa59d03ad57ab9fb7b71a47cd15e0608b21b0f：共享继承、set/store/retrieve/get_stored_labware契约；接口签名仍唯一维护于api-module-flex-stacker/common。
- api/src/opentrons/protocol_engine/commands/flex_stacker/retrieve.py（2cb205d984955b720fd76fddd5dfb634337f58b8）、store.py（69092dc839aac9f2ad2f22dd247547096fb44cc7）、set_stored_labware.py（229b5b6d682b038e1a907b6b028d7157175318ff）：取出为空托盘、存入整套匹配及重新声明前仓内为空。
- api/src/opentrons/protocol_engine/commands/load_labware.py（c580faffadc5e6adafe6bf92401c9e9eb7905d7c）、move_labware.py（cbbe632ccca1e6ef7eff6f4a7bb586d4ac8af27d）、state/geometry.py（68357e61b45daf79d956d0c13f41ea7bea0584bc）：模块承载与占用校验不等同于仓内存入校验；异类临时承载仍查实际定义及动作条件。
- api/src/opentrons/protocol_engine/state/labware.py（dedeee6786ddde009280527ccdc6c969bf633d16）raise_if_stacker_labware_pool_is_not_valid与commands/flex_stacker/common.py（c2cdd567e5445cc002ac225f9bfa35698fb0304b）：未发现无盖一律报错校验，不据此取消官方带盖装仓要求。
- 官方装载说明 https://docs.opentrons.com/stacker/loading-labware/ （在线核对，未固定内容版本）：装料门人工装入、堆叠与人工取出；不固定门的方向。不将源码阅读当SDK模拟或实机验证。

仓体安装与托盘归位于2026-11-06核对。依据[官方安装前说明](https://docs.opentrons.com/stacker/pre-installation/)和[官方安装后说明](https://docs.opentrons.com/stacker/post-installation/#attaching-the-shuttle)。
