#!/usr/bin/env python3
"""Optional Flex HTTP client/CLI. No SDK, run creation or motion.

Contract/source notes and operator-facing wording: references/flex-http.md.
Only upload_protocol() writes to a robot, after explicit confirmation.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
import re
import secrets
import ssl
import threading
import time
from datetime import datetime, timezone
from http.client import HTTPException
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, ProxyHandler, Request, build_opener

HTTP_VERSION = "4"
MAX_BYTES = 32 * 1024 * 1024
RESOURCE_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")


class FlexHTTPError(Exception):
    """A structured failure; an uncertain POST must not be blindly retried."""

    def __init__(self, code, message, *, http_status=None, upload_may_have_succeeded=False, server_errors=None):
        super().__init__(message)
        self.code = code
        self.http_status = http_status
        self.upload_may_have_succeeded = upload_may_have_succeeded
        self.server_errors = server_errors

    def as_dict(self):
        return {"code": self.code, "message": str(self), "http_status": self.http_status,
                "upload_may_have_succeeded": self.upload_may_have_succeeded,
                "server_errors": self.server_errors}


class _NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _number(value, name, maximum):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= maximum:
        raise FlexHTTPError("invalid_argument", f"{name}必须为0到{maximum}之间的有限数值。")
    return float(value)


def _base_url(host):
    if not isinstance(host, str) or not host or any(c.isspace() for c in host):
        raise FlexHTTPError("invalid_host", "请提供设备IP、主机名或完整HTTP/HTTPS地址。")
    explicit_scheme = "://" in host
    try:
        parts = urlsplit(host if explicit_scheme else "http://" + host)
        port = parts.port
        if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.path not in {"", "/"} or parts.query or parts.fragment:
            raise ValueError
        # Bare host/IP uses the normal robot HTTP port; a full URL keeps its port.
        if not explicit_scheme and port is None:
            port = 31950
        address = f"[{parts.hostname}]" if ":" in parts.hostname else parts.hostname
        return f"{parts.scheme}://{address}" + (f":{port}" if port else "")
    except ValueError:
        raise FlexHTTPError("invalid_host", "设备地址不能包含账号、路径、查询参数或无效端口。") from None


def _id(value):
    if not isinstance(value, str) or not RESOURCE_ID.fullmatch(value):
        raise FlexHTTPError("invalid_id", "协议或分析ID格式无效。")
    return value


def _data(body, expected_type, label):
    if not isinstance(body, dict) or not isinstance(body.get("data"), expected_type):
        raise FlexHTTPError("invalid_response", f"设备返回的{label}格式与已维护契约不符。")
    return body["data"]


class FlexHTTPClient:
    def __init__(self, host, *, timeout=10, token=None, ca_file=None):
        self.base_url = _base_url(host)
        self.timeout = _number(timeout, "timeout", 60)
        if self.timeout == 0:
            raise FlexHTTPError("invalid_argument", "timeout必须大于0。")
        if token and urlsplit(self.base_url).scheme != "https":
            raise FlexHTTPError("https_required", "携带访问令牌时请使用设备支持的HTTPS地址。")
        if token and (not isinstance(token, str) or "\r" in token or "\n" in token):
            raise FlexHTTPError("invalid_token", "访问令牌格式无效。")
        self._token = token
        context = ssl.create_default_context(cafile=ca_file)
        self._opener = build_opener(ProxyHandler({}), _NoRedirects(), HTTPSHandler(context=context))

    def _request(self, method, path, *, body=None, content_type=None):
        allowed = method == "GET" and (path in {"/health", "/instruments", "/modules", "/deck_configuration"} or re.fullmatch(r"/protocols/[A-Za-z0-9_-]+(?:/analyses/[A-Za-z0-9_-]+)?", path))
        if not (allowed or (method == "POST" and path == "/protocols")):
            raise FlexHTTPError("unsupported_operation", "该操作不在本工具的已维护范围内。")
        headers = {"Opentrons-Version": HTTP_VERSION, "Accept": "application/json"}
        if content_type:
            headers["Content-Type"] = content_type
        if self._token:
            headers["Authorization"] = "Bearer " + self._token
        writing = method == "POST"
        req = Request(self.base_url + path, data=body, headers=headers, method=method)
        try:
            with self._opener.open(req, timeout=self.timeout) as response:
                served = response.headers.get("Opentrons-Version")
                # /health advertises the current server version; other routes negotiate.
                valid_version = served and served.isdigit() and (int(served) >= int(HTTP_VERSION) if path == "/health" else served == HTTP_VERSION)
                if not valid_version:
                    raise FlexHTTPError("unsupported_http_version", "设备未确认已维护的HTTP接口版本；不能将其视为本次操作已验证。", upload_may_have_succeeded=writing)
                raw = response.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise FlexHTTPError("response_too_large", "设备响应超出本工具的读取上限。", upload_may_have_succeeded=writing)
                result = json.loads(raw)
                if not isinstance(result, dict):
                    raise ValueError
                return result
        except HTTPError as exc:
            # Preserve useful API error details, not arbitrary HTML or credentials.
            server_errors = []
            try:
                payload = json.loads(exc.read(65536))
                for item in payload.get("errors", [])[:5]:
                    if isinstance(item, dict):
                        server_errors.append({k: str(item[k]).replace(self._token or "\0", "[redacted]")[:1000]
                                              for k in ("id", "title", "detail") if k in item})
            except (ValueError, AttributeError, TypeError, OSError, HTTPException):
                pass
            finally:
                exc.close()
            raise FlexHTTPError("http_error", f"设备返回HTTP {exc.code}；请核对连接、权限及设备返回的错误信息。", http_status=exc.code, upload_may_have_succeeded=writing and exc.code >= 500, server_errors=server_errors) from None
        except (URLError, TimeoutError, OSError, HTTPException):
            raise FlexHTTPError("connection_error", "未能完成与设备的通信；请核对地址、网络或设备状态。", upload_may_have_succeeded=writing) from None
        except (ValueError, UnicodeError):
            raise FlexHTTPError("invalid_response", "设备未返回有效的JSON对象。", upload_may_have_succeeded=writing) from None

    def device(self):
        health = self._request("GET", "/health")
        if health.get("robot_model") != "OT-3 Standard":
            raise FlexHTTPError("not_flex", "设备没有报告为已维护的Flex型号，停止本工具的后续操作。")
        if not isinstance(health.get("name"), str) or not health["name"].strip():
            raise FlexHTTPError("invalid_response", "设备没有返回有效的设备名称。")
        for key in ("maximum_protocol_api_version", "minimum_protocol_api_version"):
            value = health.get(key)
            if value is not None and (not isinstance(value, list) or len(value) != 2 or not all(type(n) is int and n >= 0 for n in value)):
                raise FlexHTTPError("invalid_response", "设备返回的协议API版本范围格式无效。")
        parts = urlsplit(self.base_url)
        try:
            ip = str(ipaddress.ip_address(parts.hostname))
        except ValueError:
            ip = None  # A hostname is not proof of a particular IP address.
        return {"name": health["name"], "host": parts.hostname, "ip_address": ip,
                "base_url": self.base_url, "serial": health.get("robot_serial"),
                "robot_model": health["robot_model"], "server_software": health.get("api_version"),
                "system_version": health.get("system_version"),
                "maximum_protocol_api_version": health.get("maximum_protocol_api_version"),
                "minimum_protocol_api_version": health.get("minimum_protocol_api_version")}

    def inspect(self):
        device = self.device()
        sections, errors = {}, {}
        for key, path, expected in [("instruments", "/instruments", list), ("modules", "/modules", list), ("saved_deck_configuration", "/deck_configuration", dict)]:
            try:
                sections[key] = _data(self._request("GET", path), expected, key)
            except FlexHTTPError as exc:
                sections[key] = None  # Unavailable is different from an empty list.
                errors[key] = exc.as_dict()
        return {"device": device, "read_status": "partial" if errors else "complete",
                "observed_at": datetime.now(timezone.utc).isoformat(), **sections,
                "section_errors": errors, "physical_layout_confirmed": False,
                "sources": {"instruments": "device_report", "modules": "device_report",
                            "saved_deck_configuration": "saved_configuration"}}

    def upload_protocol(self, protocol, *, expected_name, expected_serial=None,
                        labware=(), parameter_values=None, confirmed=False):
        if confirmed is not True:
            raise FlexHTTPError("confirmation_required", "请先取得向目标设备上传该协议的用户授权。")
        if not isinstance(expected_name, str) or not expected_name.strip():
            raise FlexHTTPError("target_required", "请使用已读取并由用户选定的设备名称。")
        if parameter_values is not None:
            if not isinstance(parameter_values, dict) or not all(isinstance(k, str) and type(v) in {bool, int, float, str} for k, v in parameter_values.items()):
                raise FlexHTTPError("invalid_parameters", "运行参数应为参数名到字符串、布尔或数值的映射。")
            try:
                values_json = json.dumps(parameter_values, allow_nan=False)
            except ValueError:
                raise FlexHTTPError("invalid_parameters", "运行参数必须使用有限数值。") from None
        paths = [Path(protocol), *(Path(p) for p in labware)]
        if paths[0].suffix.lower() != ".py" or any(p.suffix.lower() != ".json" for p in paths[1:]):
            raise FlexHTTPError("invalid_files", "本版支持一个Python协议及可选的自定义耗材JSON。")
        files, seen = [], set()
        for path in paths:
            if path.name in seen or any(c in path.name for c in '\r\n"\\'):
                raise FlexHTTPError("invalid_files", "上传文件名重复或包含不支持的字符。")
            seen.add(path.name)
            try:
                if path.stat().st_size > MAX_BYTES:
                    raise FlexHTTPError("files_too_large", "上传文件超出本工具的大小上限。")
                content = path.read_bytes()
            except OSError:
                raise FlexHTTPError("invalid_files", "无法读取待上传的本地文件。") from None
            files.append((path.name, content))
        if sum(len(b) for _, b in files) > MAX_BYTES:
            raise FlexHTTPError("files_too_large", "上传文件合计超出本工具的大小上限。")
        device = self.device()
        if device["name"] != expected_name or (expected_serial is not None and device["serial"] != expected_serial):
            raise FlexHTTPError("target_changed", "当前设备与选定的设备身份不一致，请重新核对上传目标。")
        boundary = "flex-" + secrets.token_hex(24)
        chunks = []
        for name, content in files:
            chunks.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode(), content, b"\r\n"])
        if parameter_values is not None:
            chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="runTimeParameterValues"\r\n\r\n{values_json}\r\n'.encode())
        chunks.append(f"--{boundary}--\r\n".encode())
        response = self._request("POST", "/protocols", body=b"".join(chunks), content_type=f"multipart/form-data; boundary={boundary}")
        try:
            data = _data(response, dict, "上传结果")
            protocol_id = _id(data.get("id"))
            if data.get("robotType") != "OT-3 Standard":
                raise ValueError
            summaries = data.get("analysisSummaries")
            if not isinstance(summaries, list) or not summaries or not isinstance(summaries[-1], dict):
                raise ValueError
            analysis_id = _id(summaries[-1].get("id"))
        except (FlexHTTPError, ValueError):
            raise FlexHTTPError("upload_result_unconfirmed", "设备可能已接收文件，但返回结果不足以确认协议及分析ID；请先核对设备端记录，不要直接重传。", upload_may_have_succeeded=True) from None
        return {"device": device, "upload_confirmed": True, "protocol_id": protocol_id,
                "analysis_id": analysis_id, "analysis_summary": summaries[-1],
                "files": [{"name": n, "sha256": hashlib.sha256(b).hexdigest()} for n, b in files],
                "requested_parameter_values": parameter_values,
                "run_created": False, "experiment_started": False}

    def analysis(self, protocol_id, analysis_id, *, wait_seconds=0):
        protocol_id, analysis_id = _id(protocol_id), _id(analysis_id)
        wait_seconds = _number(wait_seconds, "wait_seconds", 30)
        device = self.device()
        protocol = _data(self._request("GET", f"/protocols/{protocol_id}"), dict, "协议记录")
        if protocol.get("id") != protocol_id or protocol.get("robotType") != "OT-3 Standard" or not isinstance(protocol.get("analysisSummaries"), list) or not any(isinstance(a, dict) and a.get("id") == analysis_id for a in protocol["analysisSummaries"]):
            raise FlexHTTPError("analysis_mismatch", "该分析ID不在目标协议的分析记录中。")
        deadline = time.monotonic() + wait_seconds
        while True:
            data = _data(self._request("GET", f"/protocols/{protocol_id}/analyses/{analysis_id}"), dict, "分析结果")
            if data.get("id") != analysis_id or data.get("status") not in {"pending", "completed"}:
                raise FlexHTTPError("invalid_response", "设备返回的分析ID或状态与请求不符。")
            completed = data["status"] == "completed"
            if completed and (data.get("result") not in {"ok", "not-ok", "parameter-value-required"} or not isinstance(data.get("errors"), list) or data.get("robotType") not in {None, "OT-3 Standard"}):
                raise FlexHTTPError("invalid_response", "设备返回的完成分析结果不足以作出判断。")
            result = {"device": device, "protocol_id": protocol_id, "analysis_id": analysis_id,
                      "status": data["status"], "result": data.get("result"),
                      "passed": data["result"] == "ok" and not data["errors"] if completed else None,
                      "errors": data.get("errors"), "run_time_parameters": data.get("runTimeParameters"),
                      "command_count": len(data["commands"]) if isinstance(data.get("commands"), list) else None,
                      "verification_kind": "device_analysis", "experiment_started": False}
            remaining = deadline - time.monotonic()
            if completed or remaining <= 0:
                return result
            time.sleep(min(1, remaining))


def probe_devices(hosts, *, timeout=3):
    """Probe only explicit candidate addresses; no network-range or mDNS scan."""
    timeout = _number(timeout, "timeout", 60)
    if not timeout:
        raise FlexHTTPError("invalid_argument", "timeout必须大于0。")
    if isinstance(hosts, str):
        hosts = [hosts]
    if not isinstance(hosts, (list, tuple)) or not all(isinstance(h, str) for h in hosts):
        raise FlexHTTPError("invalid_argument", "请提供候选设备地址列表。")
    results = []
    for host in dict.fromkeys(hosts):
        try:
            results.append({"host": host, "verification_status": "verified_flex", "device": FlexHTTPClient(host, timeout=timeout).device()})
        except FlexHTTPError as exc:
            results.append({"host": host, "verification_status": "unsupported_model" if exc.code == "not_flex" else "unverified", "error": exc.as_dict()})
    return {"devices": results, "scope": "explicit_candidates_only", "target_selected": False}


def discover_devices(*, seconds=5, timeout=2, interfaces=None):
    """Browse the official HTTP service type, then verify candidate /health.

    Optional python-zeroconf dependency. Bound discovery and stop all resources.
    ``interfaces`` may restrict browsing to chosen local interfaces (also tests).
    """
    seconds = _number(seconds, "seconds", 15)
    timeout = _number(timeout, "timeout", 3)
    if not seconds or not timeout:
        raise FlexHTTPError("invalid_argument", "mDNS发现时间及请求超时必须大于0。")
    try:
        from zeroconf import IPVersion, ServiceBrowser, Zeroconf
    except ImportError:
        raise FlexHTTPError("mdns_dependency_missing", "mDNS发现需要可选依赖zeroconf；可安装对应requirements，或直接填写设备IP。") from None
    names, lock = set(), threading.Lock()

    class Listener:
        def add_service(self, zc, service_type, name):
            with lock:
                names.add(name)

        update_service = add_service

        def remove_service(self, zc, service_type, name):
            with lock:
                names.discard(name)

    zc = browser = None
    advertisements, candidates = [], []
    try:
        options = {"ip_version": IPVersion.V4Only, "use_asyncio": False}
        if interfaces is not None:
            options["interfaces"] = interfaces
        zc = Zeroconf(**options)
        browser = ServiceBrowser(zc, "_http._tcp.local.", listener=Listener())
        time.sleep(seconds)
        browser.cancel()
        browser = None
        with lock:
            found_names = sorted(names)
        resolve_deadline = time.monotonic() + 4
        resolved_names = 0
        for name in found_names:
            remaining = resolve_deadline - time.monotonic()
            if remaining <= 0 or len(candidates) >= 8:
                break
            resolved_names += 1
            info = zc.get_service_info("_http._tcp.local.", name, timeout=max(1, min(500, int(remaining * 1000))))
            if info is None or info.port != 31950:
                continue
            model = info.properties.get(b"robotModel")
            for address in info.parsed_addresses(IPVersion.V4Only):
                host = f"{address}:{info.port}"
                advertisements.append({"service_name": name, "ip_address": address,
                    "port": info.port, "advertised_model": model.decode("utf-8", errors="replace") if isinstance(model, bytes) else None})
                if host not in candidates:
                    candidates.append(host)
    except OSError:
        raise FlexHTTPError("mdns_unavailable", "当前环境无法完成mDNS发现；请核对网络/组播支持，或直接填写设备IP。") from None
    finally:
        try:
            if browser is not None:
                browser.cancel()
        finally:
            if zc is not None:
                zc.close()
    result = probe_devices(candidates[:8], timeout=timeout)
    result.update({"scope": "local_mdns_advertisements", "discovery_seconds": seconds,
                   "advertisements": advertisements,
                   "candidate_limit_reached": resolved_names < len(found_names) or len(candidates) > 8,
                   "empty_result_is_not_proof_of_no_devices": True})
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    probe = sub.add_parser("probe", help="只检查给定的候选地址，不扫描局域网")
    probe.add_argument("hosts", nargs="+")
    probe.add_argument("--timeout", type=float, default=3)
    discover = sub.add_parser("discover", help="按需通过mDNS查找设备并读取候选设备身份")
    discover.add_argument("--seconds", type=float, default=5)
    discover.add_argument("--timeout", type=float, default=2)
    for name in ["inspect", "upload", "analysis"]:
        command = sub.add_parser(name)
        command.add_argument("--host", required=True)
        command.add_argument("--timeout", type=float, default=10)
        command.add_argument("--ca-file")
        if name == "upload":
            command.add_argument("protocol")
            command.add_argument("--expected-name", required=True)
            command.add_argument("--expected-serial")
            command.add_argument("--labware", action="append", default=[])
            command.add_argument("--parameter-values", help="实际运行参数的JSON对象；省略则由设备采用默认值")
            command.add_argument("--confirm-upload", action="store_true")
        if name == "analysis":
            command.add_argument("--protocol-id", required=True)
            command.add_argument("--analysis-id", required=True)
            command.add_argument("--wait-seconds", type=float, default=0)
    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover_devices(seconds=args.seconds, timeout=args.timeout)
        elif args.command == "probe":
            result = probe_devices(args.hosts, timeout=args.timeout)
        else:
            client = FlexHTTPClient(args.host, timeout=args.timeout, token=os.environ.get("OPENTRONS_HTTP_TOKEN"), ca_file=args.ca_file)
            if args.command == "inspect":
                result = client.inspect()
            elif args.command == "upload":
                values = json.loads(args.parameter_values) if args.parameter_values is not None else None
                result = client.upload_protocol(args.protocol, expected_name=args.expected_name,
                    expected_serial=args.expected_serial, labware=args.labware,
                    parameter_values=values, confirmed=args.confirm_upload)
            else:
                result = client.analysis(args.protocol_id, args.analysis_id, wait_seconds=args.wait_seconds)
        print(json.dumps({"ok": True, "data": result}, ensure_ascii=False, allow_nan=False))
        return 0
    except FlexHTTPError as exc:
        print(json.dumps({"ok": False, "error": exc.as_dict()}, ensure_ascii=False))
        return 1
    except (OSError, ValueError, ssl.SSLError):
        print(json.dumps({"ok": False, "error": {"code": "local_input_error", "message": "请核对本地文件、JSON参数或证书配置。"}}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
