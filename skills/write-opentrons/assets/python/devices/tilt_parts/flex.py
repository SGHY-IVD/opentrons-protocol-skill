"""Minimal Flex loading and geometric views for the third-party tilt device.

This is a facade over ordinary deck labware, not an Opentrons ModuleContext.
The SDK does not know the third-party module's occupied volume or moving shape.
All placement and rotation values must be measured for the actual installation.
No pipette path, collision detection, washing workflow, or safety interlock is
provided. Callers must clear instruments and the gripper before module movement.

Importing or constructing these classes never opens USB. Simulation is an
in-memory device model only; it does not validate hardware or robot clearances.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Protocol

from .device import (
    STATE_NAMES,
    TiltConnectionInfo,
    TiltDevice,
    TiltGeometry,
    TiltOutOfRangeError,
    TiltStateError,
    TiltStatus,
)

if TYPE_CHECKING:
    from opentrons.protocol_api import Labware, ProtocolContext, Well
    from opentrons.types import Location, Point


@dataclass(frozen=True)
class TiltFlexConfig:
    """Explicit placement calibration plus source-derived communication defaults.

    Required geometry values have no guessed defaults. ``module_height_mm`` is
    the level plate translation relative to SDK deck labware coordinates. The
    axis model is the source's translation followed by a rotation about Y.
    ``geometry_angle_sign`` maps the device angle to that rotation convention.
    Gripper Z offsets are separately measured offsets relative to a bare-slot
    move; they are required only when that corresponding gripper move is used.
    Limits and timing defaults come from supplied source, not vendor approval.
    """

    location: str
    module_height_mm: float
    axis_to_plate_bottom_mm: float
    plate_bottom_to_well_bottom_mm: float
    geometry_angle_sign: float

    usb_bus: Optional[int] = None
    usb_address: Optional[int] = None
    usb_port_numbers: Optional[tuple[int, ...]] = None
    hardware_enabled: bool = True
    default_speed_deg_s: float = 2.0
    max_angle_deg: float = 30.0
    max_speed_deg_s: float = 30.0
    response_timeout_s: float = 5.0
    home_timeout_s: float = 45.0
    motion_timeout_margin_s: float = 5.0
    angle_tolerance_deg: float = 0.15
    completion_verify_timeout_s: float = 2.0
    completion_poll_interval_s: float = 0.05
    level_tolerance_deg: float = 0.25
    require_homed: bool = True
    module_offset_x_mm: float = 0.0
    module_offset_y_mm: float = 0.0
    geometry_angle_offset_deg: float = 0.0
    gripper_drop_x_mm: float = 0.0
    gripper_drop_y_mm: float = 0.0
    gripper_drop_z_mm: Optional[float] = None
    gripper_pick_up_x_mm: float = 0.0
    gripper_pick_up_y_mm: float = 0.0
    gripper_pick_up_z_mm: Optional[float] = None

    def validate(self) -> None:
        if not isinstance(self.location, str) or not self.location.strip():
            raise ValueError("location 必须为非空的实际台面位置")
        positive = (
            "module_height_mm", "default_speed_deg_s", "max_angle_deg",
            "max_speed_deg_s", "response_timeout_s", "home_timeout_s",
            "angle_tolerance_deg", "completion_verify_timeout_s",
            "completion_poll_interval_s", "level_tolerance_deg",
        )
        non_negative = (
            "axis_to_plate_bottom_mm", "plate_bottom_to_well_bottom_mm",
            "motion_timeout_margin_s",
        )
        finite = (
            "module_offset_x_mm", "module_offset_y_mm",
            "geometry_angle_offset_deg", "gripper_drop_x_mm",
            "gripper_drop_y_mm", "gripper_pick_up_x_mm",
            "gripper_pick_up_y_mm",
        )
        for name in positive + non_negative + finite:
            value = getattr(self, name)
            if not math.isfinite(value):
                raise ValueError(f"{name} 必须为有限数")
            if name in positive and value <= 0:
                raise ValueError(f"{name} 必须大于 0")
            if name in non_negative and value < 0:
                raise ValueError(f"{name} 不能为负数")
        if self.max_angle_deg > 30 or self.max_speed_deg_s > 30:
            raise ValueError("源码限制：最大角度及最大速度均不得超过 30")
        if self.default_speed_deg_s > self.max_speed_deg_s:
            raise ValueError("default_speed_deg_s 不能超过 max_speed_deg_s")
        if self.geometry_angle_sign not in {-1.0, 1.0}:
            raise ValueError("geometry_angle_sign 必须为 -1.0 或 1.0")
        for name in ("gripper_drop_z_mm", "gripper_pick_up_z_mm"):
            value = getattr(self, name)
            if value is not None and not math.isfinite(value):
                raise ValueError(f"{name} 必须为有限数或 None")

    def gripper_drop_offset(self) -> Dict[str, float]:
        if self.gripper_drop_z_mm is None:
            raise ValueError("抓手放板前必须显式配置实测 gripper_drop_z_mm")
        return {
            "x": self.gripper_drop_x_mm,
            "y": self.gripper_drop_y_mm,
            "z": self.gripper_drop_z_mm,
        }

    def gripper_pick_up_offset(self) -> Dict[str, float]:
        if self.gripper_pick_up_z_mm is None:
            raise ValueError("抓手取板前必须显式配置实测 gripper_pick_up_z_mm")
        return {
            "x": self.gripper_pick_up_x_mm,
            "y": self.gripper_pick_up_y_mm,
            "z": self.gripper_pick_up_z_mm,
        }


@dataclass(frozen=True)
class TiltPose:
    """Cached pose; angles must not be used for coordinates unless valid."""

    hardware_angle_deg: float
    geometry_angle_deg: float
    valid: bool
    revision: int


class TiltHardwareBackend(Protocol):
    """Device interface shared by real USB and in-memory simulation."""

    @property
    def connected(self) -> bool: ...

    def connect(self) -> TiltConnectionInfo: ...
    def disconnect(self) -> None: ...
    def status(self) -> TiltStatus: ...
    def home(self, *, timeout: Optional[float] = None) -> TiltStatus: ...

    def set_angle(
        self, angle_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus: ...

    def change_angle(
        self, delta_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus: ...

    def calibrate_zero(self) -> TiltStatus: ...


class PyUsbTiltBackend:
    """Device facade; construction stores configuration without opening USB."""

    def __init__(self, config: TiltFlexConfig):
        config.validate()
        self._device = TiltDevice(
            usb_bus=config.usb_bus,
            usb_address=config.usb_address,
            usb_port_numbers=config.usb_port_numbers,
            default_speed_deg_s=config.default_speed_deg_s,
            max_angle_deg=config.max_angle_deg,
            max_speed_deg_s=config.max_speed_deg_s,
            response_timeout=config.response_timeout_s,
            motion_timeout=config.home_timeout_s,
            motion_timeout_margin=config.motion_timeout_margin_s,
            angle_tolerance_deg=config.angle_tolerance_deg,
            completion_verify_timeout=config.completion_verify_timeout_s,
            completion_poll_interval=config.completion_poll_interval_s,
            require_homed=config.require_homed,
        )

    @property
    def connected(self) -> bool:
        return self._device.connected

    def connect(self) -> TiltConnectionInfo:
        return self._device.open()

    def disconnect(self) -> None:
        self._device.close()

    def status(self) -> TiltStatus:
        return self._device.status()

    def home(self, *, timeout: Optional[float] = None) -> TiltStatus:
        return self._device.home(timeout=timeout)

    def set_angle(
        self, angle_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        return self._device.move_to(angle_deg, speed_deg_s, timeout=timeout)

    def change_angle(
        self, delta_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        return self._device.move_by(delta_deg, speed_deg_s, timeout=timeout)

    def calibrate_zero(self) -> TiltStatus:
        return self._device.calibrate_zero()


class SimulatedTiltBackend:
    """Immediate in-memory responses; never constructs or accesses USB."""

    def __init__(self):
        self._connected = False
        self._status = TiltStatus(2, STATE_NAMES[2], 0.0)

    @property
    def connected(self) -> bool:
        return self._connected

    def _require_connected(self) -> None:
        if not self._connected:
            raise TiltStateError("倾斜模块仿真后端尚未连接")

    def connect(self) -> TiltConnectionInfo:
        self._connected = True
        return TiltConnectionInfo(
            transport="simulated",
            device_info={"mode": "in-memory-tilt-simulation"},
            status=self._status,
        )

    def disconnect(self) -> None:
        self._connected = False

    def status(self) -> TiltStatus:
        self._require_connected()
        return self._status

    def home(self, *, timeout: Optional[float] = None) -> TiltStatus:
        self._require_connected()
        self._status = TiltStatus(0, STATE_NAMES[0], 0.0)
        return self._status

    def set_angle(
        self, angle_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        self._require_connected()
        self._status = TiltStatus(0, STATE_NAMES[0], float(angle_deg))
        return self._status

    def change_angle(
        self, delta_deg: float, speed_deg_s: float, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        self._require_connected()
        return self.set_angle(self._status.angle_deg + float(delta_deg), speed_deg_s)

    def calibrate_zero(self) -> TiltStatus:
        self._require_connected()
        self._status = TiltStatus(0, STATE_NAMES[0], 0.0)
        return self._status


class TiltFlexModule:
    """Single-plate loading facade with an explicitly homed geometry reference.

    ``homed`` here means an explicit successful home during this connection,
    unlike a device status merely reporting idle. Motion or read failures lose
    that reference. This class cannot detect whether robot tools have exited.
    """

    def __init__(self, context: ProtocolContext, config: TiltFlexConfig):
        config.validate()
        self.context = context
        self.config = config
        self._simulate = bool(context.is_simulating()) or not config.hardware_enabled
        self._backend: TiltHardwareBackend = (
            SimulatedTiltBackend() if self._simulate else PyUsbTiltBackend(config)
        )
        self._homed_this_session = False
        self._device_info: Optional[Dict[str, Any]] = None
        self._status: Optional[TiltStatus] = None
        self._pose = TiltPose(0.0, 0.0, False, 0)
        self._labware: Optional[Labware] = None
        self._child: Optional[TiltPlate] = None

    @property
    def connected(self) -> bool:
        return self._backend.connected

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return (dict(self._device_info)
                if self.connected and self._device_info is not None else None)

    @property
    def homed(self) -> bool:
        return self.connected and self._homed_this_session

    @property
    def angle(self) -> float:
        """Last cached angle; inspect pose.valid before using it geometrically."""
        return self._pose.hardware_angle_deg

    @property
    def pose(self) -> TiltPose:
        return self._pose

    @property
    def geometry_angle_sign(self) -> float:
        return self.config.geometry_angle_sign

    @property
    def child(self) -> Optional[TiltPlate]:
        return self._child

    @property
    def tilt_plate(self) -> Optional[TiltPlate]:
        return self._child

    @property
    def labware(self) -> Optional[Labware]:
        """SDK-registered occupant, retained even if its geometric view failed."""
        return self._labware

    def _set_pose(self, hardware_angle_deg: float, *, valid: bool) -> None:
        angle = float(hardware_angle_deg)
        self._pose = TiltPose(
            hardware_angle_deg=angle,
            geometry_angle_deg=(angle * self.config.geometry_angle_sign
                                + self.config.geometry_angle_offset_deg),
            valid=valid,
            revision=self._pose.revision + 1,
        )

    def _invalidate_pose(self, *, reference_lost: bool = False) -> None:
        if reference_lost:
            self._homed_this_session = False
        self._set_pose(self._pose.hardware_angle_deg, valid=False)

    def _accept_status(self, status: TiltStatus, *, pose_valid: bool) -> TiltStatus:
        if status.state not in STATE_NAMES or not math.isfinite(status.angle_deg):
            self._invalidate_pose(reference_lost=True)
            raise TiltStateError("倾斜模块返回了无效状态或角度")
        self._status = status
        if status.needs_home or status.has_fault:
            self._homed_this_session = False
        valid = (pose_valid and self.homed and status.is_idle
                 and abs(status.angle_deg) <= self.config.max_angle_deg)
        self._set_pose(status.angle_deg, valid=valid)
        return status

    def _confirm_motion(self, status: TiltStatus, target: float) -> TiltStatus:
        if (not status.is_idle or not math.isfinite(status.angle_deg)
                or abs(status.angle_deg - target) > self.config.angle_tolerance_deg):
            raise TiltStateError(
                f"倾斜运动未确认到位：目标 {target:.3f}°，"
                f"状态 {status.state_text}，角度 {status.angle_deg!r}°"
            )
        return self._accept_status(status, pose_valid=True)

    def connect(self) -> TiltStatus:
        if self.connected:
            return self.status()
        self._invalidate_pose(reference_lost=True)
        self._device_info = None
        self._status = None
        try:
            connection = self._backend.connect()
            self._device_info = dict(connection.device_info)
            return self._accept_status(connection.status, pose_valid=False)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            self._device_info = None
            self._status = None
            try:
                self._backend.disconnect()
            except BaseException:
                pass  # Preserve the original connection error; send no motion.
            raise

    def disconnect(self) -> None:
        self._invalidate_pose(reference_lost=True)
        self._device_info = None
        self._status = None
        self._backend.disconnect()

    close = disconnect

    def __enter__(self) -> TiltFlexModule:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.disconnect()

    def _require_connected(self) -> None:
        if not self.connected:
            self._invalidate_pose(reference_lost=True)
            raise TiltStateError("倾斜模块尚未连接，请先执行 connect()")

    def _require_homed(self) -> None:
        self._require_connected()
        if not self._homed_this_session:
            raise TiltStateError("本次连接必须显式成功执行 home() 后才能运动或使用坐标")

    def _validate_angle(self, angle_deg: float) -> None:
        if not math.isfinite(angle_deg) or abs(angle_deg) > self.config.max_angle_deg:
            raise TiltOutOfRangeError(
                f"角度必须为 [-{self.config.max_angle_deg}, "
                f"{self.config.max_angle_deg}] 内的有限数"
            )

    def _speed(self, speed_deg_s: Optional[float]) -> float:
        speed = (self.config.default_speed_deg_s if speed_deg_s is None
                 else float(speed_deg_s))
        if (not math.isfinite(speed) or speed <= 0
                or speed > self.config.max_speed_deg_s):
            raise TiltOutOfRangeError("速度必须为大于 0 且不超过配置上限的有限数")
        return speed

    def status(self) -> TiltStatus:
        self._require_connected()
        self._invalidate_pose()
        try:
            return self._accept_status(
                self._backend.status(), pose_valid=self._homed_this_session,
            )
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise

    get_status = status

    def home(self, *, timeout: Optional[float] = None) -> TiltStatus:
        self._require_connected()
        self._invalidate_pose(reference_lost=True)
        try:
            status = self._backend.home(timeout=timeout)
            self._homed_this_session = True
            return self._confirm_motion(status, 0.0)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise

    def set_angle(
        self, angle_deg: float, speed_deg_s: Optional[float] = None, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        self._require_homed()
        target = float(angle_deg)
        self._validate_angle(target)
        speed = self._speed(speed_deg_s)
        self._invalidate_pose()
        try:
            status = self._backend.set_angle(target, speed, timeout=timeout)
            return self._confirm_motion(status, target)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise

    def change_angle(
        self, delta_deg: float, speed_deg_s: Optional[float] = None, *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        self._require_homed()
        delta = float(delta_deg)
        if not math.isfinite(delta):
            raise TiltOutOfRangeError("相对角度必须为有限数")
        speed = self._speed(speed_deg_s)
        current = self.status()
        if not self.pose.valid:
            raise TiltStateError("当前状态没有有效几何姿态，禁止相对运动")
        target = current.angle_deg + delta
        self._validate_angle(target)
        self._invalidate_pose()
        try:
            status = self._backend.change_angle(delta, speed, timeout=timeout)
            return self._confirm_motion(status, target)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise

    def level(self, speed_deg_s: Optional[float] = None) -> TiltStatus:
        """Move to geometry zero, which may differ from device home at zero."""
        self._require_homed()
        target = -self.config.geometry_angle_offset_deg / self.config.geometry_angle_sign
        self._validate_angle(target)
        status = self.status()
        if not self.pose.valid:
            raise TiltStateError("当前状态没有有效几何姿态，禁止调平")
        if abs(self.pose.geometry_angle_deg) <= self.config.level_tolerance_deg:
            return status
        status = self.set_angle(target, speed_deg_s=speed_deg_s)
        if abs(self.pose.geometry_angle_deg) > self.config.level_tolerance_deg:
            self._invalidate_pose(reference_lost=True)
            raise TiltStateError(
                "调平后几何角仍超出水平容差："
                f"当前 {self.pose.geometry_angle_deg:.3f}°，"
                f"允许 ±{self.config.level_tolerance_deg}°"
            )
        return status

    def calibrate_zero(self) -> TiltStatus:
        """Write zero to device Flash; requires a new home before coordinates.

        The caller must establish the intended physical zero. A reported zero
        after calibration cannot prove that the plate is physically horizontal.
        """
        self._require_homed()
        self._invalidate_pose(reference_lost=True)
        try:
            status = self._backend.calibrate_zero()
            if (not status.is_idle or not math.isfinite(status.angle_deg)
                    or abs(status.angle_deg) > self.config.angle_tolerance_deg):
                raise TiltStateError("设备零点标定后未确认返回空闲零度状态")
            return self._accept_status(status, pose_valid=False)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise

    def _require_level_for_labware_move(self) -> TiltStatus:
        self._require_homed()
        status = self.status()
        if not self.pose.valid:
            raise TiltStateError("耗材加载或搬运前模块必须具有有效空闲姿态")
        if abs(self.pose.geometry_angle_deg) > self.config.level_tolerance_deg:
            raise TiltStateError(
                "耗材加载或搬运前模块必须水平："
                f"当前几何角 {self.pose.geometry_angle_deg:.3f}°，"
                f"硬件角 {status.angle_deg:.3f}°，"
                f"允许几何角 ±{self.config.level_tolerance_deg}°"
            )
        return status

    def _require_empty(self) -> None:
        if self._labware is not None:
            raise TiltStateError("倾斜模块已经登记一块耗材")

    def _require_labware(self) -> Labware:
        if self._labware is None:
            raise TiltStateError("倾斜模块当前没有登记耗材")
        return self._labware

    def _clear_labware(self) -> None:
        if self._child is not None:
            self._child._detach()
        self._child = None
        self._labware = None

    def _bind_labware(self, labware: Labware) -> TiltPlate:
        """Record a completed SDK load before constructing optional geometry."""
        self._require_empty()
        self._labware = labware
        try:
            plate = TiltPlate(parent=self, labware=labware)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise
        self._child = plate
        return plate

    def load_labware(
        self, load_name: str, *, label: Optional[str] = None,
    ) -> TiltPlate:
        """Register a plate already manually placed on the level module."""
        self._require_level_for_labware_move()
        self._require_empty()
        labware = self.context.load_labware(load_name, self.config.location, label=label)
        return self._bind_labware(labware)

    def unload_labware(self) -> Labware:
        """Use SDK manual move to OFF_DECK, then detach the geometric view."""
        from opentrons.protocol_api import OFF_DECK

        self._require_level_for_labware_move()
        labware = self._require_labware()
        try:
            self.context.move_labware(
                labware=labware, new_location=OFF_DECK, use_gripper=False,
            )
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise
        self._clear_labware()
        return labware

    def move_labware_onto_module(
        self, labware: Labware, *, use_gripper: bool = True,
        source_pick_up_offset: Optional[Mapping[str, float]] = None,
    ) -> TiltPlate:
        self._require_level_for_labware_move()
        self._require_empty()
        kwargs: Dict[str, Any] = {
            "labware": labware, "new_location": self.config.location,
            "use_gripper": use_gripper,
        }
        if use_gripper:
            kwargs["pick_up_offset"] = source_pick_up_offset
            kwargs["drop_offset"] = self.config.gripper_drop_offset()
        try:
            self.context.move_labware(**kwargs)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise
        return self._bind_labware(labware)

    def move_labware_off_module(
        self, new_location: Any, *, use_gripper: bool = True,
        destination_drop_offset: Optional[Mapping[str, float]] = None,
    ) -> Labware:
        self._require_level_for_labware_move()
        labware = self._require_labware()
        kwargs: Dict[str, Any] = {
            "labware": labware, "new_location": new_location,
            "use_gripper": use_gripper,
        }
        if use_gripper:
            kwargs["pick_up_offset"] = self.config.gripper_pick_up_offset()
            kwargs["drop_offset"] = destination_drop_offset
        try:
            self.context.move_labware(**kwargs)
        except BaseException:
            self._invalidate_pose(reference_lost=True)
            raise
        self._clear_labware()
        return labware


class TiltPlate:
    """A plate's translated, Y-rotated coordinate view, never a liquid planner."""

    def __init__(self, parent: TiltFlexModule, labware: Labware):
        self.parent = parent
        self.config = parent.config
        self.labware = labware
        wells = labware.wells()
        if not wells:
            raise ValueError("耗材没有孔位，无法建立倾斜几何模型")
        min_x = min(well.center().point.x for well in wells)
        max_x = max(well.center().point.x for well in wells)
        axis_x = (min_x + max_x) / 2 + self.config.module_offset_x_mm
        axis_z = (
            wells[0].bottom(z=0).point.z + self.config.module_height_mm
            - self.config.axis_to_plate_bottom_mm
            - self.config.plate_bottom_to_well_bottom_mm
        )
        self.geometry = TiltGeometry(axis_x=axis_x, axis_z=axis_z)
        self._attached = True

    @property
    def attached(self) -> bool:
        return self._attached

    @property
    def pose(self) -> TiltPose:
        return self.parent.pose

    @property
    def hardware_angle_deg(self) -> float:
        return self.pose.hardware_angle_deg

    @property
    def geometry_angle_deg(self) -> float:
        return self.pose.geometry_angle_deg

    def _require_attached(self) -> None:
        if not self._attached or self.parent.child is not self:
            raise TiltStateError("该 TiltPlate 已解除绑定，坐标不再有效")

    def _require_pose(self) -> None:
        self._require_attached()
        self.parent._require_connected()
        if not self.pose.valid:
            raise TiltStateError("模块姿态当前无效，请先显式成功执行 home()")

    def _detach(self) -> None:
        self._attached = False

    def _well(self, well_name: str) -> Well:
        self._require_attached()
        try:
            return self.labware.wells_by_name()[well_name]
        except KeyError as exc:
            raise KeyError(f"耗材中不存在孔位 {well_name!r}") from exc

    def _transform_level_point(self, point: Point) -> Point:
        from opentrons.types import Point

        placed = Point(
            x=point.x + self.config.module_offset_x_mm,
            y=point.y + self.config.module_offset_y_mm,
            z=point.z + self.config.module_height_mm,
        )
        return self.geometry.rotate(placed, self.geometry_angle_deg)

    def location(
        self, well_name: str, *, origin: str = "bottom", x: float = 0.0,
        y: float = 0.0, z: float = 0.0,
    ) -> Location:
        from opentrons.types import Location, Point

        self._require_pose()
        if not all(math.isfinite(value) for value in (x, y, z)):
            raise ValueError("孔内 x、y、z 偏移必须为有限数")
        well = self._well(well_name)
        if origin == "bottom":
            base = well.bottom(z=z)
        elif origin == "top":
            base = well.top(z=z)
        elif origin == "center":
            base = well.center().move(Point(x=0, y=0, z=z))
        else:
            raise ValueError("origin 必须为 bottom、center 或 top")
        level_point = base.move(Point(x=x, y=y, z=0)).point
        return Location(self._transform_level_point(level_point), well)

    def bottom(
        self, well_name: str, z: float = 0.0, *, x: float = 0.0, y: float = 0.0,
    ) -> Location:
        return self.location(well_name, origin="bottom", x=x, y=y, z=z)

    def center(
        self, well_name: str, *, x: float = 0.0, y: float = 0.0, z: float = 0.0,
    ) -> Location:
        return self.location(well_name, origin="center", x=x, y=y, z=z)

    def top(
        self, well_name: str, z: float = 0.0, *, x: float = 0.0, y: float = 0.0,
    ) -> Location:
        return self.location(well_name, origin="top", x=x, y=y, z=z)


def load_tilt_module(context: ProtocolContext, config: TiltFlexConfig) -> TiltFlexModule:
    """Construct the facade only; never connect, home, or move implicitly."""
    return TiltFlexModule(context=context, config=config)
