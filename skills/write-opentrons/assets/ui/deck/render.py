#!/usr/bin/env python3
"""Render a confirmed Flex layout as a self-contained SVG."""

import argparse
import json
import math
import os
import re
import sys
import tempfile
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
INK = "#16212D"
MUTED = "#58646F"
RULE = "#DCE1E5"
TIP_COLORS = {
    "opentrons_flex_96_tiprack_20ul": "#F4BB80",
    "opentrons_flex_96_tiprack_50ul": "#CDA4D8",
    "opentrons_flex_96_tiprack_200ul": "#C8DC9A",
    "opentrons_flex_96_tiprack_1000ul": "#99E4FF",
}
STATUSES = {"unknown": "未说明", "empty": "空", "unavailable": "未安装", "occupied": "已占用"}
WIDTH = 1000
PAD = 24
DECK_WIDTH = 720


def svg(parent, tag, **attributes):
    return ET.SubElement(parent, f"{{{SVG}}}{tag}", {
        key.replace("_", "-"): str(value) for key, value in attributes.items()
    })


def read_json(path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("SVG 坐标或尺寸须为有限数字")
    return value


def positive(value):
    value = number(value)
    if value <= 0:
        raise ValueError("耗材尺寸须大于零")
    return value


def color(value):
    if not isinstance(value, str) or not re.fullmatch(r"#[\da-fA-F]{6}", value):
        raise ValueError("液体颜色须采用 #RRGGBB 格式")
    return value


def translate(x, y):
    return f"translate({number(x):g} {number(y):g})"


def words(parent, content, x, y, size=18, *, fill=INK, anchor="start"):
    node = svg(parent, "text", x=x, y=y, font_size=size, fill=fill, text_anchor=anchor)
    node.text = str(content)
    return node


def wrapped(content, capacity):
    lines = []
    for paragraph in str(content).splitlines() or [""]:
        row, length = "", 0
        for char in paragraph:
            width = 2 if unicodedata.east_asian_width(char) in {"W", "F"} else 1
            if row and length + width > capacity:
                lines.append(row.rstrip())
                row, length = "", 0
            if row or not char.isspace():
                row += char
                length += width
        lines.append(row.rstrip())
    return lines


class Artwork:
    def __init__(self, defs, root):
        self.defs = defs
        self.manifest = read_json(root / "manifest.json")
        sprite = ET.parse(root / "artwork.svg").getroot()
        self.images = {image.attrib["data-asset"]: image for image in sprite.find(f"{{{SVG}}}defs")}
        self.definitions = {}

    def get(self, category, name, slot=""):
        entries = self.manifest[category]
        variants = {
            "modules": "left" if slot.endswith("1") else "right",
            "fixtures": {"1": "left", "2": "center"}.get(slot[-1:], "right"),
        }
        variant = f"{name}:{variants[category]}" if category in variants else name
        record = entries.get(variant, entries.get(name))
        if record is None:
            raise ValueError(f"缺少可用的图形资产 {name}")
        return {"file": record} if isinstance(record, str) else record

    def place(self, parent, record, x=0, y=0, *, size=None):
        path = record["file"]
        if path not in self.definitions:
            image = self.images[path]
            asset_id = f"flex-art-{len(self.definitions) + 1}"
            self.definitions[path] = asset_id
            id_map = {
                node.get("id"): f"{asset_id}-{node.get('id')}"
                for node in image.iter() if node.get("id") is not None
            }
            for node in image.iter():
                if node.tag.rsplit("}", 1)[-1] in {"foreignObject", "script", "image"}:
                    raise ValueError("图形资产包含不支持的嵌入内容")
                for attribute, value in list(node.attrib.items()):
                    if attribute == "id":
                        value = id_map[value]
                    elif attribute.rsplit("}", 1)[-1] == "href":
                        if not value.startswith("#"):
                            raise ValueError("图形资产包含外部引用")
                        value = f"#{id_map.get(value[1:], value[1:])}"
                    else:
                        value = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{id_map.get(m[1], m[1])})", value)
                    node.set(attribute, value)
            if size:
                container = svg(self.defs, "symbol", id=asset_id, viewBox=image.attrib["viewBox"])
            else:
                container = svg(self.defs, "g", id=asset_id)
            container.extend(image)
        attrs = {"href": f"#{self.definitions[path]}"}
        if size:
            attrs.update(x=x, y=y, width=size[0], height=size[1])
        else:
            attrs["transform"] = translate(x, y)
        svg(parent, "use", **attrs)


def labware_geometry(definition):
    if "dimensions" in definition:
        dims = definition["dimensions"]
        width, height = positive(dims["xDimension"]), positive(dims["yDimension"])
        offset = definition.get("cornerOffsetFromSlot", {})
        return (0, 0, width, height), (number(offset.get("x", 0)), number(offset.get("y", 0)))
    bounds = definition["extents"]["total"]
    back = bounds["backLeftBottom"]
    front = bounds["frontRightTop"]
    left, bottom = number(back["x"]), number(front["y"])
    width = positive(number(front["x"]) - left)
    height = positive(number(back["y"]) - bottom)
    foot = definition.get("features", {}).get("slotFootprintAsChild", {}).get("backLeft", back)
    return (left, bottom, width, height), (-number(foot["x"]), 86 - number(foot["y"]))


def draw_labware(parent, definition, fills, base, centered=False):
    (left, bottom, width, height), (dx, dy) = labware_geometry(definition)
    if centered:
        dx, dy = (128 - width) / 2 - left, (86 - height) / 2 - bottom
    group = svg(parent, "g", transform=translate(base[0] + dx, base[1] + dy))
    wells = definition.get("wells", {})
    if set(fills) - wells.keys():
        raise ValueError("液体标记含定义中不存在的孔位")
    parameters = definition.get("parameters", {})
    is_tiprack = parameters.get("isTiprack", False)
    tip_model = parameters.get("loadName", "").replace("_filtertiprack_", "_tiprack_")
    outline_fill = TIP_COLORS.get(tip_model, "#DCE4E9") if is_tiprack else "#FFFFFF"
    svg(group, "rect", x=left, y=bottom, width=width, height=height, rx=min(4, width / 4, height / 4),
        fill=outline_fill, stroke=INK, stroke_width=1.3)
    for name, well in wells.items():
        x, y = number(well["x"]), number(well["y"])
        attributes = {"data_well": name, "stroke": "#82909A" if is_tiprack else INK,
                      "stroke_width": 0.55, "fill": fills.get(name, "#FFFFFF")}
        if well["shape"] == "circular":
            svg(group, "circle", cx=x, cy=y, r=positive(well["diameter"]) / 2, **attributes)
        elif well["shape"] == "rectangular":
            w, h = positive(well["xDimension"]), positive(well["yDimension"])
            svg(group, "rect", x=x - w / 2, y=y - h / 2, width=w, height=h, **attributes)
        else:
            raise ValueError(f"图形不支持孔位 {name} 的形状")


def draw_stack(parent, art, slot, layers, liquids, input_dir):
    child_x, child_y = 0, 0
    centered = False
    for layer in layers:
        dx, dy = layer.get("offset", [0, 0])
        x, y = child_x + number(dx), child_y + number(dy)
        if "asset" in layer:
            if layer.get("wells"):
                raise ValueError("需要孔位标记的耗材须提供定义 JSON")
            asset = layer["asset"]
            is_module = asset in art.manifest["modules"]
            category = "modules" if is_module else "adapters"
            record = art.get(category, asset, slot)
            art.place(parent, record, x, y)
            extra_x, extra_y = record.get("childOffset", [0, 0])
            child_x, child_y = x + extra_x, y + extra_y
            centered = True
        else:
            definition = read_json(input_dir / layer["definition"])
            fills = {well: color(liquids[liquid]["color"]) for well, liquid in layer.get("wells", {}).items()}
            draw_labware(parent, definition, fills, (x, y), centered)


def draw_mounts(root, art, mounts, x, y):
    words(root, "挂载配置", x, y, 22)
    keys = [("both", "左右挂载")] if mounts.get("both") else [("left", "左挂载"), ("right", "右挂载")]
    keys.append(("gripper", "扩展挂载"))
    for key, caption in keys:
        y += 44
        value = mounts.get(key)
        words(root, caption, x + 65, y, 17, fill=MUTED)
        if isinstance(value, dict):
            name = value["asset"]
            art.place(root, art.get("instruments", name), x, y - 26, size=(60, 68))
            label = value.get("label", {"gripper": "抓手", "pipette-96ch": "96 通道移液器"}.get(name, name))
        else:
            label = "未安装" if key in mounts and value is None else "未说明"
        for index, line in enumerate(wrapped(label, 19)):
            words(root, line, x + 65, y + 23 + index * 20, 17)
        y += 60
    return y


def draw_table(root, entries, columns, y):
    cell_width = (WIDTH - PAD * 2) / columns
    capacity = int((cell_width - 26) / 9.5)
    for start in range(0, len(entries), columns):
        row = entries[start:start + columns]
        lines = [wrapped(detail, capacity) if detail else [] for _, detail, _ in row]
        height = 35 + 21 * max(1, max(map(len, lines)))
        for column, ((title, _, fill), labels) in enumerate(zip(row, lines)):
            x = PAD + column * cell_width
            svg(root, "rect", x=x, y=y, width=cell_width, height=height, fill="none", stroke=RULE)
            if fill:
                svg(root, "circle", cx=x + 18, cy=y + 19, r=6, fill=fill)
            words(root, title, x + (31 if fill else 12), y + 25, 18)
            for index, label in enumerate(labels):
                words(root, label, x + 12, y + 47 + 21 * index, 16, fill=MUTED)
        y += height
    return y


def render(layout, input_dir, asset_dir, *, html=False):
    title = layout.get("title", "Flex 甲板布局")
    root = ET.Element(f"{{{SVG}}}svg", {"role": "img", "font-family": "system-ui,sans-serif"})
    svg(root, "title").text = title
    background = svg(root, "rect", x=0, y=0, width=WIDTH, fill="#FFFFFF", rx=10)
    definitions = svg(root, "defs")
    art = Artwork(definitions, asset_dir)
    if "style" in art.manifest:
        svg(root, "style").text = (asset_dir / art.manifest["style"]).read_text(encoding="utf-8")
    positions = art.manifest["slots"]
    slots = layout.get("slots", {})
    if set(slots) - positions.keys():
        raise ValueError("存在无法绘制的 Flex 槽位")
    liquids = layout.get("liquids", {})
    mounts = layout.get("mounts", {})
    view_x, view_y, view_width, view_height = art.manifest["viewBox"]
    flip = art.manifest["flipY"]
    layer_assets = {layer.get("asset") for data in slots.values() for layer in data.get("layers", [])}
    if "flexStackerModuleV1" in layer_assets:
        view_width += 220
    scale = DECK_WIDTH / view_width
    deck_top = 67
    screen_x = PAD - scale * view_x
    screen_y = deck_top - scale * view_y
    words(root, title, PAD, 39, 28)
    deck = svg(root, "g", transform=f"{translate(screen_x, screen_y)} scale({scale:g})")
    world = svg(deck, "g", transform=f"translate(0 {flip:g}) scale(1 -1)")

    fourth = {slot for slot, item in slots.items() if slot.endswith("4") and item.get("state") != "unavailable"}
    fixture_positions = []
    for slot, (x, y) in positions.items():
        if slot.endswith("4"):
            continue
        data = slots.get(slot, {})
        column = int(slot[1])
        default_fixture = ["singleLeftSlot", "singleCenterSlot", "singleRightSlot"][column - 1]
        fixture_name = data.get("fixture", default_fixture)
        if fixture_name in art.manifest["modules"] and fixture_name not in art.manifest["fixtures"]:
            fixture_name = default_fixture
        fixture = art.get("fixtures", fixture_name, slot)
        fixture_positions.append((fixture, x, y))
        if fixture.get("expands"):
            fourth.add(slot[0] + "4")
    canvas = art.manifest.get("canvas")
    if canvas and (fourth or "thermocyclerModuleV2:open" in layer_assets):
        art.place(world, {"file": canvas})
    for fixture, x, y in fixture_positions:
        art.place(world, fixture, x, y)

    for slot, data in slots.items():
        if not data.get("layers"):
            continue
        group = svg(world, "g", transform=translate(*positions[slot]), data_slot=slot)
        svg(group, "title").text = data.get("label", slot)
        draw_stack(group, art, slot, data["layers"], liquids, input_dir)

    for row in "ABCD":
        words(deck, row, -139, flip - positions[row + "1"][1] - 36, 22, anchor="middle")
    columns = 4 if fourth or any(slot.endswith("4") for slot in slots) else 3
    for index in range(1, columns + 1):
        words(deck, index, positions[f"D{index}"][0] + 64, 526, 22, anchor="middle")
    for slot, (x, y) in positions.items():
        if slot.endswith("4") and slot not in fourth:
            continue
        data = slots.get(slot, {})
        if data.get("state", "unknown") == "unknown" and not (data.get("layers") or data.get("label")):
            words(deck, "未说明", x + 64, flip - y - 36, 16, fill=MUTED, anchor="middle")

    mount_bottom = draw_mounts(root, art, mounts, PAD + DECK_WIDTH + 26, deck_top + 30)
    y = max(deck_top + view_height * scale, mount_bottom) + 22
    words(root, "槽位配置", PAD, y, 23)
    if columns == 4:
        words(root, "第 4 列 · 扩展位", WIDTH - PAD, y, 16, fill=MUTED, anchor="end")
    entries = []
    for row in "ABCD":
        for column in range(1, columns + 1):
            slot = row + str(column)
            data = slots.get(slot, {})
            state = data.get("state", "occupied" if data.get("layers") else "unknown")
            entries.append((slot, data.get("label") or STATUSES[state], None))
    y = draw_table(root, entries, columns, y + 12)
    if liquids:
        y += 38
        words(root, "液体标签", PAD, y, 23)
        entries = [(item.get("label", name), item.get("locations", ""), color(item["color"]))
                   for name, item in liquids.items()]
        y = draw_table(root, entries, 3, y + 12)
    height = math.ceil(y + PAD)
    root.set("viewBox", f"0 0 {WIDTH} {height}")
    root.set("width", str(WIDTH))
    root.set("height", str(height))
    background.set("height", str(height))
    if html:
        root.set("style", "display:block;width:100%;height:auto")
        return b'<figure style="margin:0">' + ET.tostring(root, encoding="utf-8") + b"</figure>\n"
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", help="布局 JSON 路径，或用 - 从标准输入读入")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    input_path = None if args.layout == "-" else Path(args.layout).resolve()
    if output == input_path or output.suffix.lower() not in {".svg", ".html"}:
        parser.error("--output 须为单独的 SVG 或 HTML 路径")
    asset_dir = Path(__file__).resolve().parent / "assets"
    try:
        layout = read_json(input_path) if input_path else json.load(sys.stdin)
        content = render(layout, input_path.parent if input_path else Path.cwd(), asset_dir,
                         html=output.suffix.lower() == ".html")
        tmp = None
        try:
            with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".tmp", delete=False) as handle:
                tmp = Path(handle.name)
                handle.write(content)
            os.replace(tmp, output)
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)
    except (AttributeError, KeyError, TypeError, ValueError, OSError, ET.ParseError) as exc:
        print(f"甲板图生成失败：{exc}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
