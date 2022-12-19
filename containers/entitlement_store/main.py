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
from fastapi.openapi.utils import get_openapi
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
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://avatars.githubusercontent.com/u/90051847?s=200&v=4"
    }
    openapi_schema["servers"] = [{"url": os.getenv("SERVER_ROOT_PATH", "")}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


class EntitleRequest(BaseModel):
    primary_entity_id: str = Field(
        ...,  # Field is required, no default value
        description=(
            "The identifier for the primary entity entitlements will be fetched for. "
            "For PE auth, this will be a PE ID. For NPE auth, this will be an NPE ID."
        ),
    )
    secondary_entity_ids: Optional[List[str]] = Field(
        [],
        description=(
            "Optional. For PE auth, this will be one or more "
            "NPE IDs (client-on-behalf-of-user). "
            "For NPE auth, this may be either empty (client-on-behalf-of-itself) "
            "or populated with one or more NPE IDs (client-on-behalf-of-other-clients, aka chaining flow)"
        ),
    )

    class Config:
        schema_extra = {
            "example": {
                "primary_entity_id": "31c871f2-6d2a-4d27-b727-e619cfaf4e7a",
                "secondary_entity_ids": ["46a871f2-6d2a-4d27-b727-e619cfaf4e7b"],
            }
        }


class AttributeDisplay(BaseModel):
    attribute: str
    displayName: Optional[str]


class EntityEntitlements(BaseModel):
    entity_identifier: str
    entity_attributes: List[AttributeDisplay]


@app.post("/entitle", tags=["Entitlements"], response_model=List[EntityEntitlements])
async def fetch_entitlements(request: EntitleRequest):
    logger.info("/entitle POST [%s]", request)

    entity_entitlements = []
    fetchedEntitlements = await get_entitlements_for_entity_id(
        request.primary_entity_id
    )
    logger.debug("fetchedEntitlements [%s]", fetchedEntitlements)
    entity_entitlements.append(fetchedEntitlements)

    # Get any additional entitlements for any secondary entities involved in this entitlement grant request.
    for secondary_entity_id in request.secondary_entity_ids:
        entity_entitlements.append(
            await get_entitlements_for_entity_id(secondary_entity_id)
        )

    logger.debug("Returning entitlements: [%s]", entity_entitlements)
    logger.debug("Returning entitlements for entity 0: [%s]", entity_entitlements[0])
    return entity_entitlements


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


async def get_entitlements_for_entity_id(entityId: str):
    attributes = []
    query = table_entity_attribute.select().where(
        table_entity_attribute.c.entity_id == entityId
    )
    result = await database.fetch_all(query)
    logger.debug("Queried attrs for entityId [%s]", entityId)
    for row in result:
        uri = f"{row.get(table_entity_attribute.c.namespace)}/attr/{row.get(table_entity_attribute.c.name)}/value/{row.get(table_entity_attribute.c.value)}"
        logger.debug("Got attr: [%s]", uri)
        attributes.append(
            AttributeDisplay(
                attribute=uri, displayName=row.get(table_entity_attribute.c.name)
            )
        )

    entity_entitlements = EntityEntitlements(
        entity_identifier=entityId,
        entity_attributes=attributes,
    )

    logger.debug("Returning entitlements: [%s]", entity_entitlements)
    return entity_entitlements


if __name__ == "__main__":
    print(json.dumps(app.openapi()), file=sys.stdout)
