# 配置、硬件与枪头问答

问法与要点仅提供解释灵感，可按本次问题自由组合、改写；执行要求仍以所引资料为准，已读取的依据直接复用。

## 配置与布局

### 10. 为什么写协议前要确定耗材、设备配置和布局

- 常见问法：为什么先问装了什么模块？为什么不能直接按实验步骤写？耗材放哪里有那么重要吗？
- 解释要点：耗材定义描述物件内部的位置，配置与布局说明它在本次设备上放在哪里、由什么承载。Flex可采用不同移液器、模块、适配器及甲板配置；同一块板直接上甲板或放在模块/适配器上，实际位置与高度会不同。机器人依赖准确数据、安装位置和程序，已有传感器不能替代这些基础信息。可从定位准确、安装适配和动作可达解释预先核对的价值，按用户理解展示最终实物与位置；底层核验及确认流程仍引用原规则。
- 依据出处：[布局与耗材确认](protocol-interaction.md#布局与耗材确认)、[统一安装核验](installation-core.md#统一安装核验)、[官方甲板配置说明](https://docs.opentrons.com/flex/touchscreen/deck-config/)。

## 垃圾处理

### 19. 内置垃圾桶与外置垃圾槽有什么区别

- 常见问法：trash bin和waste chute有什么区别？枪头很多怎么办？空盒或孔板能直接扔吗？
- 解释要点：内置垃圾桶在机内收集枪头，无需在机外另设废物出口与接收容器；但占用甲板位置，能容纳的量有限，枪头堆积较多时需要安排清理，不能仅凭总数量推定堆放高度。可选外置垃圾槽把废物导到机外接收容器，便于较大量废物收集，但需要机外空间；适用条件满足时还可由抓手丢弃受支持的枪头盒、孔板等耗材，这类整件丢弃使用外置垃圾槽。旧Flex协议使用API 2.15时只有固定A3垃圾桶；其他位置或外置垃圾槽从2.16才支持。具体位置、盖状态与搬运条件按原资料，不因开口大就推断任意物体可丢。称呼不明确时可结合是否外置、实际位置或英文名澄清，不把内置垃圾桶称为内置垃圾槽。
- 依据出处：[垃圾处理与安装关系](installation.txt)、[搬运API](api-gripper.md)、[垃圾称呼与配置确认](protocol-interaction.md#实际硬件描述核对回显确认)、[官方外置垃圾槽](https://docs.opentrons.com/flex/system-description/robot/#waste-chute)、[官方丢弃与盖配置](https://docs.opentrons.com/python-api/deck-slots/#waste-chute)。

## 移液器与枪头

### 25. 八通道是否可调间距，只能用于96孔板吗

- 常见问法：和手动八通道排枪一样吗？能同时处理离心管、24孔板或其他孔距的耗材吗？
- 解释要点：Flex八通道可类比固定排枪，喷嘴间距固定为9mm，部分取头改变参与数量与定位参考，不改变间距。能否并行看实际目标孔与所用喷嘴是否匹配，以及机身和枪头空间，不只看耗材名称或孔数；24孔板、离心管等不能因装得下就套用完整八通道操作。也不能一概说非96孔板不可用，例如384孔板存在隔孔匹配的用法；单喷嘴可用于适用的逐孔操作，但不因此保证任意容器可达。
- 依据出处：[喷嘴配置接口](api-pipette-configuration.md#instrumentcontextconfigure_nozzle_layout)、[既有喷嘴几何来源](reservoir-position-sources.json)、[官方部分取头说明](https://docs.opentrons.com/python-api/pipettes/partial-tip-pickup/)、[官方耗材类型与384孔板](https://docs.opentrons.com/flex/labware/types/)。

### 26. 只有三个或五个样本，八通道能否处理

- 常见问法：样本数必须是8的倍数吗？能少取几个头，或只取一支吗？
- 解释要点：样本排列和各孔动作适合并行时，可按需用单支或连续2–7支的部分取头，也可用完整8支，不能当作任意挑选的分散喷嘴掩码。直观上是用所需喷嘴对准枪头取用，实际由喷嘴布局及对应定位实现，不是任意手加偏移。整列组织通常便于批量处理，可作为实验允许时的建议，不为凑8的倍数擅增样本或处理空孔。已取满8支时各通道同量吸排，不能说其中3支可独立关闭；空余孔的处理需有明确安排。具体布局、版本与枪头返回条件查原规则。
- 依据出处：[枪头管理](operations.md#枪头管理)、[喷嘴配置接口](api-pipette-configuration.md#instrumentcontextconfigure_nozzle_layout)、[官方部分列取头](https://docs.opentrons.com/python-api/pipettes/partial-tip-pickup/#partial-column-layout)、[官方八通道产品FAQ](https://opentrons.com/products/opentrons-flex-8-channel-pipette)。

### 27. 为什么部分取头时要考虑旁边的耗材

- 常见问法：只是少取几个头，为什么布局也可能要调整？模拟通过就不会碰撞了吗？
- 解释要点：部分取头改变定位参考，移液器机身可能伸到相邻板位上方；八通道尤其需结合前后方向伸出、甲板边界、周围耗材高度及实际取头/移液位置考虑。API分析可拦截已识别的空间冲突，但不能代替实物安装、真实尺寸与全路径核对，也不保证检出全部碰撞。可用模拟和合适的实机试跑帮助验证，不把分析通过当作无需考虑邻位的理由，也不凭相邻就一律判冲突。静态安装与实际动作可达性分别按原资料核对。
- 依据出处：[统一安装核验](installation-core.md#统一安装核验)、[空间位置与路径](operations.md#空间位置与路径)、[官方部分取头与冲突](https://docs.opentrons.com/python-api/pipettes/partial-tip-pickup/#tip-pickup-and-conflicts)、[官方模拟范围](protocol-review.md#环境检查与官方模拟)。

### 28. 为什么建议用匹配体积的移液器和枪头

- 常见问法：大枪头也能吸少量，为什么还建议换小规格？换小枪头是不是就一定准？
- 解释要点：思路与手工移液相近：在实际移液器、枪头和模式兼容的前提下，选择能容纳本次全部吸入占用、又适合目标体积的规格，通常优先考虑满足流程需求的较小枪头。容量够用不等于处于合适量程，换小枪头也不改变移液器及模式自身的限制；还需看保留液/空气占用、液体性质、位置和相应性能数据。它是合理选型方向，不保证所有液体都达到同一精度，流速曲线有值也不能证明量程和性能合适。
- 依据出处：[移液器模式接口](api-pipette-configuration.md#instrumentcontextconfigure_for_volume)、[容量与状态核算](pipette-mechanics.md)、[流速适用边界](rates.md)、[官方枪头选择与性能](https://docs.opentrons.com/flex/system-description/pipettes/)。

### 29. 枪头盒用掉一部分后能否接着用，状态由谁管理

- 常见问法：每次必须补满吗？机器会记住上次用到哪里吗？能从剩下的位置开始吗？
- 解释要点：按本次运行初始化枪头的普通协议，不会自动继承上次余头进度或扫描实物剩余位置；按满盒起步编写时，实物需与这一假设一致，而非所有协议都只能用满盒。运行内通常由API维护自动取头顺序，不需要每份脚本自写索引；程序追踪也不等于实物检测，分析通过不能证明盒内确有头。连续剩余新头可按需要指定合适起点并核对数量、喷嘴布局；一个起点不能表达任意缺头分布。退回的已用头不自动成为新头，实际换盒与状态更新仍按原规则，不用清除记录冒充实物补给。
- 依据出处：[枪头管理](operations.md#枪头管理)、[枪头不足与同位置补给](operations.md#枪头不足与同位置补给)、[取头接口](api-pipette-tips.md#instrumentcontextpick_up_tip)、[官方取头与追踪](https://docs.opentrons.com/python-api/building-block-commands/pipette-tips/)、[官方起点与逻辑状态](https://docs.opentrons.com/python-api/reference/instruments/)。

## 模块适配

### 32. 温控与热震荡为什么需要匹配的适配器

- 常见问法：直接把板或管放上去不行吗？为什么换耗材还要换金属块？适配器只是垫高吗？
- 解释要点：这类热适配器/铝块帮助匹配孔底或管壁形状、改善热接触并支撑定位；未贴合处的空气间隙会影响传热，因此不只是垫高。温控模块可加热和制冷，热震荡提供加热与振荡，不能把两者都称为可主动制冷。具体组合还涉及固定、锁扣、有效高度和搬运；热震荡官方明确要求兼容热适配器，不能统一说省略后也可使用。温控同样按实际组合与加载关系核对，API直接加载不一定表示实物没有适配器。运行前确保实际模块、适配器和耗材与代码一致，类型变化时重新核对组合及位置，不因都叫金属块而互换。
- 依据出处：[安装及模块适配关系](installation.txt)、[热震荡条件](module-conditions-heater-shaker.md)及[温控条件](module-conditions-temperature-module.md)、[模块加载入口](api-modules.md)、[官方热震荡适配器](https://docs.opentrons.com/flex/modules/heater-shaker/#thermal-adapters)、[官方温控铝块](https://docs.opentrons.com/flex/modules/temperature/#thermal-blocks)。
