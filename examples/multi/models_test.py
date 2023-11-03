from .models import AttributeDefinition, AttributeInstance, AttributeService, Rule

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
    ],
    rule=Rule.allOf,
)


def test_definition_sample():
    assert classDef.prefix() == "https://virtru.com/name/Classification"
    assert needToKnowDef.prefix() == "https://virtru.co.us/name/Need+to+Know"
    assert relToDef.prefix() == "https://virtru.com/name/Releasable+To"


def test_definition_pathfix():
    for authority, prefix in [
        ("http://e", "http://e/name/n"),
        ("https://e", "https://e/name/n"),
        ("http://e/", "http://e/name/n"),
        ("http://e/hello", "http://e/hello/name/n"),
        ("http://e/hello/", "http://e/hello/name/n"),
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
        ("http://e", "a", "1", "http://e/name/a/value/1"),
        ("https://e/", "a", "1", "https://e/name/a/value/1"),
        ("http://e", "name", "value", "http://e/name/name/value/value"),
        ("http://e", "value", "name", "http://e/name/value/value/name"),
    ]:
        assert str(AttributeInstance(authority=a, name=n, value=v)) == s


def test_instance_from_url():
    for u in ["http://e/name/a/value/1"]:
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
    assert s.get_attribute("undefined").status == 404
