"""Handwritten PyUSB CH340 transport extracted from the supplied tilt client.

Source SHA-256: 3f8af32d1f0257ef7990e3d68aecb52b16b9dd08fd7a7474b89e32ed3269b193

The default CH340 setup retains the tilt client's 115200 baud, 8/N/1 profile.
Device-specific subclasses may override ``_initialize_uart`` with a separately
evidenced setup; a shared chip does not establish identical serial settings.
This module only transports bytes, not commands, frames, CRCs, or motion.
Importing the module and constructing a transport do not discover or open USB
devices.  PyUSB is optional until USB operations are requested.

Ownership records live on ``usb.core`` so separate protocol imports in a
persistent Python process share them.  Only records whose weak owner is gone
or explicitly closed may be reclaimed.  A live owner is never assumed to be
a cancelled protocol; callers must close it explicitly before reuse.
"""

from __future__ import annotations

import threading
import time
import weakref
from typing import Any, Dict, Optional, Protocol

try:
    import usb.core as usb_core
    import usb.util as usb_util

    PYUSB_AVAILABLE = True
except ImportError:  # pragma: no cover - depends on runtime environment
    usb_core = None
    usb_util = None
    PYUSB_AVAILABLE = False


CH340_VID = 0x1A86
CH340_PID = 0x7523
BAUDRATE = 115200  # Base tilt profile only; not a claim about device subclasses.
_USB_HANDLE_REGISTRY_ATTR = "_ch340_transport_handle_registry"


class TransportError(RuntimeError):
    """USB transport, selection, or ownership error."""


class Transport(Protocol):
    is_open: bool

    def open(self) -> None: ...

    def close(self) -> None: ...

    def write(self, data: bytes) -> int: ...

    def read(self, size: int) -> bytes: ...

    def reset_input_buffer(self) -> None: ...

    def reset_output_buffer(self) -> None: ...

    def flush(self) -> None: ...


def enumerate_ch340_usb() -> list[Dict[str, Any]]:
    """Enumerate matching USB devices without claiming their interfaces."""

    if not PYUSB_AVAILABLE:
        return []
    devices = list(usb_core.find(find_all=True, idVendor=CH340_VID, idProduct=CH340_PID))
    return [
        {
            "bus": getattr(device, "bus", None),
            "address": getattr(device, "address", None),
            "port_numbers": getattr(device, "port_numbers", None),
            "device": device,
        }
        for device in devices
    ]


def select_ch340_usb(
    devices: list[Dict[str, Any]],
    *,
    usb_bus: Optional[int] = None,
    usb_address: Optional[int] = None,
    usb_port_numbers: Optional[tuple[int, ...]] = None,
) -> Optional[Dict[str, Any]]:
    """Select one matching device; never guess between multiple matches."""

    selected = list(devices)
    selectors_configured = any(
        value is not None for value in (usb_bus, usb_address, usb_port_numbers)
    )
    if usb_bus is not None:
        selected = [item for item in selected if item.get("bus") == usb_bus]
    if usb_address is not None:
        selected = [item for item in selected if item.get("address") == usb_address]
    if usb_port_numbers is not None:
        ports = tuple(usb_port_numbers)
        selected = [
            item
            for item in selected
            if tuple(item.get("port_numbers") or ()) == ports
        ]
    if len(selected) == 1:
        return selected[0]
    if len(selected) > 1:
        raise TransportError(
            "发现多个匹配的 CH340，拒绝自动选择；请配置 usb_bus/usb_port_numbers"
        )
    if selectors_configured:
        raise TransportError(
            "没有找到符合 USB 物理路径配置的 CH340: "
            f"bus={usb_bus}, address={usb_address}, port_numbers={usb_port_numbers}"
        )
    return None


def _device_identity(device: Any) -> tuple[Any, ...]:
    bus = getattr(device, "bus", None)
    ports = tuple(getattr(device, "port_numbers", None) or ())
    address = getattr(device, "address", None)
    if bus is not None and ports:
        return ("port", bus, ports)
    if bus is not None and address is not None:
        return ("address", bus, address)
    raise TransportError(
        "CH340 缺少 USB bus 与物理端口/address，无法可靠登记设备所有权"
    )


def _handle_registry() -> Dict[str, Any]:
    # setdefault shares the same registry even when this file is imported under
    # different module names in a persistent CPython protocol process.
    return vars(usb_core).setdefault(
        _USB_HANDLE_REGISTRY_ATTR,
        {"lock": threading.RLock(), "entries": {}},
    )


def _release_usb_device(device: Any, *, detached_kernel_driver: bool = False) -> None:
    if not PYUSB_AVAILABLE or device is None:
        return
    try:
        usb_util.release_interface(device, 0)
    except Exception:
        pass
    try:
        usb_util.dispose_resources(device)
    except Exception:
        pass
    if detached_kernel_driver:
        try:
            device.attach_kernel_driver(0)
        except Exception:
            pass


def _entry_is_active(entry: Dict[str, Any]) -> bool:
    owner = entry["owner"]()
    return owner is not None and bool(getattr(owner, "_ownership_active", False))


def _release_cached_entry(entry: Dict[str, Any]) -> None:
    _release_usb_device(
        entry["device"],
        detached_kernel_driver=entry.get("detached_kernel_driver", False),
    )


def clear_stale_ch340_usb_handles() -> int:
    """Release cached handles whose owners were collected or explicitly closed.

    No device discovery is performed, and records belonging to live, unclosed
    transports remain untouched.  Return the number of stale records removed.
    """

    if not PYUSB_AVAILABLE:
        return 0
    registry = _handle_registry()
    released = 0
    with registry["lock"]:
        entries = registry["entries"]
        for identity, entry in list(entries.items()):
            if not _entry_is_active(entry):
                _release_cached_entry(entry)
                del entries[identity]
                released += 1
    return released


class PyUsbCH340Transport:
    """CH340 byte transport; it does not depend on a tty/serial driver.

    ``open()`` is idempotent.  Different physical devices may be open at once;
    a second live owner for the same device raises ``TransportError``.  This
    object does not serialize a device protocol's higher-level transactions.
    """

    def __init__(self, device: Any = None, usb_timeout_ms: int = 200):
        if isinstance(usb_timeout_ms, bool) or not isinstance(usb_timeout_ms, int) or usb_timeout_ms <= 0:
            raise ValueError("usb_timeout_ms 必须是正整数毫秒数")
        self.dev = device
        self.usb_timeout_ms = usb_timeout_ms
        self.ep_out = None
        self.ep_in = None
        self.buffer = bytearray()
        self.is_open = False
        self._detached_kernel_driver = False
        self.interface_claimed = False
        self.stale_handle_released = False
        self._ownership_active = False
        self._registry_key: Optional[tuple[Any, ...]] = None
        self._registry_entry: Optional[Dict[str, Any]] = None

    def _reserve_device(self) -> None:
        identity = _device_identity(self.dev)
        registry = _handle_registry()
        with registry["lock"]:
            entries = registry["entries"]
            previous = entries.get(identity)
            if previous is not None:
                if _entry_is_active(previous):
                    raise TransportError(f"CH340 已被另一个活动 transport 占用: {identity}")
                _release_cached_entry(previous)
                del entries[identity]
                self.stale_handle_released = True
            entry = {
                "device": self.dev,
                "owner": weakref.ref(self),
                "detached_kernel_driver": False,
            }
            # Reserve before touching the device, so initialization in progress
            # is not mistaken for a closed owner by another transport.
            self._ownership_active = True
            self._registry_key = identity
            self._registry_entry = entry
            entries[identity] = entry

    def open(self) -> None:
        if self.is_open:
            return
        if self._ownership_active:
            raise TransportError("CH340 PyUSB 传输正在初始化")
        if not PYUSB_AVAILABLE:
            raise TransportError("当前环境没有 PyUSB")
        if self.dev is None:
            selected = select_ch340_usb(enumerate_ch340_usb())
            if selected is not None:
                self.dev = selected["device"]
        if self.dev is None:
            raise TransportError("没有找到 CH340 VID=1A86 PID=7523")

        self.stale_handle_released = False
        self._detached_kernel_driver = False
        self.interface_claimed = False
        self.ep_out = None
        self.ep_in = None
        self.buffer.clear()
        self._reserve_device()

        try:
            try:
                if self.dev.is_kernel_driver_active(0):
                    self.dev.detach_kernel_driver(0)
                    self._detached_kernel_driver = True
                    self._registry_entry["detached_kernel_driver"] = True
            except Exception:
                pass

            self.dev.set_configuration()
            usb_util.claim_interface(self.dev, 0)
            self.interface_claimed = True

            self._initialize_uart()

            cfg = self.dev.get_active_configuration()
            intf = cfg[(0, 0)]
            self.ep_out = usb_util.find_descriptor(
                intf,
                custom_match=lambda endpoint: usb_util.endpoint_direction(
                    endpoint.bEndpointAddress
                ) == usb_util.ENDPOINT_OUT,
            )
            self.ep_in = usb_util.find_descriptor(
                intf,
                custom_match=lambda endpoint: usb_util.endpoint_direction(
                    endpoint.bEndpointAddress
                ) == usb_util.ENDPOINT_IN,
            )
            if self.ep_out is None or self.ep_in is None:
                raise TransportError("无法找到 CH340 Bulk 输入/输出端点")
            for endpoint in (self.ep_in, self.ep_out):
                try:
                    self.dev.clear_halt(endpoint.bEndpointAddress)
                except Exception:
                    pass
            self.is_open = True
        except BaseException as exc:
            self.close()
            if isinstance(exc, TransportError):
                raise
            if isinstance(exc, Exception):
                raise TransportError(f"CH340 PyUSB 初始化失败: {exc}") from exc
            raise

    def _initialize_uart(self) -> None:
        """Retain the tilt source's fixed 115200/8N1 control transfers."""
        self.dev.ctrl_transfer(0x40, 0xA1, 0, 0)
        self.dev.ctrl_transfer(0x40, 0x9A, 0x1312, 0xCC83)
        self.dev.ctrl_transfer(0x40, 0x9A, 0x2518, 0x00C3)
        self.dev.ctrl_transfer(0x40, 0xA4, 0x00FF, 0)

    def close(self) -> None:
        if self._ownership_active:
            registry = _handle_registry()
            with registry["lock"]:
                try:
                    _release_usb_device(
                        self.dev,
                        detached_kernel_driver=self._detached_kernel_driver,
                    )
                finally:
                    entries = registry["entries"]
                    if entries.get(self._registry_key) is self._registry_entry:
                        del entries[self._registry_key]
                    self._ownership_active = False
        # Closing a never-opened or rejected transport must not release a
        # device that belongs to another transport.
        self.dev = None
        self.ep_out = None
        self.ep_in = None
        self.buffer.clear()
        self._detached_kernel_driver = False
        self.interface_claimed = False
        self.is_open = False
        self._registry_key = None
        self._registry_entry = None

    def write(self, data: bytes) -> int:
        if not self.is_open or self.ep_out is None:
            raise TransportError("CH340 PyUSB 传输尚未打开")
        return int(self.ep_out.write(data, timeout=1000))

    def _read_chunk_size(self, size: int) -> int:
        # Endpoint packet size is a USB transfer detail, not a device frame.
        return max(int(self.ep_in.wMaxPacketSize), size)

    def read(self, size: int) -> bytes:
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError("size 必须是非负整数")
        if not self.is_open or self.ep_in is None:
            raise TransportError("CH340 PyUSB 传输尚未打开")
        if size == 0:
            return b""
        if self.buffer:
            chunk = bytes(self.buffer[:size])
            del self.buffer[:size]
            return chunk
        try:
            raw = self.ep_in.read(self._read_chunk_size(size), timeout=self.usb_timeout_ms)
            data = bytes(raw)
        except usb_core.USBError as exc:
            if getattr(exc, "errno", None) in (60, 110) or "timeout" in str(exc).lower():
                return b""
            raise
        if len(data) > size:
            self.buffer.extend(data[size:])
            return data[:size]
        return data

    def reset_input_buffer(self) -> None:
        """Drain input within the configured USB timeout; reject continuous input."""
        self.buffer.clear()
        if not self.is_open or self.ep_in is None:
            return
        deadline = time.monotonic() + self.usb_timeout_ms / 1000
        while time.monotonic() < deadline:
            try:
                raw = self.ep_in.read(self._read_chunk_size(1), timeout=2)
                if not raw:
                    return
            except usb_core.USBError:
                return
        raise TransportError("输入持续到达，未能在 USB 等待窗口内清空缓冲区")

    def reset_output_buffer(self) -> None:
        # PyUSB writes are synchronous; this transport has no output queue.
        return None

    def flush(self) -> None:
        return None
