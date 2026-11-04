"""Tilt-device commands extracted from the supplied wash-template source.

Source SHA-256: 3f8af32d1f0257ef7990e3d68aecb52b16b9dd08fd7a7474b89e32ed3269b193
Transport: communication/ch340_transport.py. The 64-byte framing, big-endian CRC,
commands and defaults below come from that source, not a newly verified vendor
specification. Tilt-specific state and rotation classes share this device entry. No layout,
labware loading, washing or pipetting is performed.
Imports and constructors do not connect to hardware. Calibration explicitly
writes the device zero reference to Flash. Motion is never retried automatically.
"""

from __future__ import annotations

import math
import struct
import time
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from ...communication.ch340_transport import (
    PYUSB_AVAILABLE, PyUsbCH340Transport, Transport, TransportError,
    enumerate_ch340_usb, select_ch340_usb,
)

USB_CONNECT_RETRY_SECONDS = 6.0
if TYPE_CHECKING:
    from opentrons.types import Point

STATE_NAMES = {0: "空闲且在位", 1: "运动中", 2: "未回零", 3: "堵转或故障"}


class TiltError(TransportError):
    """Base class for tilt-module errors."""


class TiltCommunicationError(TiltError):
    pass


class TiltTimeoutError(TiltCommunicationError):
    pass


class TiltStateError(TiltError):
    pass


class TiltOutOfRangeError(ValueError):
    pass


class TiltCalibrationError(TiltError):
    pass


def crc16_modbus(data: bytes) -> int:
    """Return the standard Modbus CRC-16 numeric value."""

    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def crc_wire_bytes(data: bytes) -> bytes:
    """Return CRC bytes exactly as the vendor qyangle tool puts them on wire.

    For a zero-filled Ping body, the standard CRC value is 0xAB01 and the
    vendor frame ends in ``AB 01``. This is intentionally not little-endian.
    """

    return struct.pack(">H", crc16_modbus(data))


def inspect_crc(frame: bytes) -> Dict[str, Any]:
    if len(frame) != 64:
        raise ValueError(f"帧长度必须为 64，实际为 {len(frame)}")
    expected = crc16_modbus(frame[:62])
    return {
        "expected_value_hex": f"0x{expected:04X}",
        "wire_bytes_hex": frame[62:64].hex(" "),
        "vendor_wire_ok": frame[62:64] == crc_wire_bytes(frame[:62]),
        "little_wire_ok": frame[62:64] == struct.pack("<H", expected),
        "big_wire_ok": frame[62:64] == struct.pack(">H", expected),
    }


def build_frame(command: int, payload: bytes = b"") -> bytes:
    if not 0 <= command <= 0xFFFF:
        raise ValueError(f"命令超出 uint16 范围: {command}")
    if len(payload) > 60:
        raise ValueError(f"参数最多 60 字节，当前为 {len(payload)}")
    body = bytearray(62)
    struct.pack_into("<H", body, 0, command)
    body[2 : 2 + len(payload)] = payload
    return bytes(body) + crc_wire_bytes(bytes(body))


def parse_response_frame(frame: bytes) -> bytes:
    if len(frame) != 64:
        raise ValueError(f"响应帧长度必须为 64，实际为 {len(frame)}")
    expected = crc16_modbus(frame[:62])
    received = struct.unpack_from(">H", frame, 62)[0]
    if expected != received:
        raise ValueError(
            f"响应 CRC 错误: expected=0x{expected:04X}, received=0x{received:04X}, "
            f"details={inspect_crc(frame)}"
        )
    return frame[:62]


def hex_dump(data: bytes) -> str:
    return data.hex(" ").upper()


def printable_ascii(data: bytes) -> str:
    return "".join(chr(value) if 32 <= value <= 126 else "." for value in data)


@dataclass(frozen=True)
class TiltStatus:
    """Structured device status exposed by the high-level API."""

    state: int
    state_text: str
    angle_deg: float
    raw_payload_hex: str = ""

    @property
    def is_idle(self) -> bool:
        return self.state == 0

    @property
    def is_moving(self) -> bool:
        return self.state == 1

    @property
    def needs_home(self) -> bool:
        return self.state == 2

    @property
    def has_fault(self) -> bool:
        return self.state == 3

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _validated_status(value: Dict[str, Any]) -> TiltStatus:
    state = int(value["state"])
    angle = float(value["angle_deg"])
    if state not in STATE_NAMES:
        raise TiltStateError(f"设备返回未知状态码: {state}")
    if not math.isfinite(angle):
        raise TiltStateError(f"设备返回无效角度: {angle!r}")
    return TiltStatus(
        state=state, state_text=STATE_NAMES[state], angle_deg=angle,
        raw_payload_hex=str(value.get("raw_payload_hex", "")),
    )


@dataclass(frozen=True)
class TiltConnectionInfo:
    """Result of opening and verifying a tilt-module connection."""

    transport: str
    device_info: Dict[str, Any]
    status: TiltStatus
    usb_identity: Optional[Dict[str, Any]] = None
    stale_handle_released: bool = False


class TiltController:
    """Blocking controller for the supplied tilt-device protocol."""

    def __init__(
        self,
        *,
        usb_bus: Optional[int] = None,
        usb_address: Optional[int] = None,
        usb_port_numbers: Optional[tuple[int, ...]] = None,
        max_angle_deg: float = 30.0,
        max_speed_deg_s: float = 30.0,
        response_timeout: float = 5.0,
        motion_timeout: float = 30.0,
        motion_timeout_margin: float = 5.0,
        angle_tolerance_deg: float = 0.15,
        completion_verify_timeout: float = 2.0,
        completion_poll_interval: float = 0.05,
        require_homed: bool = True,
    ):
        if not math.isfinite(response_timeout) or response_timeout <= 0:
            raise ValueError("response_timeout 必须是正的有限秒数")
        if not math.isfinite(motion_timeout) or motion_timeout <= 0:
            raise ValueError("motion_timeout 必须是正的有限秒数")
        if not math.isfinite(motion_timeout_margin) or motion_timeout_margin < 0:
            raise ValueError("motion_timeout_margin 必须是非负有限秒数")
        if not math.isfinite(angle_tolerance_deg) or angle_tolerance_deg <= 0:
            raise ValueError("angle_tolerance_deg 必须是正的有限数")
        if not math.isfinite(completion_verify_timeout) or completion_verify_timeout <= 0:
            raise ValueError("completion_verify_timeout 必须是正的有限秒数")
        if not math.isfinite(completion_poll_interval) or completion_poll_interval <= 0:
            raise ValueError("completion_poll_interval 必须是正的有限秒数")
        for name, value in (("max_angle_deg", max_angle_deg),
                            ("max_speed_deg_s", max_speed_deg_s)):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} 必须是正的有限数")
        self.usb_bus = usb_bus
        self.usb_address = usb_address
        self.usb_port_numbers = (
            tuple(usb_port_numbers) if usb_port_numbers is not None else None
        )
        self.max_angle_deg = float(max_angle_deg)
        self.max_speed_deg_s = float(max_speed_deg_s)
        self.response_timeout = float(response_timeout)
        self.motion_timeout = float(motion_timeout)
        self.motion_timeout_margin = float(motion_timeout_margin)
        self.angle_tolerance_deg = float(angle_tolerance_deg)
        self.completion_verify_timeout = float(completion_verify_timeout)
        self.completion_poll_interval = float(completion_poll_interval)
        self.require_homed = require_homed
        self.transport: Optional[Transport] = None
        self.active_transport: Optional[str] = None
        self.active_usb_identity: Optional[Dict[str, Any]] = None
        self.stale_handle_released = False
        self.last_status: Optional[Dict[str, Any]] = None
        self.communication_verified = False

    @property
    def connected(self) -> bool:
        return bool(self.transport is not None and self.transport.is_open)

    def connect(self) -> None:
        if self.connected:
            return
        if not PYUSB_AVAILABLE:
            raise TiltCommunicationError("当前环境没有 PyUSB，无法使用手写 CH340 驱动")

        deadline = time.monotonic() + USB_CONNECT_RETRY_SECONDS
        last_error: Optional[BaseException] = None
        while time.monotonic() < deadline:
            transport = None
            try:
                devices = enumerate_ch340_usb()
                selected = select_ch340_usb(
                    devices, usb_bus=self.usb_bus, usb_address=self.usb_address,
                    usb_port_numbers=self.usb_port_numbers,
                )
                if selected is not None:
                    transport = PyUsbCH340Transport(selected["device"])
                    transport.open()
                    transport.reset_input_buffer()
                    self.stale_handle_released = bool(
                        getattr(transport, "stale_handle_released", False)
                    )
                    self.transport = transport
                    self.active_transport = "pyusb"
                    self.active_usb_identity = {
                        key: selected.get(key)
                        for key in ("bus", "address", "port_numbers")
                    }
                    return
                raise TiltCommunicationError("没有找到 CH340 USB 设备")
            except BaseException as exc:
                last_error = exc
                if transport is not None:
                    transport.close()
                self.transport = None
                self.active_usb_identity = None
                if not isinstance(exc, Exception):
                    raise
                current_error = exc
                errno = None
                while current_error is not None:
                    errno = getattr(current_error, "errno", None)
                    if errno is not None:
                        break
                    current_error = current_error.__cause__
                retryable = errno in {13, 16} or "没有找到 CH340" in str(exc)
                if retryable and time.monotonic() < deadline:
                    time.sleep(0.4)
                    continue
                raise TiltCommunicationError(f"CH340 PyUSB 连接失败: {exc}") from exc

        raise TiltCommunicationError(
            "在连接重试时间内无法锁定 CH340 接口；"
            f"最后错误: {last_error!r}。可尝试重新插拔协议盒 USB。"
        )

    def disconnect(self) -> None:
        if self.transport is not None:
            try:
                self.transport.close()
            finally:
                self.transport = None
                self.active_transport = None
                self.active_usb_identity = None
        self.communication_verified = False
        self.last_status = None

    def _require_connected(self) -> None:
        if not self.connected:
            raise TiltCommunicationError("请先执行 controller.connect()")

    def _read_exact(self, size: int, timeout: Optional[float] = None) -> bytes:
        self._require_connected()
        deadline = time.monotonic() + (timeout or self.response_timeout)
        result = bytearray()
        while len(result) < size and time.monotonic() < deadline:
            chunk = self.transport.read(size - len(result))  # type: ignore[union-attr]
            if chunk:
                result.extend(chunk)
        if len(result) != size:
            raise TiltTimeoutError(
                f"等待 {size} 字节回复超时，实际收到 {len(result)} 字节: {hex_dump(bytes(result))}"
            )
        return bytes(result)

    def _transact(
        self,
        command_code: int,
        command_name: str,
        payload: bytes = b"",
        parser: Optional[Callable[[bytes], Dict[str, Any]]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._require_connected()
        request = build_frame(command_code, payload)
        try:
            self.transport.reset_input_buffer()
            self.transport.reset_output_buffer()
            written = self.transport.write(request)
            if written != len(request):
                raise TiltCommunicationError(f"只写入 {written}/{len(request)} 字节")
            self.transport.flush()
            response = self._read_exact(64, timeout)
            data = parse_response_frame(response)
            parsed = parser(data) if parser else {"payload_hex": hex_dump(data)}
            if command_code in {0, 20, 30004}:
                self.communication_verified = True
            return parsed
        except BaseException:
            # A failed exchange leaves device outcome unknown. Require a new
            # connection/handshake; never replay a potentially completed motion.
            self.communication_verified = False
            self.last_status = None
            try:
                self.disconnect()
            except Exception:
                pass
            raise

    @staticmethod
    def _parse_empty(data: bytes) -> Dict[str, Any]:
        return {"payload_hex": hex_dump(data)}

    @staticmethod
    def _parse_result(data: bytes) -> Dict[str, Any]:
        result = data[0]
        return {
            "result": result,
            "result_text": "成功" if result == 0 else "失败/未知状态",
        }

    def ping(self) -> Dict[str, Any]:
        return self._transact(0, "Ping", parser=self._parse_empty)

    def get_status(self) -> Dict[str, Any]:
        def parse(data: bytes) -> Dict[str, Any]:
            state = data[0]
            angle = struct.unpack_from("<f", data, 1)[0]
            status = {
                "state": state,
                "state_text": STATE_NAMES.get(state, "未知状态"),
                "angle_deg": angle,
                "raw_payload_hex": hex_dump(data[:5]),
            }
            _validated_status(status)
            self.last_status = status
            return status

        return self._transact(30004, "获取倾斜模块状态", parser=parse)

    def get_fm_info(self) -> Dict[str, Any]:
        def parse(data: bytes) -> Dict[str, Any]:
            return {
                "raw_payload_hex": hex_dump(data),
                "printable_ascii": printable_ascii(data),
                "note": "当前保留原始信息；字段布局需厂家确认",
            }

        return self._transact(20, "get_fm_info", parser=parse)

    def _validate_speed(self, speed_deg_s: float) -> None:
        if not math.isfinite(speed_deg_s) or speed_deg_s <= 0:
            raise TiltOutOfRangeError("速度必须是正的有限数")
        if speed_deg_s > self.max_speed_deg_s:
            raise TiltOutOfRangeError(
                f"速度不能超过 {self.max_speed_deg_s} 度/秒，当前为 {speed_deg_s}"
            )

    def _validate_angle(self, angle_deg: float) -> None:
        if not math.isfinite(angle_deg):
            raise TiltOutOfRangeError("角度必须是有限数")
        if abs(angle_deg) > self.max_angle_deg:
            raise TiltOutOfRangeError(
                f"角度必须在 [-{self.max_angle_deg}, {self.max_angle_deg}] 内，当前为 {angle_deg}"
            )

    def _require_motion_ready(self, status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        status = self.get_status() if status is None else status
        _validated_status(status)
        if status["state"] == 2 and self.require_homed:
            raise TiltStateError("模块尚未回零，请先执行 home()")
        if status["state"] == 3:
            raise TiltStateError("模块处于堵转或故障状态")
        if status["state"] == 1:
            raise TiltStateError("模块仍在运动，请等待当前动作完成")
        return status

    def _motion_command_timeout(
        self,
        travel_deg: float,
        speed_deg_s: float,
        timeout: Optional[float],
    ) -> float:
        if timeout is not None:
            if not math.isfinite(timeout) or timeout <= 0:
                raise ValueError("timeout 必须是正的有限秒数")
            return float(timeout)
        expected_seconds = abs(float(travel_deg)) / float(speed_deg_s)
        return max(self.response_timeout, expected_seconds + self.motion_timeout_margin)

    def _verify_completed_status(self, target_angle: float) -> Dict[str, Any]:
        """Confirm the final status after the blocking motion reply.

        The vendor motion reply is blocking, but short moves can finish before
        the separately queried status register publishes its next sample.  A
        single immediate query can therefore return the previous angle.  This
        bounded window waits only for status synchronization; it does not turn
        the motion command itself into a polling implementation.
        """

        deadline = time.monotonic() + self.completion_verify_timeout
        samples: list[tuple[int, float]] = []
        status: Dict[str, Any] = {}
        while True:
            status = self.get_status()
            state = int(status["state"])
            angle = float(status["angle_deg"])
            samples.append((state, angle))

            if state == 3:
                raise TiltStateError(
                    "设备回复动作完成后，状态确认检测到堵转或故障: "
                    f"samples={samples}"
                )
            if state == 0 and abs(angle - target_angle) <= self.angle_tolerance_deg:
                return status
            if state not in {0, 1, 2}:
                raise TiltStateError(
                    f"设备回复动作完成后返回未知状态: {status}, samples={samples}"
                )

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(min(self.completion_poll_interval, remaining))

        if status.get("state") == 2:
            reason = "状态确认窗口结束后仍显示未回零"
        elif status.get("state") != 0:
            reason = "状态确认窗口结束后仍不是空闲状态"
        else:
            reason = "状态已空闲，但角度在确认窗口内始终未同步到目标"
        raise TiltStateError(
            f"设备已返回动作回复，但完成后状态确认失败（{reason}）: "
            f"target={target_angle}, actual={status.get('angle_deg')}, "
            f"tolerance={self.angle_tolerance_deg}, "
            f"verify_timeout={self.completion_verify_timeout}s, samples={samples}"
        )

    def home(self, *, timeout: Optional[float] = None) -> Dict[str, Any]:
        self._require_connected()
        current = self.get_status()
        if current["state"] == 1:
            raise TiltStateError("模块仍在运动，不能再次执行回零")
        if current["state"] == 3:
            raise TiltStateError("模块处于堵转或故障状态，不能执行回零")
        command_timeout = self.motion_timeout if timeout is None else float(timeout)
        if not math.isfinite(command_timeout) or command_timeout <= 0:
            raise ValueError("timeout 必须是正的有限秒数")
        ack = self._transact(
            30001,
            "倾斜模块回零初始化",
            parser=self._parse_result,
            timeout=command_timeout,
        )
        if ack.get("result") != 0:
            raise TiltStateError(f"回零命令失败: {ack}")
        status = self._verify_completed_status(target_angle=0.0)
        return {"ack": ack, "status": status}

    def move_absolute(
        self,
        angle_deg: float,
        speed_deg_s: float,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._validate_angle(angle_deg)
        self._validate_speed(speed_deg_s)
        initial = self._require_motion_ready()
        payload = struct.pack("<ff", float(angle_deg), float(speed_deg_s))
        command_timeout = self._motion_command_timeout(
            angle_deg - initial["angle_deg"],
            speed_deg_s,
            timeout,
        )
        ack = self._transact(
            30002,
            "移动指定绝对角度",
            payload,
            self._parse_result,
            timeout=command_timeout,
        )
        if ack.get("result") != 0:
            raise TiltStateError(f"绝对角度命令失败: {ack}")
        status = self._verify_completed_status(target_angle=float(angle_deg))
        return {"ack": ack, "status": status}

    def move_relative(
        self,
        delta_deg: float,
        speed_deg_s: float,
        *,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        self._validate_angle(delta_deg)
        self._validate_speed(speed_deg_s)
        initial = self._require_motion_ready()
        target = initial["angle_deg"] + delta_deg
        self._validate_angle(target)
        payload = struct.pack("<ff", float(delta_deg), float(speed_deg_s))
        command_timeout = self._motion_command_timeout(delta_deg, speed_deg_s, timeout)
        ack = self._transact(
            30003,
            "移动指定相对角度",
            payload,
            self._parse_result,
            timeout=command_timeout,
        )
        if ack.get("result") != 0:
            raise TiltStateError(f"相对角度命令失败: {ack}")
        status = self._verify_completed_status(target_angle=float(target))
        return {"ack": ack, "status": status}

    def calibrate_zero(self) -> Dict[str, Any]:
        """Write the current physical zero reference to device Flash."""
        current = self.get_status()
        if current["state"] != 0:
            raise TiltStateError(
                f"标定前模块必须处于空闲状态，当前为 state={current['state']} ({current['state_text']})"
            )
        result = self._transact(30005, "标定零点并写入 Flash", parser=self._parse_result)
        if result.get("result") != 0:
            raise TiltCalibrationError(
                "标定失败：舵机位置读取异常或设备拒绝写入，返回 " + repr(result)
            )
        return {"ack": result, "status": self.get_status()}


class TiltDevice:
    """Small device-level facade intended for notebooks and workflow code.

    ``TiltController`` remains the protocol-aware implementation.  This class
    provides a narrower public API, performs a complete handshake when opened,
    returns structured status objects, and preserves the supplied blocking
    motion and completion-check behavior.

    Opening never homes or calibrates automatically. ``homed`` records an
    explicit home in this connection; moves follow the reported device state
    and the configured ``require_homed``, not a forced per-session workflow.
    """

    def __init__(
        self,
        *,
        usb_bus: Optional[int] = None,
        usb_address: Optional[int] = None,
        usb_port_numbers: Optional[tuple[int, ...]] = None,
        default_speed_deg_s: float = 2.0,
        max_angle_deg: float = 30.0,
        max_speed_deg_s: float = 30.0,
        response_timeout: float = 5.0,
        motion_timeout: float = 30.0,
        motion_timeout_margin: float = 5.0,
        angle_tolerance_deg: float = 0.15,
        completion_verify_timeout: float = 2.0,
        completion_poll_interval: float = 0.05,
        require_homed: bool = True,
    ):
        self.controller = TiltController(
            usb_bus=usb_bus,
            usb_address=usb_address,
            usb_port_numbers=usb_port_numbers,
            max_angle_deg=max_angle_deg,
            max_speed_deg_s=max_speed_deg_s,
            response_timeout=response_timeout,
            motion_timeout=motion_timeout,
            motion_timeout_margin=motion_timeout_margin,
            angle_tolerance_deg=angle_tolerance_deg,
            completion_verify_timeout=completion_verify_timeout,
            completion_poll_interval=completion_poll_interval,
            require_homed=require_homed,
        )
        self.controller._validate_speed(default_speed_deg_s)
        self.default_speed_deg_s = float(default_speed_deg_s)
        self._device_info: Optional[Dict[str, Any]] = None
        self._last_status: Optional[TiltStatus] = None
        self._homed_this_session = False

    @staticmethod
    def _status_from_mapping(value: Dict[str, Any]) -> TiltStatus:
        return _validated_status(value)

    @property
    def connected(self) -> bool:
        return self.controller.connected

    @property
    def active_transport(self) -> Optional[str]:
        return self.controller.active_transport

    @property
    def last_status(self) -> Optional[TiltStatus]:
        return self._last_status if self.connected else None

    @property
    def homed(self) -> bool:
        return self.connected and self._homed_this_session

    @property
    def device_info(self) -> Optional[Dict[str, Any]]:
        return (dict(self._device_info)
                if self.connected and self._device_info is not None else None)

    def open(self) -> TiltConnectionInfo:
        was_connected = self.connected
        self.controller.connect()

        if not was_connected:
            self._homed_this_session = False

        try:
            try:
                self.controller.ping()
            except TiltTimeoutError:
                # The failed exchange closed its transport. Only the read-only
                # handshake is retried, with a fresh connection and session.
                time.sleep(0.3)
                self._homed_this_session = False
                self._last_status = None
                self._device_info = None
                self.controller.connect()
                self.controller.ping()

            self._device_info = self.controller.get_fm_info()
            self._last_status = self._status_from_mapping(
                self.controller.get_status()
            )

        except BaseException:
            self.close()
            raise
        return TiltConnectionInfo(
            transport=self.controller.active_transport or "unknown",
            device_info=dict(self._device_info),
            status=self._last_status,
            usb_identity=(
                dict(self.controller.active_usb_identity)
                if self.controller.active_usb_identity is not None
                else None
            ),
            stale_handle_released=self.controller.stale_handle_released,
        )

    connect = open

    def close(self) -> None:
        self.controller.disconnect()
        self._homed_this_session = False
        self._last_status = None
        self._device_info = None

    disconnect = close

    def __enter__(self) -> "TiltDevice":
        self.open()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.close()

    def ping(self) -> bool:
        self.controller.ping()
        return True

    def refresh_device_info(self) -> Dict[str, Any]:
        self._device_info = self.controller.get_fm_info()
        return dict(self._device_info)

    def status(self) -> TiltStatus:
        self._last_status = None
        self._last_status = self._status_from_mapping(self.controller.get_status())
        return self._last_status


    def home(
        self,
        *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        self._last_status = None
        self._homed_this_session = False
        result = self.controller.home(timeout=timeout)
        self._last_status = self._status_from_mapping(result["status"])
        self._homed_this_session = True
        return self._last_status

    def move_to(
        self,
        angle_deg: float,
        speed_deg_s: Optional[float] = None,
        *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        speed = self.default_speed_deg_s if speed_deg_s is None else float(speed_deg_s)
        self._last_status = None
        result = self.controller.move_absolute(
            angle_deg,
            speed,
            timeout=timeout,
        )
        self._last_status = self._status_from_mapping(result["status"])
        return self._last_status

    def move_by(
        self,
        delta_deg: float,
        speed_deg_s: Optional[float] = None,
        *,
        timeout: Optional[float] = None,
    ) -> TiltStatus:
        speed = self.default_speed_deg_s if speed_deg_s is None else float(speed_deg_s)
        self._last_status = None
        result = self.controller.move_relative(
            delta_deg,
            speed,
            timeout=timeout,
        )
        self._last_status = self._status_from_mapping(result["status"])
        return self._last_status

    def calibrate_zero(self) -> TiltStatus:
        self._last_status = None
        result = self.controller.calibrate_zero()
        self._last_status = self._status_from_mapping(result["status"])
        return self._last_status


@dataclass(frozen=True)
class TiltGeometry:
    """Rigid rotation around a deck-parallel Y axis."""

    axis_x: float
    axis_z: float

    def rotate(self, point: Point, angle_deg: float) -> Point:
        # Geometry alone needs the SDK; device communications do not.
        from opentrons.types import Point

        theta = math.radians(angle_deg)
        dx = point.x - self.axis_x
        dz = point.z - self.axis_z
        return Point(
            x=self.axis_x + dx * math.cos(theta) + dz * math.sin(theta),
            y=point.y,
            z=self.axis_z - dx * math.sin(theta) + dz * math.cos(theta),
        )
