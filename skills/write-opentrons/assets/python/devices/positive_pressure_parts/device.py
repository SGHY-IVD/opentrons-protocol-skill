"""Blocking positive-pressure device extracted from the supplied protocol.

Source SHA-256: 625bcbcdd06a46650d457f4eb767e0263cad52188116a63d152d5aff33cdf098
Only the supplied ``C pressure duration_ms 0 0`` and ``D`` commands are
implemented.  Their execution is never retried automatically: missing ``ok``
does not establish whether the device already executed the command.

The pressure source has three CH340 control transfers and does not state a
baud rate.  Its initialization must not inherit the tilt device's additional
baud-register write.  Importing and constructing these classes never discover,
open, reset, or move hardware.  Only PPMDevice knows about SDK simulation;
an application-level dry-run flag is not a hardware simulation flag.
"""

from __future__ import annotations

import math
import threading
import time
from numbers import Integral, Real
from typing import Any, Optional

from ...communication.ch340_transport import (
    PYUSB_AVAILABLE, PyUsbCH340Transport, Transport, TransportError,
    enumerate_ch340_usb, select_ch340_usb,
)


END_OF_LINE = "\r\n"
ACK = "ok\n"
ACK_CRLF = "ok\r\n"


class PPMCommunicationError(TransportError):
    """Pressure communication failed; execution may already have occurred."""


class AckError(PPMCommunicationError):
    """A complete, exact ``ok`` response was not obtained."""

    def __init__(self, cmd: str, response: str):
        self.cmd = cmd
        self.response = response
        super().__init__(
            f"指令 {cmd!r} 未收到有效的 ok 应答，实际收到: {response!r}。"
            "指令可能已执行；连接已失效，请核实设备后再决定下一步。"
        )


class PPMTimeoutError(AckError):
    """The command's total monotonic deadline expired."""


def _ppm_integer(name: str, value: Any, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} 必须是大于等于 {minimum} 的有限整数")
    if isinstance(value, Integral):
        converted = int(value)
        if converted < minimum:
            raise ValueError(f"{name} 必须是大于等于 {minimum} 的有限整数")
        return converted
    try:
        finite = math.isfinite(value)
        converted = int(value) if finite else 0
    except (OverflowError, TypeError, ValueError):
        finite = False
        converted = 0
    if not finite or converted != value or converted < minimum:
        raise ValueError(f"{name} 必须是大于等于 {minimum} 的有限整数")
    return converted


def _ppm_positive_seconds(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} 必须是正的有限秒数")
    try:
        converted = float(value)
    except (OverflowError, TypeError, ValueError):
        raise ValueError(f"{name} 必须是正的有限秒数") from None
    if not math.isfinite(converted) or converted <= 0:
        raise ValueError(f"{name} 必须是正的有限秒数")
    return converted


def _ppm_duration_ms(seconds: Any) -> tuple[float, int]:
    """Retain the source's int(seconds * 1000), including truncation."""
    value = _ppm_positive_seconds("seconds", seconds)
    milliseconds = value * 1000
    if not math.isfinite(milliseconds):
        raise ValueError("seconds 转换为毫秒后必须为有限数")
    duration_ms = int(milliseconds)
    if duration_ms < 1:
        raise ValueError("seconds 必须至少为 0.001 秒；小数毫秒会向零截断")
    return value, duration_ms


class PressureCH340Transport(PyUsbCH340Transport):
    """Shared USB ownership/buffering with the pressure source's exact setup."""

    def __init__(self, device: Any = None, usb_timeout_ms: int = 50):
        super().__init__(device=device, usb_timeout_ms=usb_timeout_ms)
        self._command_deadline: Optional[float] = None

    def _initialize_uart(self) -> None:
        self.dev.ctrl_transfer(0x40, 0xA1, 0, 0)
        self.dev.ctrl_transfer(0x40, 0x9A, 0x2518, 0x00C3)
        self.dev.ctrl_transfer(0x40, 0xA4, 0xFF, 0)

    def _bounded_timeout_ms(self, configured_ms: int) -> int:
        if self._command_deadline is None:
            return configured_ms
        remaining = self._command_deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("正压指令总等待时间已到")
        return max(1, min(configured_ms, math.ceil(remaining * 1000)))

    def write(self, data: bytes) -> int:
        if not self.is_open or self.ep_out is None:
            raise TransportError("CH340 PyUSB 传输尚未打开")
        return int(self.ep_out.write(data, timeout=self._bounded_timeout_ms(1000)))

    def read(self, size: int) -> bytes:
        previous_timeout = self.usb_timeout_ms
        self.usb_timeout_ms = self._bounded_timeout_ms(previous_timeout)
        try:
            return super().read(size)
        finally:
            self.usb_timeout_ms = previous_timeout

    def reset_input_buffer(self) -> None:
        previous_timeout = self.usb_timeout_ms
        self.usb_timeout_ms = self._bounded_timeout_ms(previous_timeout)
        try:
            super().reset_input_buffer()
        finally:
            self.usb_timeout_ms = previous_timeout


class PPMController:
    """Blocking pressure controller; pressure is integer kPa, time integer ms.

    ``response_timeout`` defaults to the source's five-second response window.
    A pressure command has one total deadline of duration_ms / 1000 plus that
    window; busy lines never restart it.  ``reset_timeout`` defaults to the
    response window and is configurable because the source gives no reset
    duration specification.  This deadline bounds the command loop; each USB
    operation also has a finite timeout, subject to scheduling and millisecond
    granularity.  Injected transports must bound read/write operations themselves.

    No vendor pressure maximum is established by this source; pressure must be
    a nonnegative integer.  A protocol's narrower working range belongs in its
    validated experiment settings.  Connect/close never send a reset command.
    """

    def __init__(
        self,
        *,
        transport: Optional[Transport] = None,
        usb_bus: Optional[int] = None,
        usb_address: Optional[int] = None,
        usb_port_numbers: Optional[tuple[int, ...]] = None,
        response_timeout: float = 5.0,
        reset_timeout: Optional[float] = None,
        usb_timeout_ms: int = 50,
        max_line_bytes: int = 4096,
        max_response_bytes: int = 65536,
    ):
        self.response_timeout = _ppm_positive_seconds("response_timeout", response_timeout)
        self.reset_timeout = (
            self.response_timeout if reset_timeout is None
            else _ppm_positive_seconds("reset_timeout", reset_timeout)
        )
        self.usb_timeout_ms = _ppm_integer("usb_timeout_ms", usb_timeout_ms, 1)
        self.max_line_bytes = _ppm_integer("max_line_bytes", max_line_bytes, 1)
        self.max_response_bytes = _ppm_integer("max_response_bytes", max_response_bytes, 1)
        self.usb_bus = usb_bus
        self.usb_address = usb_address
        self.usb_port_numbers = (
            tuple(usb_port_numbers) if usb_port_numbers is not None else None
        )
        self._provided_transport = transport
        self._serial: Optional[Transport] = None
        self._io_lock = threading.RLock()
        self.last_response = ""

    @property
    def connected(self) -> bool:
        return bool(self._serial is not None and self._serial.is_open)

    def connect(self) -> None:
        with self._io_lock:
            if self.connected:
                return
            serial = self._provided_transport
            if serial is None:
                if not PYUSB_AVAILABLE:
                    raise PPMCommunicationError("当前环境没有 PyUSB，无法连接正压模块")
                selected = select_ch340_usb(
                    enumerate_ch340_usb(),
                    usb_bus=self.usb_bus,
                    usb_address=self.usb_address,
                    usb_port_numbers=self.usb_port_numbers,
                )
                if selected is None:
                    raise PPMCommunicationError("未找到正压模块 CH340 VID=1A86 PID=7523")
                serial = PressureCH340Transport(
                    selected["device"], usb_timeout_ms=self.usb_timeout_ms
                )
            try:
                serial.open()
                if not serial.is_open:
                    raise PPMCommunicationError("正压模块传输未进入已连接状态")
            except BaseException:
                try:
                    serial.close()
                except Exception:
                    pass
                raise
            self._serial = serial

    def disconnect(self) -> None:
        with self._io_lock:
            serial, self._serial = self._serial, None
            if serial is not None:
                serial.close()

    def close(self) -> None:
        self.disconnect()

    def __enter__(self) -> "PPMController":
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> None:
        self.disconnect()

    def _execute_command(self, cmd: str, timeout: float) -> str:
        with self._io_lock:
            if not self.connected:
                raise PPMCommunicationError("正压模块未连接，请先执行 connect()")
            serial = self._serial
            deadline = time.monotonic() + timeout
            if not math.isfinite(deadline):
                raise ValueError("正压指令总等待时间必须为有限秒数")
            self.last_response = ""
            response = bytearray()
            pending = bytearray()
            if isinstance(serial, PressureCH340Transport):
                serial._command_deadline = deadline
            try:
                serial.reset_input_buffer()
                if time.monotonic() >= deadline:
                    raise PPMTimeoutError(cmd, self.last_response)
                data = (cmd + END_OF_LINE).encode("ascii")
                written = serial.write(data)
                if written != len(data):
                    raise PPMCommunicationError(
                        f"正压指令未完整写入: {written!r}/{len(data)}；指令可能已部分执行"
                    )
                while time.monotonic() < deadline:
                    chunk = serial.read(64)
                    if not isinstance(chunk, (bytes, bytearray)):
                        raise PPMCommunicationError("正压模块传输 read() 必须返回 bytes")
                    if not chunk:
                        # Offline/nonblocking transports must not busy-spin.
                        remaining = deadline - time.monotonic()
                        if remaining > 0:
                            time.sleep(min(0.001, remaining))
                        continue
                    response.extend(chunk)
                    if len(response) > self.max_response_bytes:
                        raise PPMCommunicationError("正压应答超过 max_response_bytes 限制")
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line_end = pending.index(b"\n") + 1
                        if line_end > self.max_line_bytes:
                            raise PPMCommunicationError("正压应答行超过 max_line_bytes 限制")
                        line = bytes(pending[:line_end])
                        del pending[:line_end]
                        try:
                            text_line = line.decode("utf-8", errors="strict")
                        except UnicodeDecodeError as exc:
                            raise PPMCommunicationError("正压应答包含无效 UTF-8 字节") from exc
                        self.last_response += text_line
                        if time.monotonic() >= deadline:
                            raise PPMTimeoutError(cmd, self.last_response)
                        if line.strip() == b"ok":
                            return self.last_response
                        if b"echo:busy" in line:
                            continue
                    if len(pending) > self.max_line_bytes:
                        raise PPMCommunicationError("正压应答行超过 max_line_bytes 限制")
                # A trailing fragment is diagnostic data, never a complete ACK.
                if pending:
                    try:
                        self.last_response += pending.decode("utf-8", errors="strict")
                    except UnicodeDecodeError as exc:
                        raise PPMCommunicationError("正压应答包含无效 UTF-8 字节") from exc
                raise PPMTimeoutError(cmd, self.last_response)
            except BaseException as exc:
                # ACK loss means uncertain execution. Close, but never resend C/D.
                self._serial = None
                try:
                    serial.close()
                except Exception:
                    pass
                if isinstance(exc, TimeoutError):
                    raise PPMTimeoutError(cmd, self.last_response) from exc
                if isinstance(exc, PPMCommunicationError) or not isinstance(exc, Exception):
                    raise
                raise PPMCommunicationError(
                    f"正压指令 {cmd!r} 通信失败；指令可能已执行，连接已失效: {exc}"
                ) from exc
            finally:
                if isinstance(serial, PressureCH340Transport):
                    serial._command_deadline = None

    def send_pressure_time(self, pressure: int, duration_ms: int) -> None:
        pressure_value = _ppm_integer("pressure (kPa)", pressure, 0)
        duration_value = _ppm_integer("duration_ms", duration_ms, 1)
        try:
            timeout = duration_value / 1000 + self.response_timeout
        except OverflowError:
            raise ValueError("duration_ms 转换为秒后必须为有限数") from None
        if not math.isfinite(timeout):
            raise ValueError("正压指令总等待时间必须为有限秒数")
        self._execute_command(f"C {pressure_value} {duration_value} 0 0", timeout)

    def reset_x_and_z(self) -> None:
        """Send the source's D command; reset axes are not established here."""
        self._execute_command("D", self.reset_timeout)


class PPMDevice(PPMController):
    """Opentrons adapter using seconds and SDK simulation isolation.

    ``int(seconds * 1000)`` retains the source's fractional-millisecond
    truncation.  Less than one millisecond is rejected.  In SDK simulation,
    send_pressure_time() only logs and calls context.delay(seconds=seconds);
    constructing, connecting, resetting, and closing never access USB.
    """

    def __init__(self, context: Any, **kwargs: Any):
        super().__init__(**kwargs)
        self._context = context
        self._simulate = bool(context.is_simulating())
        self._simulation_connected = False

    @property
    def connected(self) -> bool:
        if self._simulate:
            return self._simulation_connected
        return super().connected

    def connect(self) -> None:
        with self._io_lock:
            self._context.comment("连接正压模块")
            if self._simulate:
                self._simulation_connected = True
                return
            super().connect()

    def disconnect(self) -> None:
        with self._io_lock:
            try:
                self._context.comment("断开正压模块连接")
            finally:
                # Cleanup must still release USB if protocol logging is cancelled.
                if self._simulate:
                    self._simulation_connected = False
                else:
                    super().disconnect()

    def reset_x_and_z(self) -> None:
        with self._io_lock:
            self._context.comment("复位正压模块")
            if not self._simulate:
                super().reset_x_and_z()

    def send_pressure_time(self, pressure: int, seconds: float) -> None:
        pressure_value = _ppm_integer("pressure (kPa)", pressure, 0)
        seconds_value, duration_ms = _ppm_duration_ms(seconds)
        with self._io_lock:
            self._context.comment(f"正压启动: {pressure_value} kPa × {seconds_value:g} 秒")
            if self._simulate:
                self._context.delay(seconds=seconds_value)
                return
            super().send_pressure_time(pressure_value, duration_ms)
