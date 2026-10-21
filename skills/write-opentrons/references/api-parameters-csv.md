# 运行参数与 CSV

条目目录（可用rg按名称定位）：
- 参数类型与输入方式
- CSV：从导入到切片
- CSV 的其他访问方式
- parse_as_csv 的格式参数
- ProtocolContext.params
- CSVParameter.parse_as_csv
- CSVParameter.contents
- CSVParameter.file
- CSVParameter.file_opened
- ParameterContext.add_int
- ParameterContext.add_float
- ParameterContext.add_bool
- ParameterContext.add_str
- ParameterContext.add_csv_file

来源：维护版API速查表 v6；文档基线 API 2.30，2026-10-12。用户最新规则见SKILL.md及operations.md。

定义可配置参数、读取参数值、导入 CSV 与处理二维数据。

## 参数类型与输入方式
类型 定义接口 运行时选择方式 关键约束 bool add_bool() 开关 / On、Off 值为 True 或 False int add_int() 范围内整数输入，或固定选项 minimum + maximum 与 choices 二选一 float add_float() 范围内小数输入，或固定选项 minimum + maximum 与 choices 二选一；值使用浮点数 str add_str() 固定选项 必须提供 choices；不支持自由文本输入。即使签名写 choices=None，也不代表可省略选项后自由输入。 CSVParameter add_csv_file() 选择 CSV 文件 无默认文件；当前每次运行只支持一个 CSV 参数

choices 为字典列表，每项包含 display_name 和 value；default 应是有效选项或范围内值。minimum / maximum 含边界且需同时指定；unit 仅用于带范围的数值参数，影响显示而不改变数值。display_name 最多 30 字符，description 最多 100，unit 最多 10。

读取入口为 protocol.params.<variable_name>，类型取决于定义；值在运行设置中确定。协议名称、API 版本等 run() 外的元数据不由这些运行参数动态决定。 官方参数定义 · 官方参数读取


## CSV：从导入到切片
导入接口返回数据后，后续行列访问和切片是 Python 列表操作。默认 parse_as_csv() 的每个单元格是 str，数字需显式转换。


```python
def add_parameters(parameters: protocol_api.ParameterContext):
    parameters.add_csv_file(
        variable_name="normalization_csv",
        display_name="均一化补水 CSV",
        description="包含目标孔位和补水体积",
    )

# 在 run(protocol) 内读取：
rows = protocol.params.normalization_csv.parse_as_csv()
# rows 的类型：list[list[str]]
```

目的 写法 条件 / 含义 第一行 rows[0] 需非空；不保证一定是表头 第二行第三列 rows[1][2] 索引从 0 开始；需确认行列存在 去掉第一行 rows[1:] 仅在第一行确实是表头时使用 指定行段 rows[start:stop] 包含 start，不包含 stop；省略端点表示开头/末尾 指定一列 [row[col] for row in data_rows] 每行都需要有该列 指定行列区域 [row[c0:c1] for row in rows[r0:r1]] 二维列表先切行再切各行的列，不能用 rows[r0:r1, c0:c1] 转换体积 float(cell.strip()) 先检查空值与内容；非法字符串会抛出 ValueError

对应用户的均一化模板：扫描表头找到“补水体积”所在列 → data_rows = rows[header_row_index + 1:] → 第一列取孔位 → 指定列取体积 → 清洗、转换和检查。该模板允许表头前有说明行，因此不能一律固定跳过首行。阈值、重复孔处理、体积分段是模板的业务规则，不属于 CSV API。

当 CSV 尚未选择时，可以捕获 RuntimeParameterRequiredError 并提供用于协议分析的占位二维数据；这不是 CSV 默认文件。正式运行的数据由用户选择的 CSV 提供。此处理方式来自官方示例，也出现在用户的均一化模板中。


## CSV 的其他访问方式
contents 返回整段字符串；file 返回只读 UTF-8 文本文件对象；file_opened 表示文件对象是否打开。优先按既有模板使用 parse_as_csv()，相关属性签名见下方条目。


## parse_as_csv 的格式参数
detect_dialect=True 时尝试自动识别格式。读取吸光度读板模块导出的 CSV 时，官方要求设置 False。**kwargs 接收 Python csv.reader 的格式参数；下表为标准 dialect 的通常默认值，自动检测可能改变它们。

名称 类型 / 通常默认值 用途 delimiter str，单字符，"," 列分隔符 quotechar str | None，通常为双引号 包围字段的字符 escapechar str | None，None 转义字符 doublequote bool，True 是否把成对引号解释为字段内引号 skipinitialspace bool，False 是否忽略分隔符后的空格 strict bool，False 是否对格式错误严格报错 quoting int，通常 csv.QUOTE_MINIMAL 引号解析模式；本表未展开其他 QUOTE_* 模式，额外模式按缺失反馈 lineterminator str，通常 "\r\n" reader 不使用此设置决定换行识别

建议保持默认解析后显式转换数值；改变 quoting 模式可能改变读入值类型，不能把默认的字符串规则无条件推广到所有格式参数。来源： Python csv 官方文档 、 Python 序列切片 。这些链接仅作溯源，日常查用无需联网。
ProtocolContext.params CSVParameter.parse_as_csv CSVParameter.contents CSVParameter.file CSVParameter.file_opened ParameterContext.add_int ParameterContext.add_float ParameterContext.add_bool ParameterContext.add_str ParameterContext.add_csv_file

## ProtocolContext.params

官方来源


```python
params: Parameters
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） The values of runtime parameters, as set during run setup. Each attribute of this object corresponds to the variable_name of a parameter.
See Using Parameter Values for details. Parameter values can only be set during run setup. If you try to alter the value
    of any attribute of params , the API will raise an error.


## CSVParameter.parse_as_csv

官方来源


```python
parse_as_csv(detect_dialect: bool = True, **kwargs: Any) -> List[List[str]]
```

参数名 类型 默认值 / 必填 传参方式 detect_dialect bool True 位置或关键字 **kwargs Any 可省略 可变关键字

官方参数含义、返回值与使用约束（已保存在本文件） Parses the CSV data and returns a list of lists. Each item in the parent list corresponds to a row in the CSV file.
If the CSV has a header, that will be the first row in the list: .parse_as_csv()[0] . Each item in the child lists corresponds to a single cell within its row.
The data for each cell is represented as a string. You may need to trim
whitespace or otherwise validate string contents before passing them as
inputs to other API methods. For numeric data, cast these strings to
integers or floating point numbers, as appropriate. Parameters: detect_dialect ( bool , default: True )
          – If True , examine the file and try to assign it
a csv.Dialect to improve parsing behavior. Set this
to False when using the file output of AbsorbanceReaderContext.read() as a runtime parameter. **kwargs ( Any , default: {} )
          – For advanced CSV handling, you can pass any of the formatting parameters accepted by csv.reader() from the Python standard library.


## CSVParameter.contents

官方来源


```python
contents: str
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） Returns the full contents of the CSV file as a single string.


## CSVParameter.file

官方来源


```python
file: TextIO
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） Returns the file handler for the CSV file. The file is treated as read-only, UTF-8-encoded text.


## CSVParameter.file_opened

官方来源


```python
file_opened: bool
```

属性类型见上方官方签名；不是可调用方法。

官方参数含义、返回值与使用约束（已保存在本文件） Returns True if a file handler is open for the CSV parameter.


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
