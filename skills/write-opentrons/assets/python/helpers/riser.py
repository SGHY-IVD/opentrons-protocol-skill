"""普通台面叠放板的虚拟库存：SDK 仅登记当前顶部的一块板。

Source SHA-256: ed4697668b4bf98b7032dc91631d1ca9fc9b3ba8ec9afaafc9fb033592628780

这不是官方 Flex Stacker 或 ``opentrons_flex_deck_riser``，SDK 不掌握
整叠实物的几何与碰撞关系。层间距必须为有限正数；底座高度必须为有限非负数。
搬运或重新登记异常后停止继续取板，须先核对实物及协议状态。
"""

import math
from collections.abc import Mapping
from numbers import Integral, Real


class RiserStateError(RuntimeError):
    """当前库存状态不允许继续搬运。"""


def _riser_finite_real(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} 必须是有限实数")
    try:
        result = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{name} 必须是有限实数") from exc
    if not math.isfinite(result):
        raise ValueError(f"{name} 必须是有限实数")
    return result


def _riser_stack_offset(quantity, pitch, base):
    try:
        result = base + max(0, quantity - 1) * pitch
    except OverflowError as exc:
        raise ValueError("堆叠顶部的取板高度必须有限") from exc
    if not math.isfinite(result):
        raise ValueError("堆叠顶部的取板高度必须有限")
    return result


class Riser:
    """在普通台面位置登记顶部板，逐块搬运并登记下一块。

    ``quantity=0`` 时不加载耗材。取板偏移为
    ``riser_base_height_mm + (quantity - 1) * stack_height_mm``，X/Y 为零。
    构造参数及初始取板高度会在首次加载前完成校验。
    """

    def __init__(
        self, protocol, slot_name, load_name, quantity, stack_height_mm,
        riser_base_height_mm=0,
    ):
        if not isinstance(slot_name, str) or not slot_name.strip():
            raise ValueError("slot_name 必须是非空字符串")
        if not isinstance(load_name, str) or not load_name.strip():
            raise ValueError("load_name 必须是非空字符串")
        if isinstance(quantity, bool) or not isinstance(quantity, Integral) or quantity < 0:
            raise ValueError("quantity 必须是非负整数")
        quantity = int(quantity)
        pitch = _riser_finite_real(stack_height_mm, "stack_height_mm")
        base = _riser_finite_real(riser_base_height_mm, "riser_base_height_mm")
        if pitch <= 0:
            raise ValueError("stack_height_mm 必须大于零")
        if base < 0:
            raise ValueError("riser_base_height_mm 不能小于零")
        _riser_stack_offset(quantity, pitch, base)

        self.ctx = protocol
        self.slot = slot_name
        self.load_name = load_name
        self.stack_height = pitch
        self.base_height = base
        self._quantity = quantity
        self._current_labware = None
        self._last_moved_labware = None
        self._faulted = False
        if self._quantity:
            self._current_labware = self._load_current()

    @property
    def quantity(self):
        """尚未搬出的板数。"""
        return self._quantity

    @property
    def current_labware(self):
        """当前顶部板的原生 Labware 对象；无可用登记时为 None。"""
        return self._current_labware

    @property
    def last_moved_labware(self):
        """最近一次搬运调用成功返回的原生 Labware 对象。"""
        return self._last_moved_labware

    @property
    def faulted(self):
        """搬运或重新登记曾发生异常，后续取板已被阻止。"""
        return self._faulted

    def _load_current(self):
        return self.ctx.load_labware(
            self.load_name, self.slot, label=f"堆叠板（剩余 {self._quantity} 块）"
        )

    def move_next_to(self, target_location, *, drop_offset=None):
        """将顶部板搬到 SDK 支持的目标，返回该原生 Labware 对象。

        ``drop_offset`` 可按实际目标标定提供 x/y/z，缺省轴为零。
        搬运异常保留原库存记录；搬运成功后的重载异常保留已扣减库存和
        已搬出的对象，同时清空顶部登记。两种异常均原样抛出并锁定后续取板。
        """
        if self._faulted:
            raise RiserStateError("堆叠搬运状态异常，请先核对实物及协议状态")
        if self._quantity <= 0:
            raise RiserStateError("堆叠板已取完")
        if self._current_labware is None:
            raise RiserStateError("当前顶部板尚未登记，不能搬运")
        if isinstance(target_location, str) and (
            target_location.strip().casefold() == self.slot.strip().casefold()
        ):
            raise ValueError("目标位置不能与堆叠源位置相同")
        if drop_offset is None:
            normalized_drop = {"x": 0.0, "y": 0.0, "z": 0.0}
        else:
            if not isinstance(drop_offset, Mapping) or any(
                axis not in ("x", "y", "z") for axis in drop_offset
            ):
                raise ValueError("drop_offset 必须是仅含 x/y/z 的映射")
            normalized_drop = {
                axis: _riser_finite_real(drop_offset.get(axis, 0), f"drop_offset[{axis}]")
                for axis in ("x", "y", "z")
            }
        pick_up_z = _riser_stack_offset(self._quantity, self.stack_height, self.base_height)
        moved_labware = self._current_labware
        self.ctx.comment(f"正在搬运堆叠顶部板，本次搬运前剩余 {self._quantity} 块。")
        try:
            self.ctx.move_labware(
                labware=moved_labware,
                new_location=target_location,
                use_gripper=True,
                pick_up_offset={"x": 0, "y": 0, "z": pick_up_z},
                drop_offset=normalized_drop,
            )
        except BaseException:
            self._faulted = True
            raise

        self._last_moved_labware = moved_labware
        self._quantity -= 1
        self._current_labware = None
        if self._quantity:
            try:
                self._current_labware = self._load_current()
            except BaseException:
                self._faulted = True
                raise
        return moved_labware
