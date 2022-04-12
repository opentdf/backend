import json
import logging
import os
import sys
from enum import Enum
from http.client import NO_CONTENT
from typing import List, Optional

import databases as databases
import sqlalchemy
from fastapi import FastAPI, Request
from pydantic import BaseModel, Field

app = FastAPI()
logging.basicConfig(
    stream=sys.stdout, level=os.getenv("SERVER_LOG_LEVEL", "CRITICAL").upper()
)
logger = logging.getLogger(__package__)

VERSION_SPECIFICATION = "4.2.1"

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
    logger.info(f"REQUEST_METHOD {request.method} {request.url}")
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


class ClaimsRequest(BaseModel):
    algorithm: Optional[str] = None
    clientPublicSigningKey: str = Field(
        ...,
        description=("The client's public signing key. This will be echoed back as-is in the custom claims response. "
                     "If the IdP does not forward this, or the field is empty, "
                     "no claims should be returned and the request rejected as malformed.")
        )
    primaryEntityId: str = Field(
        ...,  #Field is required, no default value
        description=("The identifier for the primary entity seeking claims. "
                     "For PE auth, this will be a PE ID. For NPE auth, this will be an NPE ID.")
        )
    secondaryEntityIds: Optional[List[str]] = Field(
        [],
        description=("Optional. For PE auth, this will be one or more "
                     "NPE IDs (client-on-behalf-of-user). "
                     "For NPE auth, this may be either empty (client-on-behalf-of-itself) "
                     "or populated with one or more NPE IDs (client-on-behalf-of-other-clients, aka chaining flow)")
        )

    class Config:
        schema_extra = {
            "example": {
                "algorithm": "ec:secp256r1",
                "clientPublicSigningKey": "-----BEGIN PUBLIC KEY-----\n" +
                             "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2Q9axUqaxEfhOO2+0Xw+\n" +
                             "swa5Rb2RV0xeTX3GC9DeORv9Ip49oNy+RXvaMsdNKspPWYZZEswrz2+ftwcQOSU+\n" +
                             "efRCbGIwbSl8QBfKV9nGLlVmpDydcAIajc7YvWjQnDTEpHcJdo9y7/oogG7YcEmq\n" +
                             "S3NtVJXCmbc4DyrZpc2BmZD4y9417fSiNjTTYY3Fc19lQz07hxDQLgMT21N4N0Fz\n" +
                             "mD6EkiEpG5sdpDT/NIuGjFnJEPfqIs6TnPaX2y1OZ2/JzC+mldJFZuEqJZ/6qq/e\n" +
                             "Ylp04nWrSnXhPpTuxNZ5J0GcPbpcFgdT8173qmm5m5jAjiFCr735lH7USl15H2fW\n" +
                             "TwIDAQAB\n" +
                             "-----END PUBLIC KEY-----\n",
                "primaryEntityId": "31c871f2-6d2a-4d27-b727-e619cfaf4e7a",
                "secondaryEntityIds": ["46a871f2-6d2a-4d27-b727-e619cfaf4e7b"],
            }
        }


class AttributeDisplay(BaseModel):
    attribute: str
    displayName: Optional[str]


class EntityEntitlements(BaseModel):
    entity_identifier: str
    entity_attributes: List[Optional[AttributeDisplay]] = []

# NOTE This object schema should EXACTLY match the TDF spec's ClaimsObject schema
# as defined here: https://github.com/virtru/tdf-spec/blob/master/schema/ClaimsObject.md
class EntitlementsObject(BaseModel):
    client_public_signing_key: str
    entitlements: List[EntityEntitlements]
    tdf_spec_version: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "entitlements": [
                    {
                        "entity_identifier": "cliententityid-14443434-1111343434-asdfdffff",
                        "entity_attributes": [
                            {
                                "attribute": "https://example.com/attr/Classification/value/S",
                                "displayName": "classification"
                            },
                            {
                                "attribute": "https://example.com/attr/COI/value/PRX",
                                "displayName": "category of intent"
                            }
                        ]
                    },
                    {
                        "entity_identifier": "dd-ff-eeeeee1134r34434-user-beta",
                        "entity_attributes": [
                            {
                                "attribute": "https://example.com/attr/Classification/value/U",
                                "displayName": "classification"
                            },
                            {
                                "attribute": "https://example.com/attr/COI/value/PRZ",
                                "displayName": "category of intent"
                            }
                        ]
                    }
                ],
                "client_public_signing_key": "-----BEGIN PUBLIC KEY-----\n" +
                                             "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy18Efi6+3vSELpbK58gC\n" +
                                             "A9vJxZtoRHR604yi707h6nzTsTSNUg5mNzt/nWswWzloIWCgA7EPNpJy9lYn4h1Z\n" +
                                             "6LhxEgf0wFcaux0/C19dC6WRPd6 ... XzNO4J38CoFz/\n" +
                                             "wwIDAQAB\n" +
                                             "-----END PUBLIC KEY-----",
                "tdf_spec_version:": VERSION_SPECIFICATION,
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
    return {"tdf_spec_version": VERSION_SPECIFICATION}


class ProbeType(str, Enum):
    liveness = "liveness"
    readiness = "readiness"


@app.get("/healthz", status_code=NO_CONTENT, include_in_schema=False)
async def read_liveness(probe: ProbeType = ProbeType.liveness):
    if probe == ProbeType.readiness:
        await database.execute("SELECT 1")


@app.post("/claims", response_model=EntitlementsObject)
async def create_entitlements_object_for_jwt_claims(request: ClaimsRequest):
    logger.info("/claims POST [%s]", request)
    entity_entitlements = []

    # Get entitlements for primary entity, as reported by IdP
    entity_entitlements.append(await get_entitlements_for_entity_id(request.primaryEntityId))

    # Get any additional entitlements for any secondary entities involved in this entitlement grant request.
    for secondary_entity_id in request.secondaryEntityIds:
        entity_entitlements.append(await get_entitlements_for_entity_id(secondary_entity_id))

    entitlement_object = EntitlementsObject(
        client_public_signing_key=request.clientPublicSigningKey,
        entitlements=entity_entitlements,
    )
    return entitlement_object


async def get_entitlements_for_entity_id(entityId: str):
    entitlements = []
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == entityId
    )
    result = await database.fetch_all(query)
    for row in result:
        uri = f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}"
        entitlements.append(AttributeDisplay(attribute=uri, displayName=row.get(table_entity_attribute.c.name)))

    entity_entitlements = EntityEntitlements(
        entity_identifier=entityId,
        entity_entitlements=entitlements,
    )

    return entity_entitlements

if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
