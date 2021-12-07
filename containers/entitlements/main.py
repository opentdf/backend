import json
import logging
import os
import re
import sys
import base64
import requests
from enum import Enum
from http.client import NO_CONTENT
from typing import List, Optional
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import databases as databases
import sqlalchemy
import uritools
from fastapi import FastAPI, Request, Depends
from fastapi import Security, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2AuthorizationCodeBearer
from keycloak import KeycloakOpenID
from pydantic import HttpUrl, validator
from pydantic import Json
from pydantic.main import BaseModel
from sqlalchemy import and_

logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", logging.INFO)
)
logger = logging.getLogger(__package__)

swagger_ui_init_oauth = {
    "usePkceWithAuthorizationCodeGrant": True,
    "clientId": os.getenv("OIDC_CLIENT_ID"),
    "realm": os.getenv("OIDC_REALM"),
    "appName": os.getenv("SERVER_PUBLIC_NAME"),
    "scopes": ["email"],
}

app = FastAPI(swagger_ui_init_oauth=swagger_ui_init_oauth, debug=True)

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),  # "Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_attributes_for_entity(entityId: str):
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == entityId
    )
    result = await database.fetch_all(query)
    attrObjects: List[AttributeObject] = []
    for row in result:
        attrObjects.append(
            AttributeObject(
                attribute=f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}",
            )
        )
    return attrObjects


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

table_entity_attribute = sqlalchemy.Table(
    "entity_attribute",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("entity_id", sqlalchemy.VARCHAR),
    sqlalchemy.Column("namespace", sqlalchemy.VARCHAR),
    sqlalchemy.Column("name", sqlalchemy.VARCHAR),
    sqlalchemy.Column("value", sqlalchemy.VARCHAR),
)

engine = sqlalchemy.create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)


@app.middleware("http")
async def add_response_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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


class EntityAttributeRelationship(BaseModel):
    attribute: HttpUrl
    entityId: str
    state: Optional[str]

    @validator("attribute")
    def name_must_contain_space(cls, v):
        if not re.search("/attr/\w+/value/\w+", v):
            raise ValueError("invalid format")
        return v

    class Config:
        schema_extra = {
            "example": {
                "attribute": "https://eas.local/attr/ClassificationUS/value/Unclassified",
                "entityId": "Charlie_1234",
                "state": "active",
            }
        }

# https://github.com/virtru/tdf-spec/blob/2198db5605ce9d5af05be0eb331cc85dfb6383df/schema/AttributeObject.md
class ClaimsRequest(BaseModel):
    primary_entity_id: str
    secondary_entity_ids: List[str]
    entity_signing_pk: str

    class Config:
        schema_extra = {
            "example": {
                "attribute": "https://eas.local/attr/ClassificationUS/value/Unclassified",
            }
        }

# https://github.com/virtru/tdf-spec/blob/2198db5605ce9d5af05be0eb331cc85dfb6383df/schema/AttributeObject.md
class AttributeObject(BaseModel):
    attribute: HttpUrl

    class Config:
        schema_extra = {
            "example": {
                "attribute": "https://eas.local/attr/ClassificationUS/value/Unclassified",
            }
        }


# https://github.com/virtru/tdf-spec/blob/2198db5605ce9d5af05be0eb331cc85dfb6383df/schema/ClaimsObject.md
class SubjectObject(BaseModel):
    subject_identifier: str
    subject_attributes: List[AttributeObject]

    class Config:
        schema_extra = {
            "example": {
                "attribute": "https://eas.local/attr/ClassificationUS/value/Unclassified",
            }
        }


# https://github.com/virtru/tdf-spec/blob/2198db5605ce9d5af05be0eb331cc85dfb6383df/schema/ClaimsObject.md
class ClaimsObject(BaseModel):
    subjects: List[SubjectObject]
    client_public_signing_key: str

    class Config:
        schema_extra = {
            "example": {
                "attribute": "https://eas.local/attr/ClassificationUS/value/Unclassified",
            }
        }

@app.get(
    "/v1/entity/attribute",
    response_model=List[EntityAttributeRelationship],
    dependencies=[Depends(get_auth)],
)
async def read_relationship():
    query = (
        table_entity_attribute.select()
    )  # .where(entity_attribute.c.userid == request.userId)
    result = await database.fetch_all(query)
    relationships: List[EntityAttributeRelationship] = []
    for row in result:
        relationships.append(
            EntityAttributeRelationship(
                attribute=f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}",
                entityId=row.get(table_entity_attribute.c.entity_id),
                state="active",
            )
        )
    return relationships


# This accepts a list of subjects and returns a valid ClaimsObject
# TODO right now Keycloak itself needs to call this during auth flows to get claims
# so it doesn't make sense to protect this fetch endpoint with JWT auth
# Revisit, and secure in some other way (mTLS)
@app.post(
    "/v1/entity/claimsobject",
    response_model=ClaimsObject
)
async def read_relationship(req: ClaimsRequest):
    logger.debug("UNPARSED KEY: %s", req.entity_signing_pk)
    parsed_pk = parse_pk(req.entity_signing_pk)
    logger.debug("PARSED KEY: %s", parsed_pk)
    claimsObj = ClaimsObject(subjects=[], client_public_signing_key=parsed_pk)
    # Get attributes for primary entity
    primary_attrs = await get_attributes_for_entity(req.primary_entity_id)
    logger.debug(f"Fetched attrs {primary_attrs} for primary entity {req.primary_entity_id}")
    primary = SubjectObject(subject_identifier=req.primary_entity_id, subject_attributes=primary_attrs)
    claimsObj.subjects.append(primary)

    # Get attributes for any secondary entities
    for secondarySubID in req.secondary_entity_ids:
        secondary_attrs = await get_attributes_for_entity(secondarySubID)
        logger.debug(f"Fetched attrs {secondary_attrs} for primary entity {secondarySubID}")
        subObj = SubjectObject(subject_identifier=secondarySubID, subject_attributes=secondary_attrs)
        claimsObj.subjects.append(subObj)

    return claimsObj

def parse_pk(raw_pk):
    # Unfortunately, not all base64 implementations pad base64
    # strings in the way that Python expects (dependent on the length)
    # - fortunately, we can easily add the padding ourselves here if
    # it's needed.
    # See: https://gist.github.com/perrygeo/ee7c65bb1541ff6ac770
    clientKey = f"{raw_pk}{'=' * ((4 - len(raw_pk) % 4) % 4)}"
    return base64.b64decode(clientKey).decode("ascii")

def parse_attribute_uri(attribute_uri):
    # FIXME harden, unit test
    logger.debug(attribute_uri)
    uri = uritools.urisplit(attribute_uri)
    logger.debug(uri)
    logger.debug(uri.authority)
    # workaround for dropping ://
    if not uri.authority:
        uri = uritools.urisplit(attribute_uri.replace(":/", "://"))
        logger.debug(uri)
    path_split_value = uri.path.split("/value/")
    path_split_name = path_split_value[0].split("/attr/")

    return {
        "namespace": f"{uri.scheme}://{uri.authority}",
        "name": path_split_name[1],
        "value": path_split_value[1],
    }


@app.get("/v1/entity/{entityId}/attribute", dependencies=[Depends(get_auth)])
async def read_entity_attribute_relationship(entityId: str):
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == entityId
    )
    result = await database.fetch_all(query)
    relationships: List[EntityAttributeRelationship] = []
    for row in result:
        relationships.append(
            EntityAttributeRelationship(
                attribute=f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}",
                entityId=row.get(table_entity_attribute.c.entity_id),
                state="active",
            )
        )
    return relationships


@app.get("/v1/entity/{entityId}/claimsobject", dependencies=[Depends(get_auth)])
async def read_entity_attribute_relationship(entityId: str):
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == entityId
    )
    result = await database.fetch_all(query)
    claimsobject: List[ClaimsObject] = []
    for row in result:
        claimsobject.append(
            ClaimsObject(
                attribute=f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}",
            )
        )
    return claimsobject


@app.put("/v1/entity/{entityId}/attribute", dependencies=[Depends(get_auth)])
async def create_entity_attribute_relationship(entityId: str, request: List[HttpUrl]):
    rows = []
    for attribute_uri in request:
        attribute = parse_attribute_uri(attribute_uri)
        rows.append(
            {
                "entity_id": entityId,
                "namespace": attribute["namespace"],
                "name": attribute["name"],
                "value": attribute["value"],
            }
        )
    query = table_entity_attribute.insert(rows)
    await database.execute(query)
    return request


@app.get("/v1/attribute/{attributeURI:path}/entity/", dependencies=[Depends(get_auth)])
async def get_attribute_entity_relationship(attributeURI: str):
    logger.debug(attributeURI)
    attribute = parse_attribute_uri(attributeURI)
    query = table_entity_attribute.select().where(
        and_(
            table_entity_attribute.c.namespace == attribute["namespace"],
            table_entity_attribute.c.name == attribute["name"],
            table_entity_attribute.c.value == attribute["value"],
        )
    )
    result = await database.fetch_all(query)
    relationships: List[EntityAttributeRelationship] = []
    for row in result:
        relationships.append(
            EntityAttributeRelationship(
                attribute=f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}",
                entityId=row.get(table_entity_attribute.c.entity_id),
                state="active",
            )
        )
    return relationships


@app.put("/v1/attribute/{attributeURI:path}/entity/", dependencies=[Depends(get_auth)])
async def create_attribute_entity_relationship(
    attributeURI: HttpUrl, request: List[str]
):
    attribute = parse_attribute_uri(attributeURI)
    rows = []
    for entity_id in request:
        rows.append(
            {
                "entity_id": entity_id,
                "namespace": attribute["namespace"],
                "name": attribute["name"],
                "value": attribute["value"],
            }
        )
    query = table_entity_attribute.insert(rows)
    await database.execute(query)
    return request


@app.delete(
    "/v1/entity/{entityId}/attribute/{attributeURI:path}",
    status_code=204,
    dependencies=[Depends(get_auth)],
)
async def delete_attribute_entity_relationship(entityId: str, attributeURI: HttpUrl):
    attribute = parse_attribute_uri(attributeURI)
    statement = table_entity_attribute.delete().where(
        and_(
            table_entity_attribute.c.entity_id == entityId,
            table_entity_attribute.c.namespace == attribute["namespace"],
            table_entity_attribute.c.name == attribute["name"],
            table_entity_attribute.c.value == attribute["value"],
        )
    )
    await database.execute(statement)


if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
