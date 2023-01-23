import json
import logging
import os
import sys
import requests
from enum import Enum
from http.client import (
    NO_CONTENT,
    BAD_REQUEST,
    ACCEPTED,
    INTERNAL_SERVER_ERROR,
    NOT_FOUND,
)
from urllib.parse import urlparse
from pprint import pprint
from typing import Optional, List, Annotated
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import databases as databases
import sqlalchemy
from asyncpg import UniqueViolationError, ForeignKeyViolationError
from fastapi import (
    FastAPI,
    Body,
    Depends,
    HTTPException,
    Request,
    Query,
    Security,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2AuthorizationCodeBearer, OpenIdConnect
from keycloak import KeycloakOpenID
from pydantic import AnyUrl, BaseSettings, Field, Json, ValidationError
from pydantic.main import BaseModel
from python_base import (
    Pagination,
    get_query,
    add_filter_by_access_control,
    hook_into,
)
from sqlalchemy import and_
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from .hooks import (
    audit_hook,
    err_audit_hook,
    HttpMethod,
)

logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", "CRITICAL").upper()
)
logger = logging.getLogger(__package__)

swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": os.getenv("OIDC_CLIENT_ID"),
    "realm": os.getenv("OIDC_REALM"),
    "appName": os.getenv("SERVER_PUBLIC_NAME"),
    "scopes": [os.getenv("OIDC_SCOPES")],
    "authorizationUrl": os.getenv("OIDC_AUTHORIZATION_URL"),
}


class Settings(BaseSettings):
    openapi_url: str = os.getenv("SERVER_ROOT_PATH", "") + "/openapi.json"
    base_path: str = os.getenv("SERVER_ROOT_PATH", "")


settings = Settings()

app = FastAPI(
    debug=True,
    root_path=os.getenv("SERVER_ROOT_PATH", ""),
    servers=[{"url": settings.base_path}],
    swagger_ui_init_oauth=swagger_ui_init_oauth,
    openapi_url=settings.openapi_url,
    swagger_ui_parameters={
        "url": os.getenv("SERVER_ROOT_PATH", "") + settings.openapi_url
    },
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(os.environ.get("SERVER_CORS_ORIGINS", "").split(",")),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    # format f"{keycloak_url}realms/{realm}/protocol/openid-connect/auth"
    authorizationUrl=os.getenv("OIDC_AUTHORIZATION_URL", ""),
    # format f"{keycloak_url}realms/{realm}/protocol/openid-connect/token"
    tokenUrl=os.getenv("OIDC_TOKEN_URL", ""),
)


def get_retryable_request():
    retry_strategy = Retry(total=3, backoff_factor=1)

    adapter = HTTPAdapter(max_retries=retry_strategy)

    http = requests.Session()
    http.mount("https://", adapter)
    http.mount("http://", adapter)
    return http


# Given a realm ID, request that realm's public key from Keycloak's endpoint
#
# If anything fails, raise an exception
#
# TODO Consider replacing the endpoint here with the OIDC JWKS endpoint
# Keycloak exposes: `/auth/realms/{realm-name}/.well-known/openid-configuration`
# This is a low priority though since it doesn't save us from having to get the
# realmId first and so is a largely cosmetic difference
async def get_idp_public_key(realm_id):
    url = f"{os.getenv('OIDC_SERVER_URL').rstrip('/')}/realms/{realm_id}"

    http = get_retryable_request()

    response = http.get(
        url, headers={"Content-Type": "application/json"}, timeout=5  # seconds
    )

    if not response.ok:
        logger.warning("No public key found for Keycloak realm %s", realm_id)
        raise RuntimeError(f"Failed to download Keycloak public key: [{response.text}]")

    try:
        resp_json = response.json()
    except Exception as e:
        logger.warning(
            f"Could not parse response from Keycloak pubkey endpoint: {response}"
        )
        raise e

    keycloak_public_key = f"""-----BEGIN PUBLIC KEY-----
{resp_json['public_key']}
-----END PUBLIC KEY-----"""

    logger.debug(
        "Keycloak public key for realm %s: [%s]", realm_id, keycloak_public_key
    )
    return keycloak_public_key


# Looks as `iss` header field of token - if this is a Keycloak-issued token,
# `iss` will have a value like 'https://<KEYCLOAK_SERVER>/auth/realms/<REALMID>
# so we can parse the URL parts to obtain the realm this token was issued from.
# Once we know that, we know where to get a pubkey to validate it.
#
# `urlparse` should be safe to use as a parser, and if the result is
# an invalid realm name, no validation key will be fetched, which simply will result
# in an access denied
def try_extract_realm(unverified_jwt):
    issuer_url = unverified_jwt["iss"]
    # Split the issuer URL once, from the right, on /,
    # then get the last element of the result - this will be
    # the realm name for a keycloak-issued token.
    return urlparse(issuer_url).path.rsplit("/", 1)[-1]


def has_aud(unverified_jwt, audience):
    aud = unverified_jwt["aud"]
    if not aud:
        logger.debug("No aud found in token [%s]", unverified_jwt)
        return False
    if isinstance(aud, str):
        aud = [aud]
    if audience not in aud:
        logger.debug("Audience mismatch [%s] ⊄ %s", audience, aud)
        return False
    return True


async def get_auth(token: str = Security(oauth2_scheme)) -> Json:
    keycloak_openid = KeycloakOpenID(
        # trailing / is required
        server_url=os.getenv("OIDC_SERVER_URL"),
        client_id=os.getenv("OIDC_CLIENT_ID"),
        realm_name=os.getenv("OIDC_REALM"),
        client_secret_key=os.getenv("OIDC_CLIENT_SECRET"),
        verify=True,
    )
    logger.debug(token)
    if logger.isEnabledFor(logging.DEBUG):
        pprint(vars(keycloak_openid))
        pprint(vars(keycloak_openid.connection))
    try:
        unverified_decode = keycloak_openid.decode_token(
            token,
            key="",
            options={"verify_signature": False, "verify_aud": False, "exp": True},
        )
        if not has_aud(unverified_decode, keycloak_openid.client_id):
            raise Exception("Invalid audience")
        return keycloak_openid.decode_token(
            token,
            key=await get_idp_public_key(try_extract_realm(unverified_decode)),
            options={"verify_signature": True, "verify_aud": False, "exp": True},
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),  # "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# database
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DATABASE}"
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData(schema=POSTGRES_SCHEMA)

table_authority = sqlalchemy.Table(
    "attribute_namespace",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.VARCHAR),
)

table_attribute = sqlalchemy.Table(
    "attribute",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column(
        "namespace_id",
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey("attribute_namespace.id"),
    ),
    sqlalchemy.Column("state", sqlalchemy.VARCHAR),
    sqlalchemy.Column("rule", sqlalchemy.VARCHAR),
    sqlalchemy.Column("name", sqlalchemy.VARCHAR),
    sqlalchemy.Column("description", sqlalchemy.VARCHAR),
    sqlalchemy.Column("values_array", sqlalchemy.ARRAY(sqlalchemy.TEXT)),
    sqlalchemy.Column(
        "group_by_attr", sqlalchemy.Integer, sqlalchemy.ForeignKey("attribute.id")
    ),
    sqlalchemy.Column("group_by_attrval", sqlalchemy.TEXT),
)

engine = sqlalchemy.create_engine(DATABASE_URL, pool_pre_ping=True)
dbase_session = sessionmaker(bind=engine)


def get_db_session() -> Session:
    session = dbase_session()
    try:
        yield session
    finally:
        session.close()


class AttributeSchema(declarative_base()):
    __table__ = table_attribute


class AuthoritySchema(declarative_base()):
    __table__ = table_authority


# middleware
@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


# OpenAPI
tags_metadata = [
    {
        "name": "Attributes",
        "description": """Operations to view data attributes. TDF protocol supports ABAC (Attribute Based Access Control).
        This allows TDF protocol to implement policy driven and highly scalable access control mechanism.""",
    },
    {
        "name": "Authorities",
        "description": "Operations to view and create attribute authorities.",
    },
    {
        "name": "Attributes Definitions",
        "description": "Operations to manage the rules and metadata of attributes. ",
    },
]


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="OpenTDF",
        version="1.1.2",
        license_info={
            "name": "BSD 3-Clause Clear",
            "url": "https://github.com/opentdf/backend/blob/main/LICENSE",
        },
        routes=app.routes,
        tags=tags_metadata,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://avatars.githubusercontent.com/u/90051847?s=200&v=4"
    }
    openapi_schema["servers"] = [{"url": os.getenv("SERVER_ROOT_PATH", "")}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


class RuleEnum(str, Enum):
    hierarchy = "hierarchy"
    anyOf = "anyOf"
    allOf = "allOf"


class AuthorityUrl(AnyUrl):
    max_length = 2000


class AttributeInstance(BaseModel):
    authority: AuthorityUrl
    name: Annotated[str, Field(max_length=2000)]
    value: Annotated[str, Field(max_length=2000)]

    class Config:
        schema_extra = {
            "example": {
                "authority": "https://opentdf.io",
                "name": "IntellectualProperty",
                "value": "Proprietary",
            }
        }


class AttributeDefinition(BaseModel):
    authority: AuthorityUrl
    name: Annotated[str, Field(max_length=2000)]
    order: Annotated[
        List[str],
        Field(max_length=2000),
    ]
    rule: RuleEnum
    state: Annotated[Optional[str], Field(max_length=64)]
    group_by: Optional[AttributeInstance] = None

    class Config:
        schema_extra = {
            "example": {
                "authority": "https://opentdf.io",
                "name": "IntellectualProperty",
                "rule": "hierarchy",
                "state": "published",
                "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
                "group_by": {
                    "authority": "https://opentdf.io",
                    "name": "ClassificationUS",
                    "value": "Proprietary",
                },
            }
        }


class AuthorityDefinition(BaseModel):
    authority: AuthorityUrl


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", include_in_schema=False)
async def read_semver():
    return {"Hello": "attributes"}


class ProbeType(str, Enum):
    liveness = "liveness"
    readiness = "readiness"


@app.get("/healthz", status_code=NO_CONTENT, include_in_schema=False)
async def read_liveness(probe: ProbeType = ProbeType.liveness):
    if probe == ProbeType.readiness:
        await database.execute("SELECT 1")


oidc_scheme = OpenIdConnect(
    openIdConnectUrl=os.getenv("OIDC_CONFIGURATION_URL", ""), auto_error=False
)


#
# Attributes
#


@app.get(
    "/attributes",
    tags=["Attributes"],
    response_model=List[AnyUrl],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": [
                        "https://opentdf.io/attr/IntellectualProperty/value/TradeSecret",
                        "https://opentdf.io/attr/ClassificationUS/value/Unclassified",
                    ]
                }
            }
        }
    },
)
async def read_attributes(
    request: Request,
    authority: Optional[AuthorityUrl] = None,
    name: Optional[str] = None,
    rule: Optional[str] = None,
    order: Optional[str] = None,
    sort: Optional[str] = Query(
        "",
        regex="^(-*((state)|(rule)|(name)|(values_array)),)*-*((state)|(rule)|(name)|(values_array))$",
    ),
    session: Session = Depends(get_db_session),
    pager: Pagination = Depends(Pagination),
):
    filter_args = {}
    if authority:
        # logger.debug(authority)
        # lookup authority by value and get id (namespace_id)
        authorities = await read_authorities_crud(request, session)
        filter_args["namespace_id"] = list(authorities.keys())[
            list(authorities.values()).index(authority)
        ]
    if name:
        filter_args["name"] = name
    if rule:
        filter_args["rule"] = rule
    if order:
        filter_args["values_array"] = order

    sort_args = sort.split(",") if sort else []
    results = await read_attributes_crud(request, session, filter_args, sort_args)

    return pager.paginate(results)


async def read_attributes_crud(request, session, filter_args, sort_args):
    table_to_query = metadata.tables["tdf_attribute.attribute"]
    org_name = add_filter_by_access_control(request)
    table_ns = metadata.tables["tdf_attribute.attribute_namespace"]
    query = session.query(table_ns).filter(table_ns.c.name == org_name).all()
    if org_name is not None:
        for row in query:
            filter_args["namespace_id"] = row.id
    filters, sorters = get_query(table_to_query, filter_args, sort_args)
    results = session.query(table_to_query).filter(*filters).order_by(*sorters)
    error = None
    authorities = await read_authorities_crud(request, session)
    attributes: List[AnyUrl] = []

    try:
        for row in results:
            for value in row.values_array:
                attributes.append(
                    AnyUrl(
                        scheme=f"{authorities[row.namespace_id]}",
                        host=f"{authorities[row.namespace_id]}",
                        url=f"{authorities[row.namespace_id]}/attr/{row.name}/value/{value}",
                    )
                )
    except ValidationError as e:
        logger.error(e)
        error = e

    if error and not attributes:
        raise HTTPException(
            status_code=422, detail=f"attribute error: {str(error)}"
        ) from error
    return attributes


#
# Attributes Definitions
#


@app.get(
    "/definitions/attributes",
    tags=["Attributes Definitions"],
    response_model=List[AttributeDefinition],
    dependencies=[Depends(get_auth)],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": [
                        {
                            "authority": "https://opentdf.io",
                            "name": "IntellectualProperty",
                            "rule": "hierarchy",
                            "state": "published",
                            "order": [
                                "TradeSecret",
                                "Proprietary",
                                "BusinessSensitive",
                                "Open",
                            ],
                            "group_by": {
                                "authority": "https://opentdf.io",
                                "name": "ClassificationUS",
                                "value": "Proprietary",
                            },
                        }
                    ]
                }
            }
        }
    },
)
# This is an alias endpoint for the same handler, as used by KAS
# This is because KAS needs something that does *exactly* the same thing as `GET /definitions/attributes`,
# just without JWT auth or pagination.
#
# JWT auth can be disabled for the aliased route and pagination can be selectively employed, so do that to
# avoid functionally-identical-yet-parallel handlers and object models.
#
# When JWT auth is removed from service code and implemented at the Ingress level on specific routes,
# where it belongs, and KAS's attribute authority client code is made to grok pagination,
# then we won't need this endpoint alias anymore and can drop it
# (since KAS<->attribute service is east-west traffic)
# For now, let's at least just alias the deprecated endpoint to the same implementation to avoid confusing people.
@app.get(
    "/v1/attrName", response_model=List[AttributeDefinition], include_in_schema=False
)
async def read_attributes_definitions(
    request: Request,
    authority: Optional[AuthorityUrl] = None,
    name: Optional[str] = None,
    rule: Optional[str] = None,
    order: Optional[str] = None,
    sort: Optional[str] = Query(
        "",
        regex="^(-*((id)|(state)|(rule)|(name)|(values_array)),)*-*((id)|(state)|(rule)|(name)|(values_array))$",
    ),
    session: Session = Depends(get_db_session),
    pager: Pagination = Depends(Pagination),
):
    logger.debug("read_attributes_definitions %s", request.url)
    filter_args = {}
    if authority:
        # lookup authority by value and get id (namespace_id)
        authorities = await read_authorities_crud(request, session)
        try:
            filter_args["namespace_id"] = list(authorities.keys())[
                list(authorities.values()).index(authority)
            ]
        except ValueError:
            raise HTTPException(
                status_code=NOT_FOUND, detail=f"Authority {authority} does not exist"
            )
    if name:
        filter_args["name"] = name
    if order:
        filter_args["values_array"] = order
    if rule:
        filter_args["rule"] = rule

    sort_args = sort.split(",") if sort else []
    table_to_query = metadata.tables["tdf_attribute.attribute"]
    org_name = add_filter_by_access_control(request)
    table_ns = metadata.tables["tdf_attribute.attribute_namespace"]
    query = session.query(table_ns).filter(table_ns.c.name == org_name).all()
    if org_name is not None:
        for row in query:
            filter_args["namespace_id"] = row.id
    filters, sorters = get_query(table_to_query, filter_args, sort_args)
    results = session.query(table_to_query).filter(*filters).order_by(*sorters)

    authorities = await read_authorities_crud(request, session)
    attributes: List[AttributeDefinition] = []
    for row in results:
        try:
            attr_def = AttributeDefinition(
                authority=authorities[row.namespace_id],
                name=row.name,
                order=row.values_array,
                rule=row.rule,
                state=row.state,
            )
            # If this attribute definition has a "groupby AttributeInstance"
            # that is, it has a non-null reference to another attribute definition
            # and a specific grouping value, then look for and return that
            if row.group_by_attr:
                groupby_attr_q = table_attribute.select().where(
                    table_attribute.c.id == row.group_by_attr
                )

                groupby_attr = await database.fetch_one(groupby_attr_q)

                # If this happens, we have not been properly maintaining the integrity of the
                # attribute store - we're referencing an attr ID that no longer exists in this table.
                if not groupby_attr:
                    raise HTTPException(
                        status_code=INTERNAL_SERVER_ERROR,
                        detail=f"Groupby attribute {groupby_attr} not found",
                    )
                # If this attr has a group_by, get the name of the authority
                # TODO there is probably a nicer SQL query that does all this in one go.
                # For the sake of clarity, doing it individually.
                groupby_authority_q = table_authority.select().where(
                    table_authority.c.id == groupby_attr.namespace_id
                )
                groupby_authority = await database.fetch_one(groupby_authority_q)
                if not groupby_authority:
                    raise HTTPException(
                        status_code=INTERNAL_SERVER_ERROR,
                        detail=f"Group-by attribute authority {groupby_attr.namespace_id} does not exist",
                    )

                attr_def.group_by = AttributeInstance(
                    authority=groupby_authority.name,
                    name=groupby_attr.name,
                    value=row.group_by_attrval,
                )

            attributes.append(attr_def)
        except ValidationError as e:
            logger.error(e)
    logger.debug("attribute definitions %s", attributes)
    # As mentioned, `v1/attrName` and `/definitions/attributes` are the same, just
    # the latter has pagination and JWT auth, and the former does not.
    # JWT auth is something that can be included or excluded in the route decorator,
    # but our DIY pager cannot be handled at the decorator level.
    # So we do this - this conditional can be removed when we
    # stop doing JWT auth at the service level and add pagination in KAS's client code
    # and drop this alias.
    if "v1/attrName" in request.url.path:
        return attributes
    else:
        return pager.paginate(attributes)


@app.post(
    "/definitions/attributes",
    tags=["Attributes Definitions"],
    response_model=AttributeDefinition,
    dependencies=[Depends(get_auth)],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "authority": "https://opentdf.io",
                        "name": "IntellectualProperty",
                        "rule": "hierarchy",
                        "state": "published",
                        "order": [
                            "TradeSecret",
                            "Proprietary",
                            "BusinessSensitive",
                            "Open",
                        ],
                        "group_by": {
                            "authority": "https://opentdf.io",
                            "name": "ClassificationUS",
                            "value": "Proprietary",
                        },
                    }
                }
            }
        }
    },
)
@hook_into(HttpMethod.POST, post=audit_hook, err=err_audit_hook)
async def create_attributes_definitions(
    request: AttributeDefinition = Body(
        ...,
        example={
            "authority": "https://opentdf.io",
            "name": "IntellectualProperty",
            "rule": "hierarchy",
            "state": "published",
            "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
            "group_by": {
                "authority": "https://opentdf.io",
                "name": "ClassificationUS",
                "value": "Proprietary",
            },
        },
    ),
    decoded_token=Depends(get_auth),
):
    return await create_attributes_definitions_crud(request, decoded_token)


async def create_attributes_definitions_crud(request, decoded_token=None):
    # lookup
    query = table_authority.select().where(table_authority.c.name == request.authority)
    ns_result = await database.fetch_one(query)
    if not ns_result:
        raise HTTPException(status_code=BAD_REQUEST, detail=f"namespace not found")
    namespace_id = ns_result.get(table_authority.c.id)

    group_attr_id = None
    if request.group_by:
        # Groupby
        group_authority_query = table_authority.select().where(
            table_authority.c.name == request.group_by.authority
        )
        group_authority = await database.fetch_one(group_authority_query)
        if not group_authority:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Group-by attribute authority does not exist",
            )

        attr_def_q = table_attribute.select().where(
            and_(
                table_attribute.c.namespace_id == group_authority.id,
                table_attribute.c.name == request.group_by.name,
            )
        )

        group_attr = await database.fetch_one(attr_def_q)

        if request.group_by.value not in group_attr.values_array:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Specified an invalid value for group-by attribute",
            )

        group_attr_id = group_attr.id

    if request.rule == RuleEnum.hierarchy:
        is_duplicated = check_duplicates(request.order)
        if is_duplicated:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Duplicated items when Rule is Hierarchy",
            )

    # insert
    query = table_attribute.insert().values(
        name=request.name,
        namespace_id=namespace_id,
        values_array=request.order,
        state=request.state,
        rule=request.rule,
        group_by_attr=group_attr_id,
        group_by_attrval=(request.group_by.value if group_attr_id else None),
    )
    try:
        await database.execute(query)
    except UniqueViolationError as e:
        raise HTTPException(
            status_code=BAD_REQUEST, detail=f"duplicate: {str(e)}"
        ) from e
    return request


@app.put(
    "/definitions/attributes",
    tags=["Attributes Definitions"],
    response_model=AttributeDefinition,
    dependencies=[Depends(get_auth)],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "authority": "https://opentdf.io",
                        "name": "IntellectualProperty",
                        "rule": "hierarchy",
                        "state": "published",
                        "order": [
                            "TradeSecret",
                            "Proprietary",
                            "BusinessSensitive",
                            "Open",
                        ],
                    }
                }
            }
        }
    },
)
@hook_into(HttpMethod.PUT, post=audit_hook, err=err_audit_hook)
async def update_attribute_definition(
    request: AttributeDefinition = Body(
        ...,
        example={
            "authority": "https://opentdf.io",
            "name": "IntellectualProperty",
            "rule": "hierarchy",
            "state": "published",
            "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
            "group_by": {
                "authority": "https://opentdf.io",
                "name": "ClassificationUS",
                "value": "Proprietary",
            },
        },
    ),
    decoded_token=Depends(get_auth),
):
    return await update_attribute_definition_crud(request, decoded_token)


async def update_attribute_definition_crud(request, decoded_token=None):
    # update
    query = table_authority.select().where(table_authority.c.name == request.authority)
    result = await database.fetch_one(query)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        )

    if request.rule == RuleEnum.hierarchy:
        is_duplicated = check_duplicates(request.order)
        if is_duplicated:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Duplicated items when Rule is Hierarchy",
            )

    group_attr_id = None
    if request.group_by:
        # Groupby
        group_authority_query = table_authority.select().where(
            table_authority.c.name == request.group_by.authority
        )
        group_authority = await database.fetch_one(group_authority_query)
        if not group_authority:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Group-by attribute authority does not exist",
            )

        attr_def_q = table_attribute.select().where(
            and_(
                table_attribute.c.namespace_id == group_authority.id,
                table_attribute.c.name == request.group_by.name,
            )
        )

        group_attr = await database.fetch_one(attr_def_q)

        if request.group_by.value not in group_attr.values_array:
            raise HTTPException(
                status_code=BAD_REQUEST,
                detail="Specified an invalid value for group-by attribute",
            )

        group_attr_id = group_attr.id

    query = (
        table_attribute.update()
        .where(
            and_(
                table_authority.c.name == request.authority,
                table_attribute.c.name == request.name,
            )
        )
        .values(
            values_array=request.order,
            rule=request.rule,
            group_by_attr=group_attr_id,
            group_by_attrval=(request.group_by.value if group_attr_id else None),
        )
    )

    await database.execute(query)

    return request


@app.delete(
    "/definitions/attributes",
    tags=["Attributes Definitions"],
    status_code=ACCEPTED,
    dependencies=[Depends(get_auth)],
    responses={
        202: {
            "description": "No Content",
            "content": {"application/json": {"example": {"detail": "Item deleted"}}},
        }
    },
)
@hook_into(HttpMethod.DELETE, post=audit_hook, err=err_audit_hook)
async def delete_attributes_definitions(
    request: AttributeDefinition = Body(
        ...,
        example={
            "authority": "https://opentdf.io",
            "name": "IntellectualProperty",
            "rule": "hierarchy",
            "state": "published",
            "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
        },
    ),
    decoded_token=Depends(get_auth),
):
    return await delete_attributes_definitions_crud(request, decoded_token)


async def delete_attributes_definitions_crud(request, decoded_token=None):
    statement = table_attribute.delete().where(
        and_(
            table_authority.c.name == request.authority,
            table_attribute.c.name == request.name,
            table_attribute.c.rule == str(request.rule.value),
            table_attribute.c.values_array == request.order,
        )
    )
    await database.execute(statement)
    return {}


#
# Authorities
#


@app.get(
    "/authorities",
    tags=["Authorities"],
    dependencies=[Depends(get_auth)],
    responses={
        200: {"content": {"application/json": {"example": ["https://opentdf.io"]}}}
    },
)
async def read_authorities(
    request: Request,
    session: Session = Depends(get_db_session),
):
    authorities = await read_authorities_crud(request, session)
    return list(authorities.values())


async def read_authorities_crud(request, session):
    org_name = add_filter_by_access_control(request)
    table_ns = metadata.tables["tdf_attribute.attribute_namespace"]
    if org_name is not None:
        query = session.query(table_ns).filter(table_ns.c.name == org_name).all()
    else:
        query = session.query(table_ns).all()
    authorities = {}
    for row in query:
        authorities[row.id] = row.name
    return authorities


@app.post(
    "/authorities",
    tags=["Authorities"],
    dependencies=[Depends(get_auth)],
    responses={
        200: {"content": {"application/json": {"example": ["https://opentdf.io"]}}}
    },
)
@hook_into(HttpMethod.POST, post=audit_hook, err=err_audit_hook)
async def create_authorities(
    request: AuthorityDefinition = Body(
        ..., example={"authority": "https://opentdf.io"}
    ),
    decoded_token=Depends(get_auth),
):
    return await create_authorities_crud(request, decoded_token)


async def create_authorities_crud(request, decoded_token=None):
    # insert
    query = table_authority.insert().values(name=request.authority)
    try:
        await database.execute(query)
    except UniqueViolationError as e:
        raise HTTPException(
            status_code=BAD_REQUEST, detail=f"duplicate: {str(e)}"
        ) from e
    # select all
    query = table_authority.select()
    result = await database.fetch_all(query)
    namespaces = []
    for row in result:
        namespaces.append(f"{row.get(table_authority.c.name)}")
    return namespaces


@app.delete(
    "/authorities",
    tags=["Authorities"],
    dependencies=[Depends(get_auth)],
    status_code=ACCEPTED,
    responses={
        202: {
            "description": "No Content",
            "content": {"application/json": {"example": {"detail": "Item deleted"}}},
        }
    },
)
@hook_into(HttpMethod.DELETE, post=audit_hook, err=err_audit_hook)
async def delete_authorities(
    request: AuthorityDefinition = Body(
        ..., example={"authority": "https://opentdf.io"}
    ),
    decoded_token=Depends(get_auth),
):
    return await delete_authorities_crud(request, decoded_token)


async def delete_authorities_crud(request, decoded_token=None):
    query = table_authority.select().where(table_authority.c.name == request.authority)
    result = await database.fetch_one(query)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        )

    statement = table_authority.delete().where(
        and_(table_authority.c.name == request.authority)
    )
    try:
        await database.execute(statement)
    except ForeignKeyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            detail=f"Unable to delete non-empty authority",
        ) from e
    return {}


# Check for duplicated items when rule is Hierarchy
def check_duplicates(hierarchy_list):
    if len(hierarchy_list) == len(set(hierarchy_list)):
        return False
    else:
        return True


if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
