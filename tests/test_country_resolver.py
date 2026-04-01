from core.country_resolver import CountryResolver, CountryResolverError


def test_country_resolver_returns_pakistan_adapter() -> None:
    resolver = CountryResolver()
    adapter = resolver.get_adapter("ORG_DEFAULT")

    assert adapter.tax_engine is not None
    assert adapter.compliance_engine is not None
    assert adapter.payroll_rules_engine is not None


def test_country_resolver_raises_when_org_mapping_missing() -> None:
    resolver = CountryResolver()

    try:
        resolver.get_adapter("ORG_UNKNOWN")
    except CountryResolverError as exc:
        assert exc.code == "ORG_COUNTRY_NOT_FOUND"
    else:
        raise AssertionError("expected CountryResolverError")
