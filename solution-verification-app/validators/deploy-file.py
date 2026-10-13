"""
Validator for "First Landing: Deploy a File" challenge.

Checks that /opt/island/beacon.txt exists and contains the expected text.
"""
from dataclasses import dataclass


@dataclass
class ValidationResult:
    success: bool
    message: str


EXPECTED_PATH = "/opt/island/beacon.txt"
EXPECTED_CONTENT = "the island welcomes you"


def validate(host: str, username: str, password: str, run_command) -> ValidationResult:
    exit_code, stdout, stderr = run_command(f"cat {EXPECTED_PATH}")

    if exit_code != 0:
        return ValidationResult(
            success=False,
            message=f"File {EXPECTED_PATH} does not exist. Deploy it using an Ansible playbook.",
        )

    content = stdout.strip()
    if content != EXPECTED_CONTENT:
        return ValidationResult(
            success=False,
            message=(
                f"File exists but contents don't match. "
                f"Expected exactly: '{EXPECTED_CONTENT}'"
            ),
        )

    return ValidationResult(
        success=True,
        message="File deployed correctly. Welcome to the island!",
    )
