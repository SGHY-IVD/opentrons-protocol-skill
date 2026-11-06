# 甲板可视化

把本次已有的布局回显转换成 SVG。输入只描述要显示的内容。槽位、夹具、模块与叠放关系均沿用本次流程的结论。

在宿主确认支持内嵌本地 SVG 或含 SVG 的 HTML 片段时，执行本目录的 `render.py`。将精简布局 JSON 通过标准输入传入。也可传当前会话的临时 JSON 路径。工作位置选用宿主可引用的会话临时区域。同一会话重复使用同一输出路径，成功生成后用宿主的内嵌能力引用该路径。宿主要求 HTML 片段时，将输出扩展名改为 `.html`。

```bash
python3 /实际技能目录/assets/ui/deck/render.py - --output /会话临时路径/flex-deck.svg
```

该命令从标准输入读 JSON，成功时只返回输出路径。脚本读取合并的 SVG 素材文件与资产索引。素材、耗材定义和生成的图形由脚本处理，勿把图形源码贴入对话。按布局回显原流程处理宿主能力不明、缺少所需定义或渲染失败的情况。

## 布局输入

```json
{
  "title": "Flex 甲板布局",
  "mounts": {
    "left": {"asset": "pipette-8ch", "label": "8 通道 · 50 µL"},
    "right": null,
    "gripper": {"asset": "gripper", "label": "抓手"}
  },
  "slots": {
    "C1": {
      "label": "热震荡 · 适配器 · 深孔板",
      "layers": [
        {"asset": "heaterShakerModuleV1"},
        {"asset": "opentrons_96_deep_well_adapter"},
        {"definition": "/已选耗材定义的绝对路径.json", "wells": {"A1": "sample"}}
      ]
    },
    "D2": {"state": "empty"}
  },
  "liquids": {
    "sample": {"label": "样本", "color": "#006CFA", "locations": "C1 的 A1 孔"}
  }
}
```

- `slots` 按槽位给出简短 `label`，`layers` 按自下而上列图形。夹具会影响底图时，通过 `fixture` 指定已核对的夹具 ID，例如 `stagingAreaRightSlot`。明确空位用 `state: "empty"`，未安装用 `"unavailable"`，未说明用 `"unknown"` 或省略工作区槽位。回显中第 4 列的待确认格显式传 `"unknown"`。跨槽模块只在加载锚点画一次，其余占用格用 `label` 标明。
- 图形 `asset` 使用 [资产索引](assets/manifest.json) 的键。热循环开盖用 `thermocyclerModuleV2:open`。已有匹配耗材定义时传 `definition`。标准输入使用绝对路径，文件输入也接受相对于该 JSON 的路径。每层可按已知图形位置提供 `offset: [x, y]`，单位毫米。
- `mounts` 包含 `left`、`right`、`gripper`。96 通道使用一个 `both` 项。已确认未安装可显式传 `null`，未说明可省略。
- `wells` 按孔名关联 `liquids` 的键。图例名称、颜色及位置说明沿用本次回显。缺少有效定义时可用文字表格完整表达。
