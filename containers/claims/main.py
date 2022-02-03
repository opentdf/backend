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
from pydantic import BaseModel

app = FastAPI()

logger = logging.getLogger(__package__)

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
    publicKey: Optional[str] = ""
    signerPublicKey: Optional[str] = ""
    userId: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "algorithm": "ec:secp256r1",
                "publicKey": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2Q9axUqaxEfhOO2+0Xw+\nswa5Rb2RV0xeTX3GC9DeORv9Ip49oNy+RXvaMsdNKspPWYZZEswrz2+ftwcQOSU+\nefRCbGIwbSl8QBfKV9nGLlVmpDydcAIajc7YvWjQnDTEpHcJdo9y7/oogG7YcEmq\nS3NtVJXCmbc4DyrZpc2BmZD4y9417fSiNjTTYY3Fc19lQz07hxDQLgMT21N4N0Fz\nmD6EkiEpG5sdpDT/NIuGjFnJEPfqIs6TnPaX2y1OZ2/JzC+mldJFZuEqJZ/6qq/e\nYlp04nWrSnXhPpTuxNZ5J0GcPbpcFgdT8173qmm5m5jAjiFCr735lH7USl15H2fW\nTwIDAQAB\n-----END PUBLIC KEY-----\n",
                "userId": "31c871f2-6d2a-4d27-b727-e619cfaf4e7a",
            }
        }


class Attribute(BaseModel):
    attribute: str
    displayName: Optional[str]
    isDefault: Optional[bool]
    kasUrl: Optional[str]
    pubKey: Optional[str]


class Claims(BaseModel):
    client_public_signing_key: Optional[str] = ""
    entity_id: Optional[str]
    subject_attributes: List[Attribute]
    tdf_spec_version: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "subject_attributes": [
                    {
                        "attribute": "https://example.com/attr/Classification/value/Secret",
                        "displayName": "classification",
                    }
                ],
                "client_public_signing_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy18Efi6+3vSELpbK58gC\nA9vJxZtoRHR604yi707h6nzTsTSNUg5mNzt/nWswWzloIWCgA7EPNpJy9lYn4h1Z\n6LhxEgf0wFcaux0/C19dC6WRPd6 ... XzNO4J38CoFz/\nwwIDAQAB\n-----END PUBLIC KEY-----",
                "tdf_spec_version:": "x.y.z",
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
    return {"Hello": "claims"}


class ProbeType(str, Enum):
    liveness = "liveness"
    readiness = "readiness"


@app.get("/healthz", status_code=NO_CONTENT, include_in_schema=False)
async def read_liveness(probe: ProbeType = ProbeType.liveness):
    if probe == ProbeType.readiness:
        await database.execute("SELECT 1")


@app.post("/v1/claims", response_model=Claims, response_model_exclude_unset=True)
async def create_claims_object(request: ClaimsRequest):
    logger.info("/v1/claims POST [%s]", request)
    attributes = []
    # select
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == request.userId
    )
    result = await database.fetch_all(query)
    for row in result:
        uri = f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}"
        attributes.append(Attribute(attribute=uri))
    return Claims(
        entity_id=request.userId or None,
        public_key=request.publicKey or None,
        client_public_signing_key=request.signerPublicKey or None,
        subject_attributes=attributes,
    )


if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
