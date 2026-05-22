"""ELN schemas for elabFTW ↔ NOMAD bidirectional linking."""

# Package MUST be defined before section classes
# so NOMAD's metaclass can register them
from nomad.metainfo.metainfo import SchemaPackage

m_package = SchemaPackage(
    aliases=[
        "three_way_sync.schema:ElabftwLinkedEntry",
        "three_way_sync.schema:ElabftwMachineUpload",
    ]
)

from nomad.datamodel.data import EntryData, ElnIntegrationCategory
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.metainfo import Datetime, Quantity, Section, SubSection, MSection
from three_way_sync.normalizer import ElabftwBridge


class ElabftwExpRef(MSection):
    """Reference to a single elabFTW experiment."""
    elabftw_id = Quantity(type=str, description="elabFTW experiment ID", a_eln=ELNAnnotation(component="StringEditQuantity"))
    elabftw_url = Quantity(type=str, description="Full elabFTW experiment URL", a_eln=ELNAnnotation(component="URLEditQuantity"))
    elabftw_title = Quantity(type=str, description="Experiment title (auto-fetched)")
    sync_status = Quantity(type=str, description="pending/synced/error")
    last_synced = Quantity(type=Datetime, description="Last sync timestamp")


class ElabftwSyncConfig(MSection):
    """Configuration for elabFTW sync."""
    entity_type = Quantity(
        type=str,
        default="experiment",
        description="elabFTW entity type: experiment or item",
        a_eln=ELNAnnotation(component="StringEditQuantity"),
    )
    api_base_url = Quantity(type=str, description="elabFTW API URL", a_eln=ELNAnnotation(component="StringEditQuantity"))
    api_key = Quantity(type=str, description="elabFTW API key (cleared after sync)", a_eln=ELNAnnotation(component="StringEditQuantity", props=dict(type="password")))
    sync_now = Quantity(type=bool, default=False, description="Toggle to sync now", a_eln=ELNAnnotation(component="BoolEditQuantity"))
    create_elabftw_experiment = Quantity(type=bool, default=False, description="Create elabFTW experiment from this entry", a_eln=ELNAnnotation(component="BoolEditQuantity"))
    write_link_back = Quantity(type=bool, default=True, description="Write NOMAD URL back to elabFTW experiment", a_eln=ELNAnnotation(component="BoolEditQuantity"))


class ElabftwLinkedEntry(EntryData):
    """
    ELN entry that auto-links to elabFTW.

    Usage:
      1. Fill in config (API URL + key)
      2. Add experiment references under 'experiments'
      3. Toggle sync_now = true
      4. Save → normalizer fetches data, links bidirectionally
    """
    m_def = Section(label="elabFTW Linked Entry", categories=[ElnIntegrationCategory], a_eln=ELNAnnotation(overview=True))
    title = Quantity(type=str, description="Entry title", a_eln=ELNAnnotation(component="StringEditQuantity", overview=True))
    description = Quantity(type=str, description="Description", a_eln=ELNAnnotation(component="RichTextEditQuantity", overview=True))
    config = SubSection(sub_section=ElabftwSyncConfig)
    experiments = SubSection(sub_section=ElabftwExpRef, repeats=True)

    def normalize(self, archive, logger):
        super().normalize(archive, logger)
        bridge = ElabftwBridge(archive, logger)
        if not bridge.api_base or not bridge.api_key:
            return
        metadata = archive.metadata
        entry_id = metadata.entry_id if metadata else None
        upload_id = metadata.upload_id if metadata else None
        entry_name = metadata.entry_name if metadata else None
        nomad_url = (
            f"https://researchmcp.duckdns.org/nomad-oasis/gui/user/uploads/entry/{upload_id}/{entry_id}"
            if upload_id and entry_id else None
        )
        if self.config and self.config.sync_now:
            for exp_ref in self.experiments:
                if not exp_ref.elabftw_id:
                    continue
                exp = bridge.fetch_experiment(exp_ref.elabftw_id)
                if exp:
                    exp_ref.elabftw_title = exp.get("title", exp.get("name", ""))
                    exp_ref.sync_status = "synced"
                    from datetime import datetime, timezone
                    exp_ref.last_synced = datetime.now(timezone.utc)
                    if self.config.write_link_back and nomad_url:
                        bridge.add_nomad_link_to_elabftw(exp_ref.elabftw_id, nomad_url)
                else:
                    exp_ref.sync_status = "error"
            self.config.sync_now = False
        if self.config and self.config.create_elabftw_experiment:
            title = entry_name or self.title or "NOMAD Entry"
            exp_id = bridge.create_experiment(title=title, body=self.description or "")
            if exp_id:
                if metadata:
                    metadata.external_id = exp_id
                ref = ElabftwExpRef(elabftw_id=exp_id, elabftw_title=title, sync_status="created")
                self.experiments.append(ref)
                if self.config.write_link_back and nomad_url:
                    bridge.add_nomad_link_to_elabftw(exp_id, nomad_url)
            self.config.create_elabftw_experiment = False
        if self.config and self.config.api_key:
            self.config.api_key = None


class ElabftwMachineUpload(ElabftwLinkedEntry):
    """For automated machine uploads. Same as ElabftwLinkedEntry."""
    pass


m_package.init_metainfo()
