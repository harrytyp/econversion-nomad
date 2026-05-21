"""elabFTW Dynamic Linker — Custom NOMAD Plugin.

**Origin:** Original code written for the econversion-nomad project.
**License:** MIT

This plugin extends the FAIRmat `nomad-external-eln-integrations` base plugin
with dynamic cross-linking capabilities. It is NOT part of the FAIRmat codebase.

Depends on:
- nomad-external-eln-integrations (FAIRmat, Apache 2.0) — for the base parser
- nomad-lab (FAIRmat/MPCDF, Apache 2.0) — the NOMAD SDK

Provides:
- ElabftwLinkedEntry  — custom ELN schema for storing elabFTW experiment refs
- ElabftwDynamicLink  — alias for backward compatibility
- elabftw_link_normalizer — normalizer hook for auto-resolving cross-refs
"""
from elabftw_linker.schema import ElabftwDynamicLink, ElabftwLinkedEntry
from elabftw_linker.normalizer import elabftw_link_normalizer

__all__ = [
    "ElabftwDynamicLink",
    "ElabftwLinkedEntry",
    "elabftw_link_normalizer",
]
