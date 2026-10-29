# 协议结构、支持类型与常量
来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

目录：协议组成与骨架；依赖与执行边界；Point；枚举与特殊位置；参数定义与读取；异常；按孔名访问。

## 协议组成与骨架

[协议骨架](../assets/protocol-skeleton.py)是唯一的文件结构示例，只导航，不维护动作、数值或第三方驱动实例；不把模板本身、注释分区或可选区块升级为新的必经步骤。可变区块按任务选取、移动或省略，不要求照抄全部区块或拆成固定函数；教学骨架不是已完成实验。

|组成|保留的官方契约|可变内容|
|---|---|---|
|import|使用实际需要的公开接口；注解所用名称须可解析|库、导入数量；类型注解本身可选|
|metadata|协议展示信息；本骨架展示，实际按需要填写|名称、作者、描述等按实际写，不固定示例内容|
|requirements|Flex的requirements声明robotType="Flex"；apiLevel在metadata或requirements择一声明|新建建议统一把apiLevel写入requirements；合法既有写法不因位置不同误报，目标按api-versions核对；不是pip依赖清单|
|add_parameters|有参数时使用此单参数入口，定义在run前；定义上下文为ParameterContext|函数可省略、参数名/注解和具体参数；技能默认见operations|
|run|正常协议的单参数入口；App/触摸屏流程由机器人软件调用|形参名、注解、内部组织与合法辅助函数|

常量/完整内嵌JSON通常置于导入和声明后，辅助函数/类通常在run前定义；依赖参数/CSV的实例在run获得输入后创建，设备连接/调用/释放按实际生命周期安排。这些是组织建议，不禁止其他合法且符合现有规则的Python写法。内嵌与JSON加载细节只见custom-labware和api-layout，数据预检只见参数资料与operations；骨架不新增一套七步固定流程。

可选源码分隔与区块说明见operations“源码说明与运行文案”；不要求套用分区或模板外观，不能替代实际规则判断。

模板版本、API和状态注释均为示例依据，生成时改成本次实际读取版本、用户覆盖、实际审查/模拟/实机范围和未决项；不照抄通过结论，也不把空容器/注释当完整内嵌。API占位须先替换为真实目标，不能当有效apiLevel；模板NotImplementedError只标记尚未实现，补齐真实流程后移除；删掉标记不证明实验已完成。

## 依赖与执行边界

- 公开API、标准库、第三方Python包及外接硬件驱动分别核对；额外包须对应实际机器人/分析/模拟环境，不能因助手能import就称客户可用，不自动安装。自写包装类不构成官方硬件支持或安装证据。
- 顶层及类体/装饰器/默认参数可能在定义时求值；不得把设备动作、连接副作用或依赖当前参数的状态藏在导入阶段。普通协议使用传入上下文，不混入Jupyter手动run/自建上下文。
- 客户protocol不依赖技能目录或作者电脑路径；flow_rate.py/delay.py等生成工具不随协议部署。外部文件/完整内嵌/运行时CSV分别按custom-labware及参数资料核对。
- 结构/依赖变化按本节检查；局部参数改动不强制展开整个骨架。语法、官方模拟和实机验证分别记录。

来源：2026-10-28核对官方[Flex协议结构与依赖](https://docs.opentrons.com/flex/protocols/python-api/)、[Tutorial](https://docs.opentrons.com/python-api/tutorial/)、[版本声明](https://docs.opentrons.com/python-api/versioning/)、[参数定义](https://docs.opentrons.com/python-api/runtime-parameters/defining/)与[参数读取](https://docs.opentrons.com/python-api/runtime-parameters/using-values/)。为当前主题文档核对，未固定页面提交；不升级API 2.30维护基线。Tutorial对Flex的apiLevel位置措辞比versioning严格，本次另核对官方v10.0.0固定提交e8c6d0a424c25fff1604e2a02e4ccaedac95b9af的api/src/opentrons/protocols/parse.py：解析接受两处择一，拒绝重复声明；据此区分官方接受范围与本技能新建建议。


## Point
from opentrons.types import Point；按以下字段构造。字段无默认值。

```python
x: float = 0.0
y: float = 0.0
z: float = 0.0
```
官方源码


## 枚举与特殊位置
名称 类型 / 定义 ALL NozzleLayout.ALL SINGLE NozzleLayout.SINGLE COLUMN NozzleLayout.COLUMN ROW NozzleLayout.ROW PARTIAL_COLUMN NozzleLayout.PARTIAL_COLUMN OFF_DECK OffDeckType 特殊位置对象
上述常量均从 opentrons.protocol_api 导入。布局的适用条件见 configure_nozzle_layout 本地说明。


以下为SDK内部类型节选，只用于语义参考；相对导入与实现类不得复制为客户protocol依赖。公开结构示例见本页骨架。

```python
from typing import TypedDict, TypeVar, Union

from .csv_parameter_interface import CSVParameter

PrimitiveAllowedTypes = Union[str, int, float, bool]
AllAllowedTypes = Union[str, int, float, bool, bytes, None]
UserFacingTypes = Union[str, int, float, bool, CSVParameter]

ParamType = TypeVar("ParamType", bound=AllAllowedTypes)


class ParameterChoice(TypedDict):
    """A parameter choice containing the display name and value."""

    display_name: str
    value: PrimitiveAllowedTypes

```
ParameterChoice 的具体类型与选择值约束同时参见 add_int / add_float；不能只凭联合类型给整数参数传入任意字符串。


## 参数定义与读取分开

```python
def add_parameters(parameters: protocol_api.ParameterContext):
    ...

def run(protocol: protocol_api.ProtocolContext):
    # 将sample_count替换为本协议已定义的variable_name
    value = protocol.params.sample_count
```
ParameterContext 提供 add_* 方法；Parameters 是 protocol.params 返回的参数值容器。样本里的 parameters: protocol_api.Parameters 注解不作为定义阶段类型依据。


## RuntimeParameterRequiredError
从 opentrons.protocol_api 导入，对应官方 RuntimeParameterRequired 异常别名。下方为SDK内部实现节选，不在客户协议重新定义这些异常或导入opentrons_shared_data内部错误类。

```python
from typing import Dict, Optional, Sequence

from opentrons_shared_data.errors import EnumeratedError, ErrorCodes, GeneralError


class RuntimeParameterRequired(GeneralError):
    """An error raised when a parameter is required to be set for full analysis."""

    def __init__(
        self,
        message: Optional[str] = None,
        detail: Optional[Dict[str, str]] = None,
        wrapping: Optional[Sequence[EnumeratedError]] = None,
    ) -> None:
        """Build an RuntimeParameterRequired."""
        super().__init__(
            ErrorCodes.RUNTIME_PARAMETER_VALUE_REQUIRED, message, detail, wrapping
        )


class ParameterValueError(ValueError):
    """An error raised when a parameter value is not valid."""


class ParameterDefinitionError(ValueError):
    """An error raised when a parameter definition value is not valid."""


class ParameterNameError(ValueError):
    """An error raised when a parameter name or description is not valid."""


class IncompatibleParameterError(ValueError):
    """An error raised when a parameter conflicts with another parameter."""

```


## 按孔名访问
labware["A1"]：用户样本已有此写法。本表的具名方法也提供 wells_by_name()；孔名必须来自实际耗材定义，不能仅由类型签名推断所有耗材都具备 A1–H12。
