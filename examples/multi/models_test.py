import re
import pytest
import urllib

from .models import (
    AttributeBooleanExpression,
    AttributeDefinition,
    AttributeInstance,
    AttributeService,
    BooleanKeyExpression,
    ConfigurationService,
    EncryptionMapping,
    KeyAccessGrant,
    KeyClause,
    PublicKeyInfo,
    Reasoner,
    Rule,
    SingleAttributeClause,
    WebError,
    reduce,
)

classDef = AttributeDefinition(
    authority="https://virtru.com/",
    name="Classification",
    order=[
        "Top Secret",
        "Secret",
        "Confidential",
        "For Official Use Only",
        "Open",
    ],
    rule=Rule.hierarchy,
)

relToDef = AttributeDefinition(
    authority="https://virtru.com",
    name="Releasable To",
    order=[
        "FVEY",
        "AUS",
        "CAN",
        "GBR",
        "NZL",
        "USA",
    ],
    rule=Rule.anyOf,
)

needToKnowDef = AttributeDefinition(
    authority="https://virtru.co.us/",
    name="Need to Know",
    order=[
        "INT",
        "SI",
        "OTHER",
        "FORGOTTEN",
    ],
    rule=Rule.allOf,
)


def test_definition_sample():
    assert classDef.prefix() == "https://virtru.com/attr/Classification"
    assert needToKnowDef.prefix() == "https://virtru.co.us/attr/Need+to+Know"
    assert relToDef.prefix() == "https://virtru.com/attr/Releasable+To"


def test_definition_pathfix():
    for authority, prefix in [
        ("http://e", "http://e/attr/n"),
        ("https://e", "https://e/attr/n"),
        ("http://e/", "http://e/attr/n"),
        ("http://e/hello", "http://e/hello/attr/n"),
        ("http://e/hello/", "http://e/hello/attr/n"),
        ("http://e/a+b", "http://e/a+b/attr/n"),
        ("http://e/a++/", "http://e/a++/attr/n"),
    ]:
        assert (
            AttributeDefinition(
                authority=authority,
                name="n",
                order=[
                    "INT",
                    "SI",
                ],
                rule=Rule.allOf,
            ).prefix()
            == prefix
        )


def test_instance_str():
    for a, n, v, s in [
        ("http://e", "a", "1", "http://e/attr/a/value/1"),
        ("https://e/", "a", "1", "https://e/attr/a/value/1"),
        ("http://e", "attr", "value", "http://e/attr/attr/value/value"),
        ("http://e", "value", "attr", "http://e/attr/value/value/attr"),
        ("http://e", "a b", "1", "http://e/attr/a+b/value/1"),
        ("http://e", "hello there%", "#", "http://e/attr/hello+there%25/value/%23"),
    ]:
        assert str(AttributeInstance(authority=a, name=n, value=v)) == s


def test_instance_from_url():
    for u in ["http://e/attr/a/value/1"]:
        assert AttributeInstance.from_url(u).__str__() == u
        assert str(AttributeInstance.from_url(u).authority) == "http://e/"
        assert AttributeInstance.from_url(u).name == "a"
        assert AttributeInstance.from_url(u).value == "1"


def test_attribute_service():
    s = AttributeService()
    for d in [classDef, needToKnowDef, relToDef]:
        s.put_attribute(d)
    assert s.get_attribute(classDef.prefix()) == classDef
    assert s.get_attribute(relToDef.prefix()) == relToDef
    with pytest.raises(WebError):
        s.get_attribute("undefined")
    assert s.get_attribute("https://virtru.com/attr/Classification") == classDef
    assert s.get_attribute("https://virtru.com/attr/Releasable+To") == relToDef
    assert s.get_attribute("https://virtru.co.us/attr/Need+to+Know") == needToKnowDef


ca_kas = EncryptionMapping(
    kas="KAS-CAN-1",
    grants=[
        KeyAccessGrant(
            attr="https://virtru.com/attr/Releasable+To",
            values=["CAN"],
        ),
    ],
)
fvey_kas = EncryptionMapping(
    kas="KAS-FVEY-1",
    grants=[
        KeyAccessGrant(
            attr="https://virtru.com/attr/Releasable+To",
            values=["FVEY"],
        ),
    ],
)
us_kas = EncryptionMapping(
    kas="KAS-USA-1",
    grants=[
        KeyAccessGrant(
            attr="https://virtru.co.us/attr/Need+to+Know",
            values=["HCS", "SI"],
        ),
        KeyAccessGrant(
            attr="https://virtru.com/attr/Releasable+To",
            values=["USA"],
        ),
    ],
)
uk_kas = EncryptionMapping(
    kas="KAS-GBR-1",
    grants=[
        KeyAccessGrant(
            attr="https://virtru.co.us/attr/Need+to+Know",
            values=["INT"],
        ),
        KeyAccessGrant(
            attr="https://virtru.com/attr/Releasable+To",
            values=["GBR"],
        ),
    ],
)


def test_configuration_service():
    c = ConfigurationService()
    c.put_mapping(us_kas)
    c.put_mapping(uk_kas)
    with pytest.raises(WebError):
        c.get_mappings("https://virtru.com/attr/Classification")
    assert len(c.get_mappings("https://virtru.com/attr/Releasable+To")) == 2
    assert len(c.get_mappings("https://virtru.co.us/attr/Need+to+Know")) == 2


cfg_svc = ConfigurationService()
for e in [ca_kas, fvey_kas, uk_kas, us_kas]:
    cfg_svc.put_mapping(e)
attr_svc = AttributeService()
for d in [classDef, needToKnowDef, relToDef]:
    attr_svc.put_attribute(d)


AUTHORITIES = {
    "Classification": "https://virtru.com/",
    "Need to Know": "https://virtru.co.us/",
    "Releasable To": "https://virtru.com/",
}

VSHORT_NAMES = {"Classification": "CLS", "Need to Know": "N2K", "Releasable To": "REL"}
SHORT_VALUES = {
    "Top Secret": "TS",
    "Secret": "S",
    "Confidential": "CNF",
    "For Official Use Only": "FOUO",
    "Open": "O",
}
UNSHORT = {}
for l in [VSHORT_NAMES, SHORT_VALUES]:
    for k, v in l.items():
        UNSHORT[v] = k


def vshort(a: AttributeInstance) -> str:
    return f"{VSHORT_NAMES[a.name]}:{SHORT_VALUES.get(a.value, a.value)}"


def unshorten(s: str) -> AttributeInstance:
    m = re.fullmatch(
        r"(?P<name>[^:]+):(?P<value>[^:]+)",
        s,
    )
    if not m:
        raise ValueError(m)
    name = m.group("name")
    if name not in UNSHORT:
        raise ValueError(
            f"Unrecognized name: [{name}]; not found in [{list(UNSHORT.keys())}]"
        )
    name = UNSHORT[name]
    value = m.group("value")
    value = UNSHORT.get(value, value)
    return AttributeInstance(
        authority=AUTHORITIES[name],
        name=name,
        value=value,
    )


def lookup_def(name: str) -> AttributeInstance:
    name = UNSHORT.get(name, name)
    return attr_svc.get_attribute(
        f"{AUTHORITIES[name]}attr/{urllib.parse.quote_plus(name)}"
    )


def expand(e: dict[str, list[str]]):
    return AttributeBooleanExpression(
        must=[
            SingleAttributeClause(
                definition=lookup_def(n),
                values=[unshorten(f"{n}:{v}") for v in clause],
            )
            for n, clause in e.items()
        ]
    )


def test_construct_attr_boolean():
    reasoner = Reasoner(attr_svc, cfg_svc)
    policy1 = [
        unshorten(x)
        for x in [
            "CLS:S",
            "REL:GBR",
            "N2K:INT",
        ]
    ]
    ab1 = reasoner.construct_attribute_boolean(policy=policy1)
    assert ab1 == expand({"CLS": ["S"], "REL": ["GBR"], "N2K": ["INT"]})
    b1 = reasoner.insert_keys_for_attribute_value(ab1)
    assert str(b1) == "[DEFAULT]&(KAS-GBR-1)&(KAS-GBR-1)"
    assert str(reduce(b1)) == "(KAS-GBR-1)"

    assert ab1 == AttributeBooleanExpression(
        must=[
            SingleAttributeClause(
                definition=classDef,
                values=[
                    AttributeInstance.from_url(
                        "https://virtru.com/attr/Classification/value/Secret"
                    )
                ],
            ),
            SingleAttributeClause(
                definition=relToDef,
                values=[
                    AttributeInstance.from_url(
                        "https://virtru.com/attr/Releasable+To/value/GBR"
                    )
                ],
            ),
            SingleAttributeClause(
                definition=needToKnowDef,
                values=[
                    AttributeInstance.from_url(
                        "https://virtru.co.us/attr/Need+to+Know/value/INT"
                    )
                ],
            ),
        ]
    )
    policy2 = [
        unshorten(x)
        for x in [
            "CLS:S",
            "REL:FVEY",
        ]
    ]
    ab2 = reasoner.construct_attribute_boolean(policy=policy2)
    assert ab2 == expand({"CLS": ["S"], "REL": ["FVEY"]})
    b2 = reasoner.insert_keys_for_attribute_value(ab2)
    assert str(b2) == "[DEFAULT]&(KAS-FVEY-1)"
    assert str(reduce(b2)) == "(KAS-FVEY-1)"

    policy3 = [
        unshorten(x)
        for x in [
            "CLS:S",
            "REL:CAN",
            "REL:GBR",
        ]
    ]
    ab3 = reasoner.construct_attribute_boolean(policy=policy3)
    assert ab3 == expand({"CLS": ["S"], "REL": ["CAN", "GBR"]})
    b3 = reasoner.insert_keys_for_attribute_value(ab3)
    assert str(b3) == "[DEFAULT]&(KAS-CAN-1⋁KAS-GBR-1)"
    assert str(reduce(b3)) == "(KAS-CAN-1⋁KAS-GBR-1)"

    policy4 = [
        unshorten(x)
        for x in [
            "CLS:S",
            "REL:USA",
            "REL:GBR",
            "N2K:SI",
            "N2K:HCS",
        ]
    ]
    ab4 = reasoner.construct_attribute_boolean(policy=policy4)
    assert ab4 == expand({"CLS": ["S"], "REL": ["USA", "GBR"], "N2K": ["SI", "HCS"]})
    b4 = reasoner.insert_keys_for_attribute_value(ab4)
    assert str(b4) == "[DEFAULT]&(KAS-USA-1⋁KAS-GBR-1)&(KAS-USA-1⋀KAS-USA-1)"
    assert str(reduce(b4)) == "(KAS-GBR-1⋁KAS-USA-1)&(KAS-USA-1)"


def test_reduce():
    def e(sexpr: list[list[str]]):
        return BooleanKeyExpression(
            values=[
                KeyClause(
                    operator=Rule.allOf if ruley == "&" else Rule.anyOf,
                    values=[PublicKeyInfo(kas=k) for k in rest],
                )
                for [ruley, *rest] in sexpr
            ]
        )

    assert str(e([["&", "A"]])) == "(A)"
    assert str(reduce(e([["&", "A"]]))) == "(A)"

    assert str(e([["|", "A"]])) == "(A)"
    assert str(reduce(e([["|", "A"]]))) == "(A)"

    assert str(e([["&", "A", "A"]])) == "(A⋀A)"
    assert str(reduce(e([["&", "A", "A"]]))) == "(A)"

    assert str(e([["|", "A", "A"]])) == "(A⋁A)"
    assert str(reduce(e([["|", "A", "A"]]))) == "(A)"

    assert str(e([["|", "DEFAULT"]])) == "[DEFAULT]"
    assert reduce(e([["|", "DEFAULT"]])) == None

    assert str(e([["&", "A", "A"]])) == "(A⋀A)"
    assert str(reduce(e([["&", "A", "A"]]))) == "(A)"

    assert str(e([["&", "A"], ["&", "DEFAULT"]])) == "(A)&[DEFAULT]"
    assert str(reduce(e([["&", "A"], ["&", "DEFAULT"]]))) == "(A)"

    assert str(e([["&", "A", "DEFAULT"]])) == "(A⋀DEFAULT)"
    assert str(reduce(e([["&", "A", "DEFAULT"]]))) == "(A)"

    assert str(e([["|", "A", "DEFAULT"]])) == "(A⋁DEFAULT)"
    assert str(reduce(e([["|", "A", "DEFAULT"]]))) == "(A)"

    assert str(e([["&", "DEFAULT", "A", "DEFAULT"]])) == "(DEFAULT⋀A⋀DEFAULT)"
    assert str(reduce(e([["&", "DEFAULT", "A", "DEFAULT"]]))) == "(A)"


def test_split_eyes():
    cfg_svc_split = ConfigurationService()
    for country_code in ["AUS", "CAN", "GBR", "NZL", "USA"]:
        cfg_svc_split.put_mapping(
            EncryptionMapping(
                kas=f"KAS-{country_code}-1",
                grants=[
                    KeyAccessGrant(
                        attr="https://virtru.com/attr/Releasable+To",
                        values=["FVEY"],
                    ),
                ],
            )
        )
    reasoner = Reasoner(attr_svc, cfg_svc_split)
    policy1 = [
        unshorten(x)
        for x in [
            "CLS:S",
            "REL:FVEY",
        ]
    ]
    ab = reasoner.construct_attribute_boolean(policy=policy1)
    assert ab == expand({"CLS": ["S"], "REL": ["FVEY"]})

    b = reasoner.insert_keys_for_attribute_value(ab)
    assert str(b) == "[DEFAULT]&(KAS-AUS-1⋁KAS-CAN-1⋁KAS-GBR-1⋁KAS-NZL-1⋁KAS-USA-1)"
    assert str(reduce(b)) == "(KAS-AUS-1⋁KAS-CAN-1⋁KAS-GBR-1⋁KAS-NZL-1⋁KAS-USA-1)"
