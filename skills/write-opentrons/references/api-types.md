# 支持类型、常量与协议入口
来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

以下只补充本批接口需要的定义。


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
    value = protocol.params.<variable_name>
```
ParameterContext 提供 add_* 方法；Parameters 是 protocol.params 返回的参数值容器。样本里的 parameters: protocol_api.Parameters 注解不作为定义阶段类型依据。


## RuntimeParameterRequiredError
从 opentrons.protocol_api 导入，对应官方 RuntimeParameterRequired 异常别名。

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
