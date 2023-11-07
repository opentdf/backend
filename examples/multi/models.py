import re
import urllib

from enum import Enum
from pydantic import AnyUrl, BaseModel, field_validator


class PublicKeyAlgorithm(str, Enum):
    rsa_2048 = "rsa:2048"
    ec_secp256r1 = "ec_secp256r1"


class PublicKeyAlgorithm(str, Enum):
    rsa_2048 = "rsa:2048"
    ec_secp256r1 = "ec_secp256r1"


class PublicKeyResponse(BaseModel):
    kid: str
    publicKey: str


class WebError(BaseException):
    pass


class Rule(str, Enum):
    hierarchy = "hierarchy"
    anyOf = "anyOf"
    allOf = "allOf"


class AttributeDefinition(BaseModel):
    authority: AnyUrl
    name: str
    order: list[str]
    rule: Rule
    # TODO - Replace EncryptionMapping with this or something like it:
    # access_controller: dict[str, AnyUrl] | None = None

    @field_validator("authority")
    @classmethod
    def authority_mut_not_end_with_slash(cls, v):
        if not v.path.endswith("/"):
            v2 = AnyUrl.build(
                scheme=v.scheme,
                host=v.host,
                port=v.port,
                fragment=v.fragment,
                path=v.path[1:] + "/",
                query=v.query,
            )
            return v2
        return v

    def prefix(self) -> str:
        return f"{self.authority}attr/{urllib.parse.quote_plus(self.name)}"


class KeyAccessGrant(BaseModel):
    attr: str
    values: list[str]


class EncryptionMapping(BaseModel):
    kas: str
    grants: list[KeyAccessGrant]


class AttributeInstance(BaseModel):
    authority: AnyUrl
    name: str
    value: str

    @field_validator("authority")
    @classmethod
    def authority_mut_not_end_with_slash(cls, v):
        if not v.path.endswith("/"):
            v2 = AnyUrl.build(
                scheme=v.scheme,
                host=v.host,
                port=v.port,
                fragment=v.fragment,
                path=v.path[1:] + "/",
                query=v.query,
            )
            return v2
        return v

    @classmethod
    def from_url(cls, url: str) -> "AttributeInstance":
        m = re.fullmatch(
            r"(?P<authority>https?://[\w./]+)/attr/(?P<name>\S*)/value/(?P<value>\S*)",
            url,
        )
        if not m:
            raise ValueError(url)
        return AttributeInstance(
            authority=m.group("authority"),
            name=urllib.parse.unquote_plus(m.group("name")),
            value=urllib.parse.unquote_plus(m.group("value")),
        )

    def prefix(self) -> str:
        return f"{self.authority}attr/{urllib.parse.quote_plus(self.name)}"

    def __str__(self) -> str:
        return f"{self.authority}attr/{urllib.parse.quote_plus(self.name)}/value/{urllib.parse.quote_plus(self.value)}"


class AttributeService:
    def __init__(self) -> None:
        self.dict: dict[str, AttributeDefinition] = {}
        self.names: dict[str, AttributeDefinition] = {}

    # @app.put("/attribute/{attribute_name}", response_model=AttributeDefinition)
    def put_attribute(self, attribute: AttributeDefinition):
        self.dict[attribute.prefix()] = attribute
        self.names[attribute.name] = attribute
        return attribute

    def get_attribute(self, prefix: str) -> AttributeDefinition | WebError:
        if prefix not in self.dict:
            raise WebError(
                f"[404] Unknown attribute type: [{prefix}], not in [{list(self.dict.keys())}]"
            )
        return self.dict[prefix]


class ConfigurationService:
    def __init__(self) -> None:
        self.by_kas: dict[str, EncryptionMapping] = {}
        self.by_attr: dict[str, list[str]] = {}
        self.by_prefix: dict[str, list[EncryptionMapping]] = {}

    def put_mapping(self, em: EncryptionMapping):
        for grant in em.grants:
            for v in grant.values:
                a = f"{grant.attr}/value/{urllib.parse.quote_plus(v)}"
                if a in self.by_attr:
                    self.by_attr[a] += [em.kas]
                else:
                    self.by_attr[a] = [em.kas]
            if grant.attr in self.by_prefix:
                self.by_prefix[grant.attr] += [em]
            else:
                self.by_prefix[grant.attr] = [em]
        self.by_kas[em.kas] = em

    def get_mappings(self, prefix: str):
        if prefix not in self.by_prefix:
            raise WebError(f"[404] Unknown attribute type: [{prefix}]")
        return self.by_prefix[prefix]

    def get_mapping(self, attr: str):
        if attr not in self.by_attr:
            raise WebError(f"[404] Unknown attribute mapping: [{attr}]")
        return self.by_attr[attr]


class SingleAttributeClause(BaseModel):
    definition: AttributeDefinition
    values: list[AttributeInstance]


class AttributeBooleanExpression(BaseModel):
    must: list[SingleAttributeClause]


class PublicKeyInfo(BaseModel):
    kas: str
    # TODO kid: str


class KeyClause(BaseModel):
    operator: Rule
    values: list[PublicKeyInfo]

    def __str__(self):
        if len(self.values) == 1 and self.values[0].kas == "DEFAULT":
            return "[DEFAULT]"
        op = "⋁" if self.operator == Rule.anyOf else "⋀"
        return f"({op.join(x.kas for x in self.values)})"


class BooleanKeyExpression(BaseModel):
    values: list[KeyClause]

    def __str__(self):
        return "&".join(str(x) for x in self.values)


def reduce(e: BooleanKeyExpression) -> BooleanKeyExpression:
    print(f"reduce({e})")
    conjunction: list[list[str]] = []
    for v in e.values:
        print(f"v={v}")
        if v.operator == Rule.anyOf:
            kas = sorted(set([k.kas for k in v.values if k.kas != "DEFAULT"]))
            if kas and kas not in conjunction:
                print(f"{conjunction} += ({[kas]})")
                conjunction += [kas]
        else:
            for k in v.values:
                if k.kas != "DEFAULT" and [k.kas] not in conjunction:
                    print(f"{conjunction} += ({[[k.kas]]})")
                    conjunction += [[k.kas]]
    print(f"conjunction = {conjunction}")
    if not conjunction:
        return None
    return BooleanKeyExpression(
        values=[
            KeyClause(
                operator=Rule.anyOf,
                values=[PublicKeyInfo(kas=kas) for kas in disjunction],
            )
            for disjunction in conjunction
        ]
    )


class Reasoner:
    def __init__(
        self, attribute_svc: AttributeService, config_svc: ConfigurationService
    ) -> None:
        self.attrs = attribute_svc
        self.cfg = config_svc

    def construct_attribute_boolean(
        self, policy: list[AttributeInstance]
    ) -> AttributeBooleanExpression:
        # FIXME reduce hierarchical groups
        prefixes: dict[str, AttributeInstance] = {}
        for a in policy:
            p = a.prefix()
            if p not in prefixes:
                try:
                    d = self.attrs.get_attribute(p)
                except:
                    raise ValueError(f"Unrecognized {p}: [{d}]")
                prefixes[p] = SingleAttributeClause(definition=d, values=[a])
            else:
                prefixes[p].values += [a]
        return AttributeBooleanExpression(must=list(prefixes.values()))

    def insert_keys_for_attribute_value(
        self, e: AttributeBooleanExpression
    ) -> BooleanKeyExpression:
        return BooleanKeyExpression(
            values=[
                KeyClause(
                    operator=clause.definition.rule,
                    values=[
                        PublicKeyInfo(kas=kas)
                        for term in clause.values
                        for kas in self.cfg.by_attr.get(str(term), ["DEFAULT"])
                    ],
                )
                for clause in e.must
            ]
        )
