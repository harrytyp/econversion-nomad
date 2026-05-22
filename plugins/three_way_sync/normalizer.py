"""elabFTW ↔ NOMAD bidirectional bridge.

API key resolution order:
  1. Entry-level config (typed by user for one-off use)
  2. User settings entry (set once in GUI, persists)
"""

from typing import Optional
from datetime import datetime, timezone
import requests


class ElabftwBridge:
    """Handles bidirectional communication with elabFTW API."""

    def __init__(self, archive, logger):
        self.archive = archive
        self.logger = logger
        self._api_key = None
        self._api_base = None

    @property
    def api_base(self) -> Optional[str]:
        if self._api_base:
            return self._api_base
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'api_base_url', None):
                self._api_base = data.config.api_base_url
                return self._api_base
        # Fallback to user settings
        self._api_base = self._from_settings('api_base_url',
                      'https://elntest.ub.tum.de/api/v2')
        return self._api_base

    @property
    def api_key(self) -> Optional[str]:
        if self._api_key:
            return self._api_key
        # 1. Entry-level key (explicit, per-entry)
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'api_key', None):
                self._api_key = data.config.api_key
                return self._api_key
        # 2. User settings entry (set once in GUI)
        key = self._from_settings('api_key')
        if key:
            self._api_key = key
            return self._api_key
        return None

    def _from_settings(self, key, default=None):
        """Read from the user's ElabftwSettings entry via NOMAD search."""
        try:
            from nomad.search import search, MetadataPagination
            user_id = None
            if self.archive.metadata and self.archive.metadata.main_author:
                user_id = self.archive.metadata.main_author.user_id
            result = search(
                owner="user" if user_id else "all",
                query={"entry_name": "elabFTW Settings"},
                pagination=MetadataPagination(page_size=1),
                user_id=user_id,
            )
            if result.pagination.total > 0 and result.data:
                entry = result.data[0]
                upload_id = entry.get("upload_id")
                entry_id = entry.get("entry_id")
                if upload_id and entry_id:
                    from nomad.datamodel import EntryArchive
                    from nomad.app.v1.routes.uploads import get_upload
                    # Fetch the full entry data
                    url = f"http://localhost:8000/nomad-oasis/api/v1/uploads/{upload_id}/archive/{entry_id}"
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        cfg = data.get("data", {}).get("config", {})
                        return cfg.get(key, default)
        except Exception as e:
            self.logger.debug(f"Settings lookup: {e}")
        return default

    def headers(self):
        return {"Authorization": self.api_key or ""}

    def _entity_type(self):
        data = self.archive.data
        if hasattr(data, 'config') and data.config:
            return getattr(data.config, 'entity_type', 'experiment') or 'experiment'
        return 'experiment'

    def _endpoint(self, entity_type, entity_id=None, suffix=""):
        base = self.api_base or 'https://elntest.ub.tum.de/api/v2'
        ep = f"{base}/items/{entity_id}" if entity_id else f"{base}/items"
        if entity_type != 'item':
            ep = f"{base}/experiments/{entity_id}" if entity_id else f"{base}/experiments"
        return ep + suffix

    def fetch_entity(self, entity_id: str, entity_type: str = None) -> Optional[dict]:
        etype = entity_type or self._entity_type()
        url = self._endpoint(etype, entity_id, "?format=json&json=true")
        try:
            resp = requests.get(url, headers=self.headers(), timeout=15)
            if resp.status_code == 200:
                return resp.json()
            self.logger.warning(f"Fetch {etype} {entity_id}: HTTP {resp.status_code}")
        except Exception as e:
            self.logger.error(f"Fetch {etype} {entity_id}: {e}")
        return None

    def create_entity(self, title: str, body: str = "", entity_type: str = None) -> Optional[str]:
        etype = entity_type or self._entity_type()
        url = self._endpoint(etype)
        try:
            resp = requests.post(url, headers=self.headers(), json={"title": title, "body": body}, timeout=15)
            if resp.status_code in (200, 201):
                return str(resp.json().get('id'))
        except Exception as e:
            self.logger.error(f"Create {etype}: {e}")
        return None

    def add_nomad_link_to_elabftw(self, entity_id: str, nomad_url: str, entity_type: str = None) -> bool:
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
            self.logger.error(f"Link-back {etype} {entity_id}: {e}")
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

        entity_type = 'experiment'
        if hasattr(data, 'config') and data.config:
            entity_type = getattr(data.config, 'entity_type', 'experiment') or 'experiment'

        if external_id:
            eid = str(external_id)
            logger.info(f"Bridge: linking to {entity_type} {eid}")
            entity = bridge.fetch_entity(eid, entity_type)
            if entity and nomad_url:
                bridge.add_nomad_link_to_elabftw(eid, nomad_url, entity_type)

        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'create_elabftw_experiment', False):
                title = getattr(metadata, 'entry_name', None) or getattr(data, 'title', 'NOMAD Entry') or 'NOMAD Entry'
                logger.info(f"Bridge: creating {entity_type} '{title}'")
                eid = bridge.create_entity(title=title, entity_type=entity_type)
                if eid:
                    metadata.external_id = eid
                    if nomad_url:
                        bridge.add_nomad_link_to_elabftw(eid, nomad_url, entity_type)
                    data.config.create_elabftw_experiment = False

        # Clear entry-level API key if user has settings saved
        if hasattr(data, 'config') and data.config:
            if getattr(data.config, 'api_key', None):
                if bridge._from_settings('api_key'):
                    data.config.api_key = None
                    logger.info("Bridge: cleared entry-level key (using saved settings)")

        return True
    except Exception as e:
        logger.warning(f"Bridge error: {e}")
        return None
