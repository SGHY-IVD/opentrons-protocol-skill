"""Generation-time official liquid-class delay lookup. No network or robot actions."""
import argparse
import json
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "references" / "delay-rates.json"
ALIASES = {"水相": "water", "有机相": "organic", "甘油相": "glycerol"}
ACTIONS = {"aspirate": "aspirate", "dispense": "singleDispense", "multi_dispense": "multiDispense"}


def query(model, tip, liquid, action="aspirate", filtered=False):
    liquid = ALIASES.get(liquid, liquid)
    if action not in ACTIONS:
        raise ValueError("未支持的等待动作；不自动回退")
    data = json.loads(DATA.read_text())
    matches = [r for r in data["rules"] if
               (r["model"], r["tip_volume"], r["liquid"], r["filtered"]) ==
               (model, tip, liquid, filtered)]
    if len(matches) != 1:
        raise ValueError("等待规则缺失或重复；不回退其他型号/枪头/滤芯/液体")
    rule = matches[0]
    phases = {k: dict(v, effective_seconds=v["duration"] if v["enabled"] else 0)
              for k, v in rule["delays"][ACTIONS[action]].items()}
    return dict(model=model, tip_volume=tip, filtered=filtered, liquid=liquid,
                official_name=rule["official_name"], action=action, phases=phases,
                units="seconds", revision=data["revision"],
                provenance="official liquid class v3; delay fields only")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--tip", required=True, type=int)
    parser.add_argument("--liquid", required=True)
    parser.add_argument("--action", choices=list(ACTIONS), default="aspirate")
    parser.add_argument("--filtered", action="store_true")
    a = parser.parse_args()
    try:
        result = query(a.model, a.tip, a.liquid, a.action, a.filtered)
    except ValueError as e:
        parser.exit(2, str(e) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
