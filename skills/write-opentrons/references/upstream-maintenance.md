# 官方仓库导航与资料更新（特殊排查/维护时读取）

采用随技能发布的已核对快照，不在下载、安装或每次生成时自动刷新。不把官方仓库设为运行依赖，不引入全量克隆或submodule。常规生成不联网刷新；官方耗材按catalog检索快照并按operations定向获取本次定义。具体异常或维护资料不能解释的特殊行为，可按下节定向查询官方依据；查证不等于升级资料或授权使用未收录接口。

## 来源与责任

官方主仓库：https://github.com/Opentrons/opentrons 。目录提示唯一维护在[operations.md](operations.md)的“官方仓库查找起点”，实际查询核对目标版本下的路径。

|资料|本地权威入口|更新方式|
|---|---|---|
|API签名、行为与版本边界|api-versions.md、各api-*.md；模块成员覆盖见module-api-coverage.json|按明确目标API及对应软件发布源码核对；不根据API数字自行猜软件tag|
|常用耗材、硬件型号与安装关系|catalog.txt、installation.txt|维护时定向核对公开文档、相关定义及实现；缺失不等于不兼容|
|官方全量耗材名称索引|labware-index.json；catalog.txt为查询入口|scripts/labware.py从完整固定发布目录提取；只维护时重建，非逐次生成同步|
|自定义耗材构建/字段查证|custom-labware.md|命中按需分支后定向查官方schema/定义及厂家尺寸，不扩展设备API/安装基线|
|单次任务所需孔几何|operations.md“耗材几何按需查询”|优先实际定义；缺失时按现有例外获取官方JSON，不自动写回技能|
|官方流速、等待、硬件参数|相关JSON的sources/commit/blob_sha等现有字段及配套说明|保留原始来源与项目覆盖的区别；只更新受影响条目|
|经验默认、模板与审查|operations.md、patterns/mixing-examples等、protocol-review.md|项目维护；不随官方刷新被覆盖，官方新限制冲突时报告并修正组合|

## 官方耗材索引维护

运行时search/get只读随技能发布的索引；fetch仅取明确选中的完整定义，不自动扫描整库。索引不是已验证安装/模型或当前机器人已装定义白名单。常用项继续留在catalog；移液器/模块型号与API独立维护，不从耗材文件名推导硬件支持。

维护时选定稳定发布tag并解析到commit，核对commit→definitions树的实际链，取得该提交的完整Git树及对应JSON，另取同commit的默认版本策略_default_labware_versions.py与全局展示策略shared-data/js/getLabware.ts。工具重算目录/根Git树与逐文件blob，但tag/commit到树及策略文件的绑定仍由维护者按官方来源核对；不能仅凭调用者填写的tag/commit声称来源已验证。只取得所需目录和策略文件即可，无需克隆全仓库。离线重建：

```bash
python scripts/labware.py build --definitions <definitions目录> --tree <完整树JSON> --default-versions <默认版本策略.py> --listing-policy <getLabware.ts> --release <稳定tag> --commit <40位提交> --retrieved-on <日期> --output <临时索引JSON>
```

build拒绝截断/删项/散列不符的Git树、缺文件、blob不符及路径/定义身份不一致；输出至新文件，维护者核对新增/删除、定义版本/schema、用途及常用项差异后才替换发布索引，不把部分下载当全量。普通检索排除旧格式、全局UI隐藏项和无公开默认版本的测试/草稿条目，保留完整源行及用途标记；不执行上游Python/TS，不用仅PD名单推断Python支持，也不泛化为schema 3禁用。不要把schema版本、定义version和机器人软件版本混为一谈；目标软件不匹配时按catalog核对对应版本，不自动升级。

实际运行工具验收 `python -m unittest discover -s assets/review-regression -p test_labware.py`；核心路由变化另按项目维护规则执行协议回归。API及硬件名单在明确维护任务中同步并核对兼容范围，不由索引重建顺带扩展。

## 特殊问题查找导航

触发条件：出现具体报错、实际行为与维护资料不一致，或已有资料无法解释影响当前任务的关键行为。普通生成、单纯未收录某个接口不自动触发全库搜索。先定位现有资料与目标API/机器人软件版本，再按问题只查相关层；已给出的日志、方法名或异常类型优先作为搜索词。

以下路径依据2026-10-21已取得的仓库树（commit `72fd2310e5b8f39e6024f3926c95bfc4468be260`）核对，仅是查找起点，不声明其内容与用户软件版本一致；实际使用时以目标版本目录为准。基础定义目录见operations.md，避免重复维护完整目录树。

|问题/能力|官方查找起点|查证重点|
|调用参数、默认行为、版本限制|`api/src/opentrons/protocol_api/`，按方法名定位|公开契约与版本标记；不要把内部方法当协议API|
|取头顺序、剩余枪头、部分喷嘴、换盒状态|上述目录的`instrument_context.py`、`labware.py`；必要时转`protocol_engine/state/`与`hardware_control/nozzle_manager.py`|调用如何更新状态、布局及起始位置影响；结合当前配置|
|吸排液余量、push-out、活塞准备、体积模式|`protocol_api/instrument_context.py` → `protocol_engine/commands/`、`execution/` → `hardware_control/`；数值查shared-data移液器定义|先跟踪实际调用链，再读相关硬件分支，不混用机型|
|液面计算、耗材模型、沿壁或喷嘴偏移|`protocol_api/labware.py`、`protocol_engine/state/`，配合shared-data耗材/移液器定义|几何字段、液量状态与坐标转换分别核对|
|甲板占位、模块堆叠、搬运冲突|shared-data甲板/模块/耗材定义，结合`protocol_engine/state/`与`execution/`|定义关系如何被实际执行校验，不能只读一个JSON推断全部兼容性|
|模块盖/夹爪、温度/震荡、等待状态|`protocol_api/module_contexts.py`、`protocol_engine/commands/`与`hardware_control/modules/`|前置条件、状态转换、等待与停止的区别|
|参数/CSV、暂停及界面提示|`protocol_api/`按参数或CSV方法搜索；确为执行服务/显示问题时查`robot-server/robot_server/`、`app/src/`|区分协议计算、运行服务与UI显示，不因显示问题修改实验逻辑|
|行为边界、疑似回归、某种异常是否有覆盖|`api/tests/opentrons/protocol_api/`、`protocol_engine/`、`hardware_control/`，按方法/错误名搜索对应测试|用测试理解覆盖条件；测试存在不等于当前配置或实机已验证|

表内简写`protocol_api/`、`protocol_engine/`、`hardware_control/`均相对`api/src/opentrons/`。先公开契约，再状态/命令，再硬件层；不要求每个问题都读到底层。必要时查目标发布记录或官方issue/PR定位变化，讨论和未合并补丁不能直接当已发布行为。

只保留与问题相关的证据：来源、版本、适用条件、结论及不确定项。查到新接口/参数或安装关系时报告可补充项，按维护流程核对收录后再用于生成；不静默写回技能，不直接覆盖经验默认。版本不明或证据冲突时明确缺口。结论足够即停止，不扩展为全仓库解读。

## 版本与追溯

技能规则版本、协议API版本、机器人软件版本、耗材定义版本及JSON schema版本分别记录，不互相替代。维护API基线与目标选择唯一查api-versions.md，文档基线不是新建实机协议的自动目标。

已有快照的追溯精度不同：有的保存提交号或blob SHA，有的仅记录日期/API基线。不能声称整个资料库已固定到同一官方提交，也不得倒填未实际核对的来源。历史缺口仅在相关资料下一次更新时补齐，不为补元数据无差别重查全库。

每次实际更新在对应文件/现有JSON来源字段中记录：官方路径或URL、实际读取的发布tag与解析后commit（或内容blob/hash）、核对日期、适用API/软件/定义版本和覆盖范围。流动的edge/main URL仅作导航，不能单独证明旧快照内容；无精确版本依据时标明未固定或待确认。来源信息在条目所属文件唯一维护，本表只做索引。

## 最小更新流程

1. 明确更新对象和目标版本。用户只要求检查更新时，先报告差异，不把它当作替换基线的授权；明确要求升级时直接推进已授权范围。
2. 仅获取受影响官方文件，保留更新前快照；先比较新增/删除接口、参数默认、行为、定义字段与兼容关系，不直接用新文件覆盖维护资料。
3. 区分官方事实与项目覆盖。保留用户流速覆盖和经验规则；新硬限制与经验冲突时明确指出，不静默选择，也不因为上游新增功能就加入默认实验流程。
4. 同步受影响的API、版本边界、安装关系、参数表及模板；没有相关变化的文件不改。耗材定义改变时核对现有协议的定位/堆叠影响，不静默升级既有协议。
5. 按变化范围检查：文档/来源变更检查链接和一致性；数值变更验证查询及插值边界；动作/状态变化补充或运行相关回归并核对理由。格式、案例结构、框架审查、官方模拟的结果分别报告，不互相冒充。
6. 通过对应检查后提高技能规则版本，保留Git提交以便回退。交付明确改变内容、基线是否变化及未决项；发布仓库同步经过核对的技能文件，保留仓库自身说明和其他独立修改。

目前仅提供耗材离线索引重建及单份定义获取工具，不提供自动升级API/安装关系或合并全库的脚本。维护拉取先进入暂存区并核对差异；不可安装即联网、追随开发分支或自动覆盖经验规则。
