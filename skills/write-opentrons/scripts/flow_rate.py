"""Offline generation-time flow-rate lookup; not robot capacity validation."""
import argparse
import json
import math
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'references' / 'aspiration-rates.json'
ALIASES = {'水相': 'water', '有机相': 'organic', '甘油相': 'glycerol'}


def query(model, tip, liquid, volume, action='aspirate', filtered=False):
    liquid = ALIASES.get(liquid, liquid)
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError('体积必须为有限正数')
    if action == 'air_gap':
        supported = any(r['model'] == model and r['tip_volume'] == tip
                        for r in json.loads(DATA.read_text())['rules'])
        if not supported or volume > tip:
            raise ValueError('型号/枪头组合未收录或体积超过枪头容量')
        return dict(flow_rate=20, units='uL/s', method='user_default',
                    action=action, model=model, tip_volume=tip, volume=volume,
                    hardware_volume_validation='not_performed')
    path = DATA.with_name('dispense-rates.json') if action == 'dispense' else DATA
    data = json.loads(path.read_text())
    matches = [r for r in data['rules'] if
               (r['model'], r['tip_volume'], r['liquid'], r['action']) ==
               (model, tip, liquid, action) and
               (action != "dispense" or r["filtered"] == filtered)]
    if len(matches) != 1:
        raise ValueError('规则缺失或重复：不自动回退其他型号、枪头、液体或动作')
    rule = matches[0]
    points = rule['points']
    if volume > rule['max_volume'] or volume < rule['min_rule_volume']:
        raise ValueError('体积超出已维护规则范围或枪头容量；不外推')
    if len(points) == 1:
        rate = points[0][1]
        method = 'constant'
    elif volume > points[-1][0]:
        if rule['upper_endpoint'] != 'hold':
            raise ValueError('体积超过曲线覆盖范围；不外推')
        rate = points[-1][1]
        method = 'inherited_official_upper_endpoint'
    else:
        for i, (v, q) in enumerate(points):
            if volume == v:
                rate, method = q, 'exact_point'
                break
            if volume < v:
                v0, q0 = points[i-1]
                rate = q0 + (volume-v0)*(q-q0)/(v-v0)
                method = 'linear_interpolation'
                break
    return dict(flow_rate=round(rate, 6), units='uL/s', method=method,
                action=action, filtered=filtered, model=model, tip_volume=tip, liquid=liquid, volume=volume,
                provenance=rule['provenance'], revision=data['revision'],
                hardware_volume_validation='not_performed')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--model', required=True)
    p.add_argument('--tip', type=int, required=True)
    p.add_argument('--liquid', required=True)
    p.add_argument('--volume', type=float, required=True)
    p.add_argument('--action', default='aspirate')
    p.add_argument('--filtered', action='store_true', help='实际使用滤芯枪头时传入')
    a = p.parse_args()
    try:
        result = query(a.model, a.tip, a.liquid, a.volume, a.action, a.filtered)
    except ValueError as e:
        p.exit(2, str(e)+'\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
