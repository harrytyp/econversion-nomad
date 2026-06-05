"""Entry point for NOMAD plugin registration."""
from nomad.config.models.plugins import SchemaPackageEntryPoint, ParserEntryPoint

# Clean stale example_uploads/apps from _plugins to work around NOMAD v1.4.2
# shared-state bug where load_plugins() raises:
#   ValueError: Failed loading example_uploads/... Old style plugins are no longer supported.
try:
    from nomad.config import _plugins as _nomad_plugins
    if _nomad_plugins:
        _opts = _nomad_plugins.get("entry_points", {}).get("options", {})
        for _k in list(_opts.keys()):
            if _k.startswith("example_uploads/"):
                del _opts[_k]
except Exception:
    pass



class InstrumentDataEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from instrument_data.schema import m_package
        return m_package


instrument_schema = InstrumentDataEntryPoint(
    name="instrument-data",
    description="Instrument measurement schemas (TGA, DMA, FTIR, MS)",
)

class TgaParserEntryPoint(ParserEntryPoint):
    def load(self):
        from instrument_data.tga_parser import TgaParser
        return TgaParser()


tga_parser_entry_point = TgaParserEntryPoint(
    name="parsers/tga",
    description="Parser for TGA measurement CSV/TXT files",
    aliases=["parsers/tga"],
)
