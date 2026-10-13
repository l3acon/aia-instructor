import importlib.util
import logging
from pathlib import Path
from dataclasses import dataclass

import paramiko

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    success: bool
    message: str


def list_challenges() -> list[str]:
    """Return available challenge slugs based on validator files."""
    validators_dir = settings.validators_dir
    if not validators_dir.exists():
        return []
    return sorted(
        p.stem for p in validators_dir.glob("*.py") if not p.name.startswith("_")
    )


def run_ssh_command(host: str, username: str, password: str, command: str) -> tuple[int, str, str]:
    """Execute a command on a remote host via SSH. Returns (exit_code, stdout, stderr)."""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(
            hostname=host,
            port=settings.ssh_port,
            username=username,
            password=password,
            timeout=15,
            look_for_keys=False,
            allow_agent=False,
        )
        stdin, stdout, stderr = client.exec_command(command, timeout=30)
        exit_code = stdout.channel.recv_exit_status()
        return exit_code, stdout.read().decode(), stderr.read().decode()
    finally:
        client.close()


def validate_challenge(challenge: str, player_name: str) -> ValidationResult:
    """Load and execute the validator script for the given challenge."""
    validator_path = settings.validators_dir / f"{challenge}.py"
    if not validator_path.exists():
        return ValidationResult(
            success=False,
            message=f"Unknown challenge: {challenge}",
        )

    player_info = settings.players.get(player_name)
    if not player_info:
        return ValidationResult(
            success=False,
            message=f"Unknown player: {player_name}",
        )

    host = settings.get_player_host(player_name)
    username = settings.get_ssh_user(player_name)
    password = player_info["password"]

    spec = importlib.util.spec_from_file_location(f"validator_{challenge}", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    if not hasattr(module, "validate"):
        return ValidationResult(
            success=False,
            message=f"Validator for '{challenge}' is misconfigured (missing validate function)",
        )

    try:
        return module.validate(
            host=host,
            username=username,
            password=password,
            run_command=lambda cmd: run_ssh_command(host, username, password, cmd),
        )
    except paramiko.AuthenticationException:
        return ValidationResult(
            success=False,
            message=f"Authentication failed connecting to {host}. Verify your environment is running.",
        )
    except Exception as e:
        logger.exception("Validator error for %s/%s", challenge, player_name)
        return ValidationResult(
            success=False,
            message=f"Validation error: {e}",
        )
