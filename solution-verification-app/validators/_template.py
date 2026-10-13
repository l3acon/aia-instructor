"""
Validator template.

Each validator module must define a `validate` function with this signature:

    def validate(host: str, username: str, password: str, run_command) -> ValidationResult

Parameters:
    host        - FQDN or IP of the player's target machine
    username    - SSH username (playerN)
    password    - SSH password (same password used for CTFd/Gitea login)
    run_command - helper: run_command("cmd") -> (exit_code, stdout, stderr)
                  Executes the command via SSH on the player's host as root.

Returns:
    ValidationResult(success=True/False, message="...")

The run_command helper handles SSH connection setup. Just pass shell commands.
"""
from dataclasses import dataclass


@dataclass
class ValidationResult:
    success: bool
    message: str


def validate(host: str, username: str, password: str, run_command) -> ValidationResult:
    # Example: check that a file exists
    exit_code, stdout, stderr = run_command("cat /etc/hostname")
    if exit_code != 0:
        return ValidationResult(success=False, message="Could not read hostname")

    return ValidationResult(success=True, message="Validation passed")
