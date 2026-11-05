# 参数显示与流速选择片段

仅实现参考，按已命中的权威规则与本次前提使用；已读取内容直接复用。

## dry_run流速赋值

按rates.md确定两分支的维护配置；下方仅展示定值方案的结构占位，不得原样交付，最终用数值或已赋值变量替换右侧来源变量。参数化计算按参数化指引处理。只需选择速率，不复制整段移液流程。

```python
aspirate_flow_rate = water_aspirate_rate if dry_run else normal_aspirate_rate
dispense_flow_rate = water_dispense_rate if dry_run else normal_dispense_rate
```

混匀同样分别选择mix_aspirate_rate（M）、stroke_aspirate_rate（S）、stroke_dispense_rate（S）和final_dispense_rate（M）；一吸多分按各实际体积赋值。相同值直接合并。其他原子片段使用这些已选定的flow_rate变量。

## 交付标识与参数

技能标识、参数默认及展示语义按[输出规范](protocol-output.md)；本页仅演示声明与读取，生成时使用实际版本和本次覆盖，不照搬占位。返回判断仍须满足[枪头管理](operations.md#枪头管理)。

## 二选一参数：choice显示、布尔判断

以下示范参数声明与读取，不是完整协议；其他二选一参数采用相同结构，标签按具体行为命名。

```python
def add_parameters(parameters):
    parameters.add_str(
        variable_name="dry_run", display_name="运行方式", default="normal",
        choices=[{"display_name": "正式运行", "value": "normal"},
                 {"display_name": "用水试运行", "value": "water_test"}],
    )
    parameters.add_str(
        variable_name="return_tips", display_name="枪头处理", default="discard",
        choices=[{"display_name": "丢弃枪头", "value": "discard"},
                 {"display_name": "返回枪头", "value": "return"}],
    )

# 在run(protocol)中读取，后续原子流程使用这两个布尔变量：
dry_run = protocol.params.dry_run == "water_test"
return_tips = protocol.params.return_tips == "return"
```

return_tips仍须结合当前喷嘴配置及复用规则判断，不因choice选中返回而绕过限制。
