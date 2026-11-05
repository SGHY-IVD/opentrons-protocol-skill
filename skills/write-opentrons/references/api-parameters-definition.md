# 运行参数声明与输入约束

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

一般运行参数自API 2.18起；CSV文件参数自2.20起，旧目标不能仅因支持一般参数就使用CSV。版本选择见[版本索引](api-versions.md#已核对的关键分界)。

[完整成员索引](api-parameters-csv.md)；生成与审查仍按SKILL.md及[操作规则](operations.md)执行。

- [参数类型与输入方式](#参数类型与输入方式)
- [ParameterContext.add_int](#parametercontextadd_int)
- [ParameterContext.add_float](#parametercontextadd_float)
- [ParameterContext.add_bool](#parametercontextadd_bool)
- [ParameterContext.add_str](#parametercontextadd_str)
- [ParameterContext.add_csv_file](#parametercontextadd_csv_file)

## 参数类型与输入方式
类型 定义接口 运行时选择方式 关键约束 bool add_bool() 开关 / On、Off 值为 True 或 False int add_int() 范围内整数输入，或固定选项 minimum + maximum 与 choices 二选一 float add_float() 范围内小数输入，或固定选项 minimum + maximum 与 choices 二选一；值使用浮点数 str add_str() 固定选项 必须提供 choices；不支持自由文本输入。即使签名写 choices=None，也不代表可省略选项后自由输入。 CSVParameter add_csv_file() 选择 CSV 文件 无默认文件；当前每次运行只支持一个 CSV 参数

choices 为字典列表，每项包含 display_name 和 value；default 应是有效选项或范围内值。minimum / maximum 含边界且需同时指定；unit 仅用于带范围的数值参数，影响显示而不改变数值。display_name 最多 30 字符，description 最多 100，unit 最多 10。

读取入口为 protocol.params.<variable_name>，类型取决于定义；值在运行设置中确定。协议名称、API 版本等 run() 外的元数据不由这些运行参数动态决定。 官方参数定义 · 官方参数读取


## ParameterContext.add_int

官方来源


```python
add_int(display_name: str, variable_name: str, default: int, minimum: Optional[int]=None, maximum: Optional[int]=None, choices: Optional[List[ParameterChoice]]=None, description: Optional[str]=None, unit: Optional[str]=None) -> None
```

参数名 类型 默认值 / 必填 传参方式 display_name str 必填 位置或关键字 variable_name str 必填 位置或关键字 default int 必填 位置或关键字 minimum Optional[int] None 位置或关键字 maximum Optional[int] None 位置或关键字 choices Optional[List[ParameterChoice]] None 位置或关键字 description Optional[str] None 位置或关键字 unit Optional[str] None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Creates an integer parameter, settable within a given range or list of choices.

Arguments:
    display_name: The display name of the int parameter as it would show up on the frontend.
    variable_name: The variable name the int parameter will be referred to in the run context.
    default: The default value the int parameter will be set to. This will be used in initial analysis.
    minimum: The minimum value the int parameter can be set to (inclusive). Mutually exclusive with choices.
    maximum: The maximum value the int parameter can be set to (inclusive). Mutually exclusive with choices.
    choices: A list of possible choices that this parameter can be set to.
        Mutually exclusive with minimum and maximum.
    description: A description of the parameter as it will show up on the frontend.
    unit: An optional unit to be appended to the end of the integer as it shown on the frontend.


## ParameterContext.add_float

官方来源


```python
add_float(display_name: str, variable_name: str, default: float, minimum: Optional[float]=None, maximum: Optional[float]=None, choices: Optional[List[ParameterChoice]]=None, description: Optional[str]=None, unit: Optional[str]=None) -> None
```

参数名 类型 默认值 / 必填 传参方式 display_name str 必填 位置或关键字 variable_name str 必填 位置或关键字 default float 必填 位置或关键字 minimum Optional[float] None 位置或关键字 maximum Optional[float] None 位置或关键字 choices Optional[List[ParameterChoice]] None 位置或关键字 description Optional[str] None 位置或关键字 unit Optional[str] None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Creates a float parameter, settable within a given range or list of choices.

Arguments:
    display_name: The display name of the float parameter as it would show up on the frontend.
    variable_name: The variable name the float parameter will be referred to in the run context.
    default: The default value the float parameter will be set to. This will be used in initial analysis.
    minimum: The minimum value the float parameter can be set to (inclusive). Mutually exclusive with choices.
    maximum: The maximum value the float parameter can be set to (inclusive). Mutually exclusive with choices.
    choices: A list of possible choices that this parameter can be set to.
        Mutually exclusive with minimum and maximum.
    description: A description of the parameter as it will show up on the frontend.
    unit: An optional unit to be appended to the end of the float as it shown on the frontend.


## ParameterContext.add_bool

官方来源


```python
add_bool(display_name: str, variable_name: str, default: bool, description: Optional[str]=None) -> None
```

参数名 类型 默认值 / 必填 传参方式 display_name str 必填 位置或关键字 variable_name str 必填 位置或关键字 default bool 必填 位置或关键字 description Optional[str] None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Creates a boolean parameter with allowable values of "On" (True) or "Off" (False).

Arguments:
    display_name: The display name of the boolean parameter as it would show up on the frontend.
    variable_name: The variable name the boolean parameter will be referred to in the run context.
    default: The default value the boolean parameter will be set to. This will be used in initial analysis.
    description: A description of the parameter as it will show up on the frontend.


## ParameterContext.add_str

官方来源


```python
add_str(display_name: str, variable_name: str, default: str, choices: Optional[List[ParameterChoice]]=None, description: Optional[str]=None) -> None
```

参数名 类型 默认值 / 必填 传参方式 display_name str 必填 位置或关键字 variable_name str 必填 位置或关键字 default str 必填 位置或关键字 choices Optional[List[ParameterChoice]] None 位置或关键字 description Optional[str] None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Creates a string parameter, settable among given choices.

Arguments:
    display_name: The display name of the string parameter as it would show up on the frontend.
    variable_name: The variable name the string parameter will be referred to in the run context.
    default: The default value the string parameter will be set to. This will be used in initial analysis.
    choices: A list of possible choices that this parameter can be set to.
        Mutually exclusive with minimum and maximum.
    description: A description of the parameter as it will show up on the frontend.


## ParameterContext.add_csv_file

官方来源


```python
add_csv_file(display_name: str, variable_name: str, description: Optional[str]=None) -> None
```

参数名 类型 默认值 / 必填 传参方式 display_name str 必填 位置或关键字 variable_name str 必填 位置或关键字 description Optional[str] None 位置或关键字

官方参数含义、返回值与使用约束（已保存在本文件） Creates a CSV parameter that can be set to any CSV file via the Flex ODD or a local computer.

Arguments:
    display_name: The display name of the CSV parameter as it would show up on the frontend.
    variable_name: The variable name the CSV parameter will be referred to in the run context.
    description: A description of the parameter as it will show up on the frontend.
