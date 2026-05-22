"""elabFTW ↔ NOMAD bidirectional bridge.

Normalizer that runs inside NOMAD to auto-link entries with elabFTW.
Supports both experiments and database items (resources).
API keys come from: entry config > per-user config > shared config.
"""

from typing import Optional
from datetime import datetime, timezone
from pathlib import Path
import requests


class ElabftwBridge:
    """Handles bidirectional communication with elabFTW API."""

    def __init__(self, archive, logger):
        self.archive = archive
        self.logger = logger
        self._api_key = None
        self._api_base = None
        self._username = None

    @property
    def username(self) -> Optional[str]:
        if self._username:
            return self._username
        if self.archive.metadata and self.archive.metadata.main_author:
            self._username = self.archive.metadata.main_author.user_id
        return self._username

    @property
    def api_base(self) -> Optional[str]:
        if self._api_base:
            return self._api_base
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'api_base_url', None):
                self._api_base = data.config.api_base_url
                return self._api_base
        self._api_base = self._from_config('elabftw', 'api_url', 'https://elntest.ub.tum.de/api/v2')
        return self._api_base

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        # 1. Check entry config (explicit key on this entry)
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'api_key', None):
                self._api_key = data.config.api_key
                if self._api_key:
                    return self._api_key
        # 2. Check per-user config
        user_key = self._from_user_config('elabftw', 'api_key')
        if user_key:
            self._api_key = user_key
            return self._api_key
        # 3. Fall back to shared config
        self._api_key = self._from_config('elabftw', 'api_key', '')
        return self._api_key

    def _from_config(self, section, key, default=None):
        """Read from shared config.yaml."""
        path = '/app/plugins/three_way_sync/config.yaml'
        if Path(path).exists():
            import yaml
            with open(path) as f:
                cfg = yaml.safe_load(f)
            return cfg.get(section, {}).get(key, default)
        return default

    def _from_user_config(self, section, key, default=None):
        """Read from per-user config at configs/{username}.yaml."""
        if not self.username:
            return default
        path = f'/app/plugins/three_way_sync/configs/{self.username}.yaml'
        if Path(path).exists():
            import yaml
            with open(path) as f:
                cfg = yaml.safe_load(f)
            return cfg.get(section, {}).get(key, default)
        return default

    def headers(self):
        return {"Authorization": self.api_key or ""}

    def _entity_type(self):
        """Determine entity type from entry data."""
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            etype = getattr(data.config, 'entity_type', 'experiment') or 'experiment'
            return etype
        return 'experiment'

    def _endpoint(self, entity_type, entity_id=None, suffix=""):
        """Build the right API endpoint for experiment or item."""
        base = self.api_base or 'https://elntest.ub.tum.de/api/v2'
        if entity_type == 'item':
            ep = f"{base}/items/{entity_id}" if entity_id else f"{base}/items"
        else:
            ep = f"{base}/experiments/{entity_id}" if entity_id else f"{base}/experiments"
        return ep + suffix

    def fetch_entity(self, entity_id: str, entity_type: str = None) -> Optional[dict]:
        """Fetch an experiment or item from elabFTW."""
        etype = entity_type or self._entity_type()
        url = self._endpoint(etype, entity_id, "?format=json&json=true")
        try:
            resp = requests.get(url, headers=self.headers(), timeout=15)
            if resp.status_code == 200:
                return resp.json()
            self.logger.warning(f"elabFTW fetch {etype} {entity_id}: HTTP {resp.status_code}")
        except Exception as e:
            self.logger.error(f"elabFTW fetch {etype} {entity_id}: {e}")
        return None

    def create_entity(self, title: str, body: str = "", entity_type: str = None) -> Optional[str]:
        """Create an experiment or item in elabFTW."""
        etype = entity_type or self._entity_type()
        url = self._endpoint(etype)
        try:
            resp = requests.post(url, headers=self.headers(), json={"title": title, "body": body}, timeout=15)
            if resp.status_code in (200, 201):
                return str(resp.json().get('id'))
        except Exception as e:
            self.logger.error(f"elabFTW create {etype}: {e}")
        return None

    def add_nomad_link_to_elabftw(self, entity_id: str, nomad_url: str, entity_type: str = None) -> bool:
        """Write NOMAD URL back into elabFTW as extra field."""
        etype = entity_type or self._entity_type()
        extra = {"NOMAD URL": nomad_url, "NOMAD Synced": datetime.now(timezone.utc).isoformat()}
        try:
            resp = requests.put(
                self._endpoint(etype, entity_id),
                headers=self.headers(),
                json={"extra_fields": extra},
                timeout=15,
            )
            return resp.status_code in (200, 201)
        except Exception as e:
            self.logger.error(f"elabFTW link-back {etype} {entity_id}: {e}")
        return False


def normalize(archive, logger) -> Optional[bool]:
    """NOMAD normalizer — auto-links entries with elabFTW."""
    try:
        bridge = ElabftwBridge(archive, logger)
        if not bridge.api_base or not bridge.api_key:
            return None

        metadata = archive.metadata
        if not metadata:
            return None
        data = archive.data

        external_id = getattr(metadata, 'external_id', None)
        entry_id = getattr(metadata, 'entry_id', None)
        upload_id = getattr(metadata, 'upload_id', None)

        nomad_url = (
            f"https://researchmcp.duckdns.org/nomad-oasis/gui/user/uploads/entry/{upload_id}/{entry_id}"
            if upload_id and entry_id else None
        )

        # Determine entity type from config
        entity_type = 'experiment'
        if hasattr(data, 'config') and data.config:
            entity_type = getattr(data.config, 'entity_type', 'experiment') or 'experiment'

        # Case: external_id set → link to existing entity
        if external_id:
            eid = str(external_id)
            logger.info(f"Bridge: linking to elabFTW {entity_type} {eid}")
            entity = bridge.fetch_entity(eid, entity_type)
            if entity and nomad_url:
                bridge.add_nomad_link_to_elabftw(eid, nomad_url, entity_type)
                logger.info(f"Bridge: wrote NOMAD link back to {entity_type} {eid}")

        # Case: auto-create flag
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'create_elabftw_experiment', False):
                title = getattr(metadata, 'entry_name', None) or getattr(data, 'title', 'NOMAD Entry') or 'NOMAD Entry'
                logger.info(f"Bridge: creating elabFTW {entity_type} for '{title}'")
                eid = bridge.create_entity(title=title, entity_type=entity_type)
                if eid:
                    metadata.external_id = eid
                    if nomad_url:
                        bridge.add_nomad_link_to_elabftw(eid, nomad_url, entity_type)
                    data.config.create_elabftw_experiment = False

        # Clear API key from entry data if it was explicitly filled
        if hasattr(data, 'config') and data.config:
            if hasattr(data.config, 'api_key') and data.config.api_key:
                api_in_entry = data.config.api_key
                # Only clear if user has a saved config (so they don't need to retype)
                if bridge._from_user_config('elabftw', 'api_key'):
                    data.config.api_key = None

        return True
    except Exception as e:
        logger.warning(f"Bridge error: {e}")
        return None
