# Flex设备连接与协议发送（按需工具）

仅在用户希望连接设备、已有可达设备信息可辅助核对配置，或交付后适合提供发送帮助时读取。不是编写protocol的前置步骤，不默认查网、安装依赖或每次提示；不可达或用户不需要时沿用原流程。已确认的设备和已有授权直接复用，不另加固定确认轮次。

## 范围与分工

- `scripts/flex_http.py`提供Python调用和命令行入口：mDNS发现或检查给定候选地址、读取Flex身份/硬件/保存的甲板配置、上传Python协议与可选耗材JSON、获取设备端分析。HTTP功能用Python标准库，只有mDNS发现需可选zeroconf依赖；不依赖本地Opentrons SDK，不写入生成的protocol。
- `discover`按需在可访问的本地网络进行短时mDNS发现，检查官方`_http._tcp.local.`服务的31950端口，再读取候选设备health核对Flex身份；不把广播名称/TXT字段直接当成已连接Flex。默认发现5秒、最多核对8个候选地址，达到预算时标记candidate_limit_reached。未发现或核对失败不代表没有设备，可手动填写IP。`probe`只检查明确给出的地址；两者都不自动选择目标或扫描网段。不把“工具存在”当成“已发现本地设备”。工具所在环境须能访问目标网络；助手环境的连通性不能冒充用户电脑的连接状态。
- 不创建run，不开始实验，不归零/移动、不改温控或甲板配置。向设备上传须有用户对目标设备及该文件的授权；已有授权直接复用。客户端上传前重读身份；提供上次读取的名称和可用序列号，避免地址变化后误选目标。
- 工具返回结构化JSON；AI按现有机头/甲板表整理展示。instruments/modules来自设备报告，saved_deck_configuration来自软件保存配置，不能当作完整实物识别。缺失/失败标未知，不能当未安装；器件的ok/compatibleWithRobot等状态、配置与实物的差异仍按原规则核对。不把校准记录中的旧位置、USB端口号或分析末态当作实际初始布局。
- HTTP结果不替代技能规则审查或本地SDK模拟。机器人返回的协议API上限仍按api-versions选择目标；HTTP接口版本与protocol的apiLevel是不同概念。

## 面向用户的提示

只在有真实工具结果、当前任务适合时自然表达，不要求逐字套用或每次出现。配置读取可以替代人工填写示例，保留现有用户核对环节；用户可能要使用另一台设备，不能自动把可连接设备当成指定设备。

有真实读取结果时，例如：

> 已连接到Flex「{设备名}」（IP：{实际IP}），目前读取到的配置如下。您看看这是不是本次要使用的设备，配置是否与实际台面一致？

已知设备可连接、交付文件及本次检查已完成时，例如：

> 是否需要把这份脚本发送到您当前连接的Flex「{设备名}」（IP：{实际IP}）？我也可以帮您查看设备端的分析结果。

括号内容取真实结果；只有主机名时写“地址”，不猜IP。不确定运行位置是否为用户本机时，不使用“您本地已连接”；不要向用户复述这些内部判断规则。没有连接结果时可按需提出连接帮助，不用上述“已连接”措辞。上传成功、分析待完成、分析有错误分别回显；不得将上传或分析完成说成实验已启动。

## 调用

以下地址、名称、序列号、ID及文件名都是示例，执行时换成已核对值。命令相对技能根目录；不把示例IP作为真实设备地址。

```bash
python3 scripts/flex_http.py discover --seconds 5
python3 scripts/flex_http.py probe 192.0.2.10 flex.local
python3 scripts/flex_http.py inspect --host 192.0.2.10
python3 scripts/flex_http.py upload protocol.py --host 192.0.2.10 --expected-name "Flex A" --expected-serial "实际序列号" --confirm-upload
python3 scripts/flex_http.py analysis --host 192.0.2.10 --protocol-id "实际协议ID" --analysis-id "实际分析ID" --wait-seconds 20
```

- Python入口：`FlexHTTPClient(host).inspect()`、`upload_protocol(path, expected_name=..., expected_serial=..., confirmed=True)`、`analysis(protocol_id, analysis_id, wait_seconds=...)`；`discover_devices()`短时发现，`probe_devices(hosts)`检查候选地址。没有导入/后台发现副作用。
- mDNS缺少依赖时明确报告，可在用户同意后为对应环境安装`python3 -m pip install -r scripts/requirements-flex-http-mdns.txt`，不由工具自行安装。该固定依赖版要求Python≥3.10；本次工具测试使用Python3.12。已连接设备可直接用inspect/upload，无需先发现。mDNS可能受网卡、组播/VLAN或宿主网络限制；第一版按官方客户端做IPv4发现，IPv6/HTTPS设备可使用明确的完整地址。访问控制导致health未通过时保留候选和错误，不以此断言设备未连接或不属于Flex。
- 上传支持重复`--labware file.json`。有非默认标量运行参数时用`--parameter-values`传JSON对象，键/值按本次协议实际定义；省略时由设备采用默认值，不暗指所有分支均已分析。本版不管理CSV数据文件上传；设备若返回parameter-value-required，报告缺少输入，不记通过。
- 使用上传结果的protocol_id和analysis_id查询；工具检查分析归属。分析仅在completed、result=ok且errors为空时给passed=true；pending、parameter-value-required和not-ok均不能当通过。查询保留设备实际run_time_parameters。返回的ok=true只表示工具取得了结果，不等于分析通过。
- `--wait-seconds`最多30秒，未结束仍返回pending，可稍后再查；`--timeout`控制每次网络请求超时。POST不自动重试；超时/异常且upload_may_have_succeeded=true时，先核对设备记录，不能直接重复上传。已确认上传后即使分析查询失败，也保留上传得到的ID与文件SHA256，分别报告。
- 支持明确HTTP/HTTPS地址及可选`--ca-file`。已有访问令牌由环境变量`OPENTRONS_HTTP_TOKEN`提供，仅用于HTTPS；不在命令、文案或协议中放令牌。工具不负责登录、关闭访问控制或修改账号。HTTP默认端口31950；HTTPS使用实际部署地址和端口，不猜配置。
- stdout为JSON，操作失败退出1，参数用法错误退出2。inspect的partial只表示部分接口未读取成功，不代表台面空；读取成功也始终保留physical_layout_confirmed=false，直到用户按原流程核对。工具不保存或自动应用硬件档案。

## 契约与来源

2026-10-29首批核对：官方Opentrons/opentrons **v10.0.0**，commit `e8c6d0a424c25fff1604e2a02e4ccaedac95b9af`；HTTP请求固定`Opentrons-Version: 4`，不使用`*`。该发布versioning.py定义当前4、最低2；本工具只维护下列小范围，未扩展Python API 2.30基线。其他设备软件的兼容性不由本次测试自动证明；保留实读软件版本，版本/响应不匹配时报告，不能静默改用旧接口。

|方法与路径|用途与实际读取来源（均为robot-server/robot_server/下）|blob SHA|
|---|---|---|
|GET /health|health/models.py：名称、型号、序列号及版本；router.py实际响应另核对|ce157c8c9645b50402daeccd2314353de2a13acc；54c5e5312bde3fb60fce88095589c8292963df1d|
|GET /instruments|instruments/router.py；instrument_models.py：移液器、抓手、异常器件|832c9581e93f8c7fe716aee5721f4fcafb4b3c4f；25f575e0b3a089585fc361b777d0e1185415896f|
|GET /modules|modules/router.py；module_models.py：连接模块及兼容/校准字段|09f945cc5a37e5d259fed7950115f38b39813e6f；9b6ba629c28df4e33eafb50e9e15a4ef5a4903e9|
|GET /deck_configuration|deck_configuration/router.py：已保存夹具配置|56b1b82e7ec058218925838c2a7011399b50cd5d|
|POST /protocols；GET /protocols/{id}；GET /protocols/{id}/analyses/{analysisId}|protocols/router.py：重复files表单、自动分析和关联查询；protocol_models.py、analysis_models.py定义响应|e22871187583996acbb78532785a63ff1c855bf3；4e47b14606e87e6f95588f78d988982e79f9d2b7；96b97797249b2dd049ee9c6df4fca599b062bc4d|
|HTTP版本与Flex身份|versioning.py；shared-data/python/opentrons_shared_data/robot/types.py：Flex内部标识OT-3 Standard|d49ccbac75748b367e02b9919ba0b3a2891a3f4d；bc23815fba45d69513414d744a2e3f7808fd90a0|

发现行为另核对同一commit的discovery-client/src/mdns-browser/index.ts（blob d4a9edec1667904dd1584fc415a031d894fd052e）、discovery-client/src/mdns-browser/base-browser.ts（cac2bc7395531e0705c1851b6b8d721612239418）及discovery-client/src/constants.ts（306bcfc0250a9e03bb4fa42ead17133946d410e6）：浏览HTTP服务、按31950筛选并核对health。mDNS使用外部[python-zeroconf](https://python-zeroconf.readthedocs.io/en/latest/api.html)，依赖版固定0.151.5，按其ServiceBrowser/Zeroconf/ServiceInfo公开接口使用；同步入口采用use_asyncio=False使其使用独立循环，避免Jupyter/已有asyncio循环中漏发现。不复制或打包依赖源码；其许可为LGPL-2.1-or-later。

官方[集成示例](https://github.com/Opentrons/opentrons-integration-tools/tree/a4b9aad0166091eae985c757c479bb1cd73a0fbb/http-api)用于核对上传/分析流程（该commit的http-api/README.md blob为d7d7adcf1019deded2226aa0c04f5215ac7b1d06），示例不是通用SDK；未整包引入。此前检查的官方flex-testing-agent为带数据库等依赖的设备测试框架，也未作为运行依赖。这里的工具为独立实现；不复制示例中的其他机器人内容或控制命令。

维护备注：上传可能触发服务器自身的协议保留/清理策略；工具不另外删除记录。v10.0.0分析详情路由有未严格核对协议归属的源码备注，客户端因此先核对protocol.analysisSummaries。验证仅覆盖本次离线契约/本地替身服务检查，未作实机连接、真实上传或设备端分析验证；不能据此称为官方成熟SDK或所有Flex版本已验证。
