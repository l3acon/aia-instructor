"""
Validator for "You found a treasure chest" challenge.

Checks that:
1. httpd (Apache) service is running
2. The web server is serving the expected treasure page
"""
from dataclasses import dataclass


@dataclass
class ValidationResult:
    success: bool
    message: str


def validate(host: str, username: str, password: str, run_command) -> ValidationResult:
    # Check httpd is installed and running
    exit_code, stdout, stderr = run_command("systemctl is-active httpd")
    if exit_code != 0 or "active" not in stdout.strip():
        return ValidationResult(
            success=False,
            message="Apache (httpd) is not running. Ensure your playbook starts the httpd service.",
        )

    # Check the web server is serving content with the expected flag
    exit_code, stdout, stderr = run_command("curl -s http://localhost")
    if exit_code != 0:
        return ValidationResult(
            success=False,
            message="Could not reach the web server on localhost. Is httpd listening on port 80?",
        )

    if "Ansible is simple powerful and agentless" not in stdout:
        return ValidationResult(
            success=False,
            message="Web server is running but not serving the expected treasure content.",
        )

    return ValidationResult(
        success=True,
        message="Apache is running and serving the treasure page. Well done!",
    )
