import os
import yaml
from pathlib import Path


class Settings:
    def __init__(self):
        self.hmac_secret = os.environ.get("VERIFIER_HMAC_SECRET", "change-me-in-production")
        self.players_file = Path(os.environ.get("VERIFIER_PLAYERS_FILE", "/config/players.yml"))
        self.validators_dir = Path(os.environ.get("VERIFIER_VALIDATORS_DIR", "/app/validators"))
        self.ssh_port = int(os.environ.get("VERIFIER_SSH_PORT", "22"))
        self.host_pattern = os.environ.get("VERIFIER_HOST_PATTERN", "{player}.{domain}")
        self.ssh_user_pattern = os.environ.get("VERIFIER_SSH_USER_PATTERN", "{player}")
        self.domain = os.environ.get("VERIFIER_DOMAIN", "")

        self._players = None
        self._token_map = None

    @property
    def players(self) -> dict:
        """Load player data: {playerN: {password: ..., token: ...}}"""
        if self._players is None:
            self._players = self._load_players()
        return self._players

    @property
    def token_map(self) -> dict:
        """Reverse map: {token: playerN}"""
        if self._token_map is None:
            self._token_map = {
                info["token"]: name
                for name, info in self.players.items()
                if info.get("token")
            }
        return self._token_map

    def _load_players(self) -> dict:
        if not self.players_file.exists():
            return {}
        with open(self.players_file) as f:
            data = yaml.safe_load(f)
        passwords = data.get("players", {})
        tokens = data.get("tokens", {})
        players = {}
        for name, password in passwords.items():
            players[name] = {
                "password": str(password),
                "token": tokens.get(name, ""),
            }
        return players

    def get_player_host(self, player_name: str) -> str:
        return self.host_pattern.format(player=player_name, domain=self.domain)

    def get_ssh_user(self, player_name: str) -> str:
        return self.ssh_user_pattern.format(player=player_name, domain=self.domain)

    def reload(self):
        self._players = None
        self._token_map = None


settings = Settings()
