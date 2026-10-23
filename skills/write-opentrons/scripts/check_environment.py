"""Read-only probe of this Python environment; never connects to a robot or installs."""
import importlib.metadata
import importlib.util
import json
import re
import shutil
import subprocess
import sys


def run_probe(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                encoding='utf-8', errors='replace',
                                timeout=10, check=False)
        return {
            'command': command, 'returncode': result.returncode,
            'ok': result.returncode == 0,
            'stdout': result.stdout[-12000:], 'stderr': result.stderr[-4000:],
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        return {'command': command, 'ok': False,
                'error': f'{type(error).__name__}: {error}'}


def inspect_environment():
    try:
        version = importlib.metadata.version('opentrons')
    except importlib.metadata.PackageNotFoundError:
        version = None
    try:
        found = importlib.util.find_spec('opentrons') is not None
    except (ImportError, ValueError) as error:
        return {'scope': 'current_executor_only', 'python': sys.executable,
                'distribution_version': version, 'probe_error': str(error)}
    report = {
        'scope': 'current_executor_only', 'python': sys.executable,
        'python_version': sys.version.split()[0],
        'distribution_version': version, 'module_found': found,
        'max_supported_api': None, 'sdk_probe': None,
        'simulator_probes': [],
        'robot_software_version': None, 'robot_max_api': None,
    }
    if found:
        # Public API documented by the official simulation reference.
        probe = run_probe([
            sys.executable, '-B', '-c',
            'import json; from opentrons.protocol_api import MAX_SUPPORTED_VERSION; '
            'print(json.dumps({"max_supported_api": str(MAX_SUPPORTED_VERSION)}))',
        ])
        report['sdk_probe'] = probe
        if probe['ok']:
            try:
                api = json.loads(probe['stdout'].splitlines()[-1])['max_supported_api']
                if not isinstance(api, str) or not re.fullmatch(r'\d+\.\d+', api):
                    raise ValueError('Invalid API version')
                report['max_supported_api'] = api
            except (ValueError, KeyError, IndexError, TypeError):
                probe['ok'] = False
                probe['error'] = 'Could not read the SDK API limit; do not infer it.'
        module_help = run_probe([sys.executable, '-B', '-m', 'opentrons.simulate', '--help'])
        module_help['scope'] = 'same_python'
        report['simulator_probes'].append(module_help)
    cli = shutil.which('opentrons_simulate')
    if cli:
        cli_help = run_probe([cli, '--help'])
        cli_help['scope'] = 'path_entrypoint_interpreter_not_verified'
        report['simulator_probes'].append(cli_help)
    return report


if __name__ == '__main__':
    print(json.dumps(inspect_environment(), ensure_ascii=False, indent=2))
