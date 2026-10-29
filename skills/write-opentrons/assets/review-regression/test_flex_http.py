"""Optional HTTP tool checks: local fake HTTP server and isolated mDNS fixtures.

No real robot, protocol execution or SDK simulation. Optional zeroconf test
advertises a synthetic service on loopback only; it does not discover lab hosts.
"""
import contextlib
import asyncio
import importlib.util
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import types
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.client import IncompleteRead
from unittest.mock import patch
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("flex_http_tool", ROOT / "scripts/flex_http.py")
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

HEALTH = {"name": "测试Flex", "robot_model": "OT-3 Standard", "robot_serial": "FLEX-TEST-1",
          "api_version": "10.0.0", "system_version": "10.0.0",
          "maximum_protocol_api_version": [2, 30], "minimum_protocol_api_version": [2, 15]}
PROTOCOL = {"id": "protocol-1", "robotType": "OT-3 Standard",
            "analysisSummaries": [{"id": "analysis-1", "status": "pending"}]}
COMPLETE = {"id": "analysis-1", "status": "completed", "result": "ok", "errors": [],
            "robotType": "OT-3 Standard", "runTimeParameters": [{"variableName": "dry_run", "value": "water"}], "commands": []}


class FakeRobot:
    def __enter__(self):
        self.calls = []
        self.routes = {
            ("GET", "/health"): (200, HEALTH),
            ("GET", "/instruments"): (200, {"data": [{"instrumentType": "pipette", "mount": "left", "ok": False}]}),
            ("GET", "/modules"): (200, {"data": []}),
            ("GET", "/deck_configuration"): (200, {"data": {"cutoutFixtures": [{"cutoutId": "cutoutD3", "cutoutFixtureId": "trashBinAdapter"}]}}),
            ("POST", "/protocols"): (201, {"data": PROTOCOL}),
            ("GET", "/protocols/protocol-1"): (200, {"data": PROTOCOL}),
            ("GET", "/protocols/protocol-1/analyses/analysis-1"): (200, {"data": COMPLETE}),
        }
        fixture = self

        class Handler(BaseHTTPRequestHandler):
            def handle_request(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                fixture.calls.append((self.command, self.path, dict(self.headers), body))
                response = fixture.routes.get((self.command, self.path), (404, {"errors": []}))
                status, payload, *extra = response
                if callable(payload):
                    payload = payload()
                self.send_response(status)
                headers = extra[0] if extra else {"Opentrons-Version": "4"}
                for name, value in headers.items():
                    self.send_header(name, value)
                raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            do_GET = do_POST = handle_request

            def log_message(self, *args):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.host = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=lambda: self.server.serve_forever(poll_interval=0.01), daemon=True)
        self.thread.start()
        return self

    def __exit__(self, *args):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class HTTPClientChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.protocol = Path(self.temp.name) / "示例.py"
        self.protocol.write_text('requirements = {"robotType": "Flex", "apiLevel": "2.30"}\n')

    def upload(self, client, **kwargs):
        return client.upload_protocol(self.protocol, expected_name=HEALTH["name"], expected_serial=HEALTH["robot_serial"], confirmed=True, **kwargs)

    def test_inspect_preserves_reported_vs_saved_and_bad_instrument(self):
        with FakeRobot() as robot:
            result = tool.FlexHTTPClient(robot.host).inspect()
        self.assertEqual(result["read_status"], "complete")
        self.assertFalse(result["physical_layout_confirmed"])
        self.assertFalse(result["instruments"][0]["ok"])
        self.assertEqual(result["sources"]["saved_deck_configuration"], "saved_configuration")
        self.assertEqual(result["device"]["ip_address"], "127.0.0.1")
        self.assertTrue(all(c[0] == "GET" for c in robot.calls))

    def test_unavailable_section_is_unknown_not_empty(self):
        with FakeRobot() as robot:
            robot.routes[("GET", "/modules")] = (503, {"errors": [{"id": "NotReady"}]})
            result = tool.FlexHTTPClient(robot.host).inspect()
        self.assertEqual(result["read_status"], "partial")
        self.assertIsNone(result["modules"])
        self.assertIn("modules", result["section_errors"])

    def test_other_robot_stops_after_health(self):
        with FakeRobot() as robot:
            robot.routes[("GET", "/health")] = (200, {**HEALTH, "robot_model": "other-model"})
            with self.assertRaises(tool.FlexHTTPError) as caught:
                tool.FlexHTTPClient(robot.host).inspect()
        self.assertEqual(caught.exception.code, "not_flex")
        self.assertEqual(len(robot.calls), 1)

    def test_upload_multipart_exact_files_and_runtime_values(self):
        labware = Path(self.temp.name) / "labware.json"
        labware.write_text('{"example":true}')
        with FakeRobot() as robot:
            result = self.upload(tool.FlexHTTPClient(robot.host), labware=[labware], parameter_values={"dry_run": "water"})
        post = next(c for c in robot.calls if c[0] == "POST")
        self.assertEqual(post[1], "/protocols")
        self.assertEqual(post[2]["Opentrons-Version"], "4")
        self.assertEqual(post[3].count(b'name="files"'), 2)
        self.assertIn(self.protocol.read_bytes(), post[3])
        self.assertIn(b'name="runTimeParameterValues"', post[3])
        self.assertEqual(result["protocol_id"], "protocol-1")
        self.assertEqual(result["analysis_id"], "analysis-1")
        self.assertFalse(result["run_created"])
        self.assertFalse(result["experiment_started"])
        self.assertNotIn("passed", result)

    def test_upload_requires_authorization_before_network(self):
        client = tool.FlexHTTPClient("192.0.2.10")
        with patch.object(client, "device", side_effect=AssertionError("must not connect")):
            with self.assertRaises(tool.FlexHTTPError) as caught:
                client.upload_protocol(self.protocol, expected_name="test")
        self.assertEqual(caught.exception.code, "confirmation_required")

    def test_changed_name_or_serial_prevents_post(self):
        for change in [{"name": "different"}, {"robot_serial": "different"}]:
            with self.subTest(change=change), FakeRobot() as robot:
                robot.routes[("GET", "/health")] = (200, {**HEALTH, **change})
                with self.assertRaises(tool.FlexHTTPError) as caught:
                    self.upload(tool.FlexHTTPClient(robot.host))
                self.assertFalse(any(c[0] == "POST" for c in robot.calls))
                self.assertEqual(caught.exception.code, "target_changed")

    def test_post_server_error_is_not_retried_or_claimed_absent(self):
        with FakeRobot() as robot:
            robot.routes[("POST", "/protocols")] = (500, {"errors": [{"id": "InternalError"}]})
            with self.assertRaises(tool.FlexHTTPError) as caught:
                self.upload(tool.FlexHTTPClient(robot.host))
        self.assertTrue(caught.exception.upload_may_have_succeeded)
        self.assertEqual(sum(c[0] == "POST" for c in robot.calls), 1)

    def test_malformed_post_result_remains_uncertain(self):
        with FakeRobot() as robot:
            robot.routes[("POST", "/protocols")] = (201, {"data": {"id": "protocol-1"}})
            with self.assertRaises(tool.FlexHTTPError) as caught:
                self.upload(tool.FlexHTTPClient(robot.host))
        self.assertEqual(caught.exception.code, "upload_result_unconfirmed")
        self.assertTrue(caught.exception.upload_may_have_succeeded)

    def test_interrupted_http_post_is_uncertain_and_not_retried(self):
        client = tool.FlexHTTPClient("192.0.2.10")
        with patch.object(client, "device", return_value={"name": HEALTH["name"], "serial": HEALTH["robot_serial"]}), patch.object(client._opener, "open", side_effect=IncompleteRead(b"partial", 20)) as request:
            with self.assertRaises(tool.FlexHTTPError) as caught:
                self.upload(client)
        self.assertEqual(caught.exception.code, "connection_error")
        self.assertTrue(caught.exception.upload_may_have_succeeded)
        self.assertEqual(request.call_count, 1)

    def test_invalid_probe_options_do_not_masquerade_as_device_failures(self):
        for timeout in [0, -1, float("nan")]:
            with self.assertRaises(tool.FlexHTTPError):
                tool.probe_devices(["192.0.2.10"], timeout=timeout)

    def test_interrupted_error_body_preserves_uncertain_post_status(self):
        client = tool.FlexHTTPClient("192.0.2.10")
        error = HTTPError(client.base_url + "/protocols", 500, "error", {}, io.BytesIO(b""))
        with patch.object(client, "device", return_value={"name": HEALTH["name"], "serial": HEALTH["robot_serial"]}), patch.object(error, "read", side_effect=IncompleteRead(b"partial", 20)), patch.object(client._opener, "open", side_effect=error):
            with self.assertRaises(tool.FlexHTTPError) as caught:
                self.upload(client)
        self.assertEqual(caught.exception.http_status, 500)
        self.assertTrue(caught.exception.upload_may_have_succeeded)

    def test_http_error_keeps_useful_details_not_credentials(self):
        with FakeRobot() as robot:
            robot.routes[("GET", "/health")] = (401, {"errors": [{"id": "Unauthorized", "detail": "secret-token"}]})
            client = tool.FlexHTTPClient(robot.host)
            client._token = "secret-token"  # Only the local fixture receives this token.
            with self.assertRaises(tool.FlexHTTPError) as caught:
                client.device()
        self.assertNotIn("secret-token", json.dumps(caught.exception.as_dict()))
        self.assertEqual(caught.exception.http_status, 401)

    def test_pending_and_incomplete_parameter_analysis_do_not_pass(self):
        records = [{"id": "analysis-1", "status": "pending"},
                   {**COMPLETE, "result": "parameter-value-required"},
                   {**COMPLETE, "result": "not-ok", "errors": [{"id": "error-1"}]}]
        for record in records:
            with self.subTest(record=record), FakeRobot() as robot:
                robot.routes[("GET", "/protocols/protocol-1/analyses/analysis-1")] = (200, {"data": record})
                result = tool.FlexHTTPClient(robot.host).analysis("protocol-1", "analysis-1")
                self.assertIsNot(result["passed"], True)

    def test_completed_ok_preserves_actual_parameters_and_is_device_analysis(self):
        with FakeRobot() as robot:
            result = tool.FlexHTTPClient(robot.host).analysis("protocol-1", "analysis-1")
        self.assertTrue(result["passed"])
        self.assertEqual(result["verification_kind"], "device_analysis")
        self.assertEqual(result["run_time_parameters"][0]["value"], "water")

    def test_analysis_id_must_belong_to_protocol(self):
        with FakeRobot() as robot:
            with self.assertRaises(tool.FlexHTTPError) as caught:
                tool.FlexHTTPClient(robot.host).analysis("protocol-1", "another-analysis")
        self.assertEqual(caught.exception.code, "analysis_mismatch")
        self.assertFalse(any("/analyses/" in c[1] for c in robot.calls))

    def test_invalid_ids_and_parameters_fail_before_writing(self):
        client = tool.FlexHTTPClient("192.0.2.10")
        for value in ["../runs", "a/b", "", "a?x=1"]:
            with self.assertRaises(tool.FlexHTTPError):
                client.analysis(value, "a")
        with self.assertRaises(tool.FlexHTTPError):
            self.upload(client, parameter_values={"x": float("nan")})

    def test_response_version_and_schema_fail_explicitly(self):
        for payload, headers in [(HEALTH, {"Opentrons-Version": "2"}), (b"not json", {"Opentrons-Version": "4"}), ({**HEALTH, "maximum_protocol_api_version": "2.30"}, {"Opentrons-Version": "4"})]:
            with self.subTest(payload=payload), FakeRobot() as robot:
                robot.routes[("GET", "/health")] = (200, payload, headers)
                with self.assertRaises(tool.FlexHTTPError):
                    tool.FlexHTTPClient(robot.host).device()

    def test_redirect_is_not_followed(self):
        with FakeRobot() as robot, FakeRobot() as other:
            robot.routes[("GET", "/health")] = (302, {}, {"Location": other.host + "/health"})
            with self.assertRaises(tool.FlexHTTPError):
                tool.FlexHTTPClient(robot.host).device()
            self.assertEqual(other.calls, [])

    def test_cli_json_success_and_failure(self):
        with FakeRobot() as robot, contextlib.redirect_stdout(io.StringIO()) as out:
            status = tool.main(["inspect", "--host", robot.host])
        self.assertEqual(status, 0)
        self.assertTrue(json.loads(out.getvalue())["ok"])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            status = tool.main(["upload", str(self.protocol), "--host", "192.0.2.10", "--expected-name", "test"])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(out.getvalue())["error"]["code"], "confirmation_required")

    def test_host_and_token_validation_and_manual_ipv6(self):
        self.assertEqual(tool._base_url("192.0.2.10"), "http://192.0.2.10:31950")
        self.assertEqual(tool._base_url("https://flex.local:32313/"), "https://flex.local:32313")
        self.assertEqual(tool._base_url("http://[::1]:31950"), "http://[::1]:31950")
        for host in ["http://name:password@host", "http://host/runs", "http://host?x=1", "file:///etc/passwd"]:
            with self.assertRaises(tool.FlexHTTPError):
                tool.FlexHTTPClient(host)
        with self.assertRaises(tool.FlexHTTPError):
            tool.FlexHTTPClient("192.0.2.10", token="secret")

    def test_local_file_errors_are_structured(self):
        with self.assertRaises(tool.FlexHTTPError) as caught:
            tool.FlexHTTPClient("192.0.2.10").upload_protocol(Path(self.temp.name)/"missing.py", expected_name="test", confirmed=True)
        self.assertEqual(caught.exception.code, "invalid_files")


def fake_zeroconf(infos):
    state = types.SimpleNamespace(closed=False, cancelled=False, queries=[])

    class ZC:
        def __init__(self, **kwargs):
            state.options = kwargs

        def get_service_info(self, service_type, name, timeout):
            state.queries.append((service_type, name, timeout))
            return infos[name]

        def close(self):
            state.closed = True

    class Browser:
        def __init__(self, zc, service_type, listener):
            state.service_type = service_type
            for name in infos:
                listener.add_service(zc, service_type, name)

        def cancel(self):
            state.cancelled = True

    module = types.SimpleNamespace(Zeroconf=ZC, ServiceBrowser=Browser, IPVersion=types.SimpleNamespace(V4Only=4))
    return module, state


class MDNSChecks(unittest.TestCase):
    def info(self, port=31950, addresses=("192.0.2.10",)):
        return types.SimpleNamespace(port=port, properties={b"robotModel": b"OT-3 Standard"}, parsed_addresses=lambda version: addresses)

    def test_mdns_filters_port_deduplicates_and_checks_health(self):
        module, state = fake_zeroconf({"printer": self.info(80), "robot": self.info(addresses=("192.0.2.10", "192.0.2.10"))})
        with patch.dict(sys.modules, {"zeroconf": module}), patch.object(tool.time, "sleep"), patch.object(tool.FlexHTTPClient, "device", return_value=HEALTH) as health:
            result = tool.discover_devices(seconds=0.1)
        self.assertEqual(state.service_type, "_http._tcp.local.")
        self.assertIs(state.options["use_asyncio"], False)
        self.assertEqual(health.call_count, 1)
        self.assertEqual(len(result["devices"]), 1)
        self.assertFalse(result["target_selected"])
        self.assertTrue(state.closed and state.cancelled)

    def test_many_other_http_services_do_not_hide_robot(self):
        infos={f"printer-{i}":self.info(80) for i in range(10)}
        infos["z-robot"]=self.info()
        module, state=fake_zeroconf(infos)
        with patch.dict(sys.modules, {"zeroconf":module}), patch.object(tool.time,"sleep"), patch.object(tool.FlexHTTPClient,"device",return_value=HEALTH):
            result=tool.discover_devices(seconds=0.1)
        self.assertEqual(len(result["devices"]),1)

    def test_advertisement_alone_is_not_verified_flex(self):
        module, state = fake_zeroconf({"robot": self.info()})
        with patch.dict(sys.modules, {"zeroconf": module}), patch.object(tool.time, "sleep"), patch.object(tool.FlexHTTPClient, "device", side_effect=tool.FlexHTTPError("http_error", "HTTP401")):
            result = tool.discover_devices(seconds=0.1)
        self.assertEqual(result["devices"][0]["verification_status"], "unverified")
        self.assertTrue(result["advertisements"])

    def test_empty_discovery_does_not_claim_no_devices(self):
        module, state = fake_zeroconf({})
        with patch.dict(sys.modules, {"zeroconf": module}), patch.object(tool.time, "sleep"):
            result = tool.discover_devices(seconds=0.1)
        self.assertEqual(result["devices"], [])
        self.assertTrue(result["empty_result_is_not_proof_of_no_devices"])

    def test_missing_dependency_is_actionable_without_installing(self):
        with patch.dict(sys.modules, {"zeroconf": None}), self.assertRaises(tool.FlexHTTPError) as caught:
            tool.discover_devices()
        self.assertEqual(caught.exception.code, "mdns_dependency_missing")

    @unittest.skipUnless(importlib.util.find_spec("zeroconf"), "optional zeroconf not installed")
    def test_real_zeroconf_synthetic_loopback_advertisement(self):
        self._loopback_advertisement(async_context=False)

    @unittest.skipUnless(importlib.util.find_spec("zeroconf"), "optional zeroconf not installed")
    def test_real_zeroconf_in_running_asyncio_loop(self):
        self._loopback_advertisement(async_context=True)

    def _loopback_advertisement(self, async_context):
        from zeroconf import IPVersion, ServiceInfo, Zeroconf
        name = "skill-test-" + uuid.uuid4().hex + "._http._tcp.local."
        publisher = Zeroconf(interfaces=["127.0.0.1"], ip_version=IPVersion.V4Only)
        info = ServiceInfo("_http._tcp.local.", name, addresses=[socket.inet_aton("127.0.0.1")], port=31950, properties={"robotModel": "OT-3 Standard"}, server="skill-test.local.")
        try:
            publisher.register_service(info)
            with patch.object(tool.FlexHTTPClient, "device", return_value=HEALTH):
                if async_context:
                    async def call():
                        return tool.discover_devices(seconds=5, interfaces=["127.0.0.1"])
                    result = asyncio.run(call())
                else:
                    result = tool.discover_devices(seconds=5, interfaces=["127.0.0.1"])
            self.assertTrue(any(a["service_name"] == name for a in result["advertisements"]))
        finally:
            publisher.unregister_service(info)
            publisher.close()


if __name__ == "__main__":
    unittest.main()
