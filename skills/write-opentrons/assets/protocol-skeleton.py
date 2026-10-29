# 技能：write-opentrons
# 规则版本：2026-10-28.10（模板依据；正式稿按实际读取版本改写）
# 用户覆盖项：按本次任务填写；审查范围/结论：按实际检查填写。
# 官方模拟：未运行；实机验证：未进行；未决项：实际配置与实验尚未填入。
# 本文件仅作结构导航与示例；分隔注释、可选区块、位置和顺序均非硬要求。

# 导入：公开API；标准库/第三方依赖按需。见api-types.md“依赖与执行边界”。
from opentrons import protocol_api

# ==================== 协议声明 ====================
# 展示字段按实际填写。
metadata = {
    "protocolName": "Flex协议结构骨架",
    "author": "实际作者或机构",
    "description": "结构导航，尚未填入实验流程。",
}

# Flex执行要求；apiLevel是待填占位，不是可运行值，设置见api-versions.md。
requirements = {"robotType": "Flex", "apiLevel": "<按实际软件填写目标API>"}

# ==================== 可选数据与辅助定义 ====================
# 可选：常量、预计算方案。见rates.md及delays.md；不在骨架抄参数表。

# 可选：完整内嵌耗材JSON/定义字典。见custom-labware.md。
# 完整内容放数据区；from_definition调用放实际加载处；此注释不代表已有定义。

# 可选：纯处理函数/类、第三方驱动包装类定义。见api-types.md“依赖与执行边界”。
# 参数/CSV相关实例及设备连接按依赖放run相应阶段，不预写虚构驱动接口。


# ==================== 运行参数定义（按需） ====================
# 接口见api-parameters-csv.md；具体字段/默认/排序见operations.md。
# 有运行参数时使用；无参数可删去整个函数。
def add_parameters(parameters: protocol_api.ParameterContext):
    # 参数/CSV接口见api-parameters-csv.md；技能默认参数见operations.md。
    pass


# ==================== 协议入口 ====================
# 正常App/触摸屏流程由机器人软件调用；参数名和类型注解可按合法写法调整。
def run(protocol: protocol_api.ProtocolContext):
    # 模板专用标记，补齐实际实验后移除；不是正式协议必须保留的命令。
    raise NotImplementedError("仅结构导航：尚未填入实际实验。")

    # 分区是导航及输出样式，允许按实际依赖移动、合并或省略，不强拆成函数。

    # -------------------- 参数读取与预检 --------------------
    # 参数/CSV、处理类实例、方案选择：api-parameters-csv.md、rates.md、operations.md。

    # -------------------- 布局与设备加载 --------------------
    # 模块/适配器/耗材/移液器/垃圾处理：catalog.txt、installation.txt、api-layout.md。
    # 内嵌定义加载：custom-labware.md；第三方实例/连接按已核实驱动和环境安排。

    # -------------------- 液体标签与初始液量 --------------------
    # 液体定义、颜色、批量初始化和账本：api-wells-liquids.md、operations.md。

    # -------------------- 实验执行 --------------------
    # 先后关系按实验安排：装载准备、移液/混匀、温控、等待、搬运、暂停及循环。
    # 规则/原子组合：operations.md、patterns.md；模块：api-modules.md及对应经验。
    # 搬运：api-gripper.md、installation.txt；暂停/延时：api-flow.md。

    # -------------------- 正常收尾 --------------------
    # 枪头/液体归宿、模块与第三方资源：operations.md、module-practices.md及实际驱动。
    # 实际审查与交付状态：protocol-review.md；不把模板标记当成已经验证。

# 注释路由位于references/；生成时按任务查用，不把全部参考或模板标记复制给客户。
