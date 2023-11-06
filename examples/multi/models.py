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


class WebError(BaseModel):
    status: int
    message: str


class Rule(str, Enum):
    hierarchy = "hierarchy"
    anyOf = "anyOf"
    allOf = "allOf"


class AttributeDefinition(BaseModel):
    authority: AnyUrl
    name: str
    order: list[str]
    rule: Rule

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

    # @app.put("/attribute/{attribute_name}", response_model=AttributeDefinition)
    def put_attribute(self, attribute: AttributeDefinition):
        self.dict[attribute.prefix()] = attribute
        return attribute

    def get_attribute(self, prefix: str):
        return self.dict.get(prefix) or WebError(
            status=404,
            message=f"Unknown attribute type: [{prefix}], not in [{list(self.dict.keys())}]",
        )


class ConfigurationService:
    def __init__(self) -> None:
        self.by_kas: dict[str, EncryptionMapping] = {}
        self.by_prefix: dict[str, list[EncryptionMapping]] = {}

    def put_mapping(self, em: EncryptionMapping):
        if em.kas in self.by_kas:
            for grant in self.by_kas[em.kas].grants:
                self.by_prefix[grant.attr] -= [em]

        for grant in em.grants:
            if grant.attr in self.by_prefix:
                self.by_prefix[grant.attr] += [em]
            else:
                self.by_prefix[grant.attr] = [em]
        self.by_kas[em.kas] = em

    def get_mappings(self, prefix: str):
        return self.by_prefix.get(prefix) or WebError(
            status=404, message=f"Unknown attribute type: [{prefix}]"
        )


class SingleAttributeClause(BaseModel):
    definition: AttributeDefinition
    values: list[AttributeInstance]


class AttributeBooleanExpression(BaseModel):
    must: list[SingleAttributeClause]


class Reasoner:
    def __init__(
        self, attribute_svc: AttributeService, config_svc: ConfigurationService
    ) -> None:
        self.attrs = attribute_svc
        self.cfg = config_svc

    def construct_attribute_boolean(
        self, policy: list[AttributeInstance]
    ) -> AttributeBooleanExpression:
        prefixes: dict[str, AttributeInstance] = {}
        for a in policy:
            p = a.prefix()
            if p not in prefixes:
                d = self.attrs.get_attribute(p)
                if isinstance(d, WebError):
                    raise ValueError(f"Unrecognized {p}: [{d}]")
                prefixes[p] = SingleAttributeClause(definition=d, values=[a])
            else:
                prefixes[p].values += [a]
        return AttributeBooleanExpression(must=list(prefixes.values()))
