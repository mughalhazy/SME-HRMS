from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / 'deployment' / 're_qc_validate_security_compliance_lock.py'


def test_security_compliance_lock_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count('PASS:') == 12, result.stdout
    assert 'FAIL:' not in result.stdout, result.stdout
