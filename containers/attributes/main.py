import json
import logging
import os
import sys
import requests
from enum import Enum
from http.client import NO_CONTENT
from urllib.parse import urlparse
from pprint import pprint
from typing import Optional, List
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import databases as databases
import sqlalchemy
from asyncpg import UniqueViolationError
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi import Security, status
from fastapi.security import OAuth2AuthorizationCodeBearer
from fastapi.security import OpenIdConnect
from keycloak import KeycloakOpenID
from pydantic import HttpUrl, ValidationError
from pydantic import Json
from pydantic.main import BaseModel

logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", logging.CRITICAL)
)
logger = logging.getLogger(__package__)

swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": os.getenv("OIDC_CLIENT_ID"),
    "realm": os.getenv("OIDC_REALM"),
    "appName": os.getenv("SERVER_PUBLIC_NAME"),
    "scopes": ["email"],
}

app = FastAPI(debug=True, swagger_ui_init_oauth=swagger_ui_init_oauth)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    # format f"{keycloak_url}realms/{realm}/protocol/openid-connect/auth"
    authorizationUrl=os.getenv("OIDC_AUTHORIZATION_URL", ""),
    # format f"{keycloak_url}realms/{realm}/protocol/openid-connect/token"
    tokenUrl=os.getenv("OIDC_TOKEN_URL", ""),
)

keycloak_openid = KeycloakOpenID(
    # trailing / is required
    server_url=os.getenv("OIDC_SERVER_URL"),
    client_id=os.getenv("OIDC_CLIENT_ID"),
    realm_name=os.getenv("OIDC_REALM"),
    client_secret_key=os.getenv("OIDC_CLIENT_SECRET"),
    verify=True,
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
async def get_idp_public_key(realmId):
    url = f"{os.getenv('OIDC_SERVER_URL')}realms/{realmId}"

    http = get_retryable_request()

    response = http.get(
        url, headers={"Content-Type": "application/json"}, timeout=5  # seconds
    )

    if not response.ok:
        logger.warning("No public key found for Keycloak realm %s", realmId)
        raise KeyNotFoundError(
            f"Failed to download Keycloak public key: [{response.text}]"
        )

    try:
        resp_json = response.json()
    except:
        logger.warning(
            f"Could not parse response from Keycloak pubkey endpoint: {response}"
        )
        raise

    keycloak_public_key = f"""-----BEGIN PUBLIC KEY-----
{resp_json['public_key']}
-----END PUBLIC KEY-----"""

    logger.debug("Keycloak public key for realm %s: [%s]", realmId, keycloak_public_key)
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

async def get_auth(token: str = Security(oauth2_scheme)) -> Json:
    logger.debug(token)
    if logger.isEnabledFor(logging.DEBUG):
        pprint(vars(keycloak_openid))
        pprint(vars(keycloak_openid.connection))
    try:
        unverified_decode = keycloak_openid.decode_token(
            token,
            key='',
            options={"verify_signature": False, "verify_aud": True, "exp": True},
        )

        return keycloak_openid.decode_token(
            token,
            key=await get_idp_public_key(try_extract_realm(unverified_decode)),
            options={"verify_signature": True, "verify_aud": True, "exp": True},
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
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DATABASE = os.getenv("POSTGRES_DATABASE")
POSTGRES_SCHEMA = os.getenv("POSTGRES_SCHEMA")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DATABASE}"
database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData(schema=POSTGRES_SCHEMA)

table_authority_namespace = sqlalchemy.Table(
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
    sqlalchemy.Column("values", sqlalchemy.ARRAY(sqlalchemy.TEXT)),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)


@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


class AttributeRuleType(str, Enum):
    hierarchy = "hierarchy"
    anyOf = "anyOf"
    allOf = "allOf"


class Attribute(BaseModel):
    authorityNamespace: HttpUrl
    name: str
    order: list
    rule: AttributeRuleType
    state: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "authorityNamespace": "https://eas.local",
                "name": "IntellectualProperty",
                "rule": "hierarchy",
                "state": "published",
                "order": ["TradeSecret", "Proprietary", "BusinessSensitive", "Open"],
            }
        }


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/", include_in_schema=False)
async def read_semver():
    return {"Hello": "World"}


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


@app.get("/v1/attr", response_model=List[Attribute], dependencies=[Depends(get_auth)])
@app.post(
    "/v1/attrName", response_model=List[Attribute], dependencies=[Depends(get_auth)]
)
async def read_attribute():
    error = None
    query = table_attribute.select()
    result = await database.fetch_all(query)
    attributes: List[Attribute] = []
    for row in result:
        try:
            # lookup
            query = table_authority_namespace.select().where(
                table_authority_namespace.c.id
                == row.get(table_attribute.c.namespace_id)
            )
            result_namespace = await database.fetch_one(query)
            if result_namespace:
                namespace = result_namespace.get(table_authority_namespace.c.name)
            else:
                error = ValidationError
                break
            attributes.append(
                Attribute(
                    authorityNamespace=namespace,
                    name=row.get(table_attribute.c.name),
                    order=row.get("values"),
                    rule=row.get(table_attribute.c.rule),
                    state="published",  # row.get(table_attribute.c.state),
                )
            )
        except ValidationError as e:
            logging.error(e)
            error = e
    if error and not attributes:
        raise HTTPException(
            status_code=422, detail=f"attribute error: {str(error)}"
        ) from error
    return attributes


@app.post("/v1/attr", response_model=Attribute, dependencies=[Depends(get_auth)])
async def create_attribute(request: Attribute):
    # lookup
    query = table_authority_namespace.select().where(
        table_authority_namespace.c.name == request.authorityNamespace
    )
    result = await database.fetch_one(query)
    if result:
        if request.rule == AttributeRuleType.hierarchy:
            isDuplicated = checkDuplicates(request.order)
            if isDuplicated:
                raise HTTPException(status_code=400, detail="Duplicated items when Rule is Hierarchy")
        namespace_id = result.get(table_authority_namespace.c.id)
        # insert
        query = table_attribute.insert().values(
            name=request.name,
            namespace_id=namespace_id,
            values=request.order,
            state=request.state,
            rule=request.rule,
        )
        try:
            await database.execute(query)
        except UniqueViolationError as e:
            raise HTTPException(status_code=400, detail=f"duplicate: {str(e)}") from e
    else:
        raise HTTPException(status_code=400, detail=f"namespace not found")
    return request


@app.put("/v1/attr", response_model=Attribute, dependencies=[Depends(get_auth)])
async def update_attribute(request: Attribute):
    # update
    query = table_authority_namespace.select().where(
        table_authority_namespace.c.name == request.authorityNamespace
    )
    result = await database.fetch_one(query)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Record not found"
        )

    if request.rule == AttributeRuleType.hierarchy:
        isDuplicated = checkDuplicates(request.order)
        if isDuplicated:
            raise HTTPException(status_code=400, detail="Duplicated items when Rule is Hierarchy")

    query = table_attribute.update().values(
        values=request.order,
    )

    await database.execute(query)
    return request


@app.get("/v1/authorityNamespace", dependencies=[Depends(get_auth)])
async def read_authority_namespace():
    query = (
        table_authority_namespace.select()
    )  # .where(entity_attribute.c.userid == request.userId)
    result = await database.fetch_all(query)
    namespaces = []
    for row in result:
        namespaces.append(f"{row.get(table_authority_namespace.c.name)}")
    return namespaces


@app.post("/v1/authorityNamespace", dependencies=[Depends(get_auth)])
async def create_authority_namespace(request_authority_namespace: HttpUrl):
    # insert
    query = table_authority_namespace.insert().values(name=request_authority_namespace)
    try:
        await database.execute(query)
    except UniqueViolationError as e:
        raise HTTPException(status_code=400, detail=f"duplicate: {str(e)}") from e
    # select all
    query = (
        table_authority_namespace.select()
    )  # .where(entity_attribute.c.userid == request.userId)
    result = await database.fetch_all(query)
    namespaces = []
    for row in result:
        namespaces.append(f"{row.get(table_authority_namespace.c.name)}")
    return namespaces

#Check for duplicated items when rule is Hierarchy
def checkDuplicates(hierachyList):
    if len(hierachyList) == len(set(hierachyList)):
        return False
    else:
        return True


if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
