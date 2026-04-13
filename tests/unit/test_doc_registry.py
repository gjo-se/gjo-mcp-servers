"""Unit tests for doc_registry.py."""

from __future__ import annotations

import re

import pytest

from servers.doc_server.server import DOC_SOURCES
from servers.doc_server.tools.doc_registry import DOC_REGISTRY
from servers.web_search_server.tools.tavily_search import DOCUMENTATION_DOMAINS

VALID_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}(/.*)?$")
KNOWN_TOOLS = {
    "fetch_fastapi_docs",
    "fetch_pydantic_docs",
    "fetch_langchain_docs",
    "fetch_langgraph_docs",
    "fetch_fastmcp_docs",
    "fetch_pycharm_docs",
}


def test_all_doc_sources_have_registry_entry() -> None:
    """Every key in DOC_SOURCES must have a matching entry in DOC_REGISTRY."""
    for source_name in DOC_SOURCES:
        assert (
            source_name in DOC_REGISTRY
        ), f"DOC_SOURCES[{source_name!r}] has no entry in DOC_REGISTRY"


def test_llms_txt_entries_reference_known_tool() -> None:
    """Every llms_txt entry must reference a registered MCP tool."""
    for pkg, entry in DOC_REGISTRY.items():
        if entry["type"] == "llms_txt":
            assert (
                entry["tool"] in KNOWN_TOOLS
            ), f"DOC_REGISTRY[{pkg!r}] references unknown tool {entry['tool']!r}"


def test_web_search_entries_have_valid_domain_format() -> None:
    """Every web_search domain must be non-empty, whitespace-free, and valid-looking."""
    for pkg, entry in DOC_REGISTRY.items():
        if entry["type"] == "web_search":
            domain = entry["domain"]
            assert domain, f"DOC_REGISTRY[{pkg!r}] has empty domain"
            assert (
                " " not in domain
            ), f"DOC_REGISTRY[{pkg!r}] domain contains whitespace"
            assert (
                "." in domain
            ), f"DOC_REGISTRY[{pkg!r}] domain missing dot: {domain!r}"


def test_all_web_search_domains_in_documentation_domains() -> None:
    """Every web_search domain in DOC_REGISTRY must be listed
    in DOCUMENTATION_DOMAINS."""
    registry_domains = {
        entry["domain"]
        for entry in DOC_REGISTRY.values()
        if entry["type"] == "web_search"
    }
    for domain in registry_domains:
        assert (
            domain in DOCUMENTATION_DOMAINS
        ), f"DOC_REGISTRY domain {domain!r} missing from DOCUMENTATION_DOMAINS"


def test_package_names_are_normalized() -> None:
    """All DOC_REGISTRY keys must be lowercase and contain no whitespace."""
    for pkg in DOC_REGISTRY:
        assert pkg == pkg.lower(), f"Key {pkg!r} is not lowercase"
        assert " " not in pkg, f"Key {pkg!r} contains whitespace"


def test_syncfusion_domain_in_documentation_domains() -> None:
    """ej2.syncfusion.com must be listed in DOCUMENTATION_DOMAINS.

    Regression guard: ensures the Syncfusion domain is reachable via
    web_search_documentation and not accidentally removed from the allow-list.
    """
    assert "ej2.syncfusion.com" in DOCUMENTATION_DOMAINS


@pytest.mark.parametrize("source_name", list(DOC_SOURCES.keys()))
def test_each_doc_source_has_registry_entry(source_name: str) -> None:
    """Parametrized: each DOC_SOURCES key appears in DOC_REGISTRY."""
    assert source_name in DOC_REGISTRY
