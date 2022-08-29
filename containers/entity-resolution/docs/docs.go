// Package docs GENERATED BY SWAG; DO NOT EDIT
// This file was generated by swaggo/swag
package docs

import "github.com/swaggo/swag"

const docTemplate = `{
    "schemes": {{ marshal .Schemes }},
    "swagger": "2.0",
    "info": {
        "description": "{{escape .Description}}",
        "title": "{{.Title}}",
        "contact": {
            "name": "OpenTDF",
            "url": "https://www.opentdf.io"
        },
        "license": {
            "name": "BSD 3-Clause",
            "url": "https://opensource.org/licenses/BSD-3-Clause"
        },
        "version": "{{.Version}}"
    },
    "host": "{{.Host}}",
    "basePath": "{{.BasePath}}",
    "paths": {
        "/healthz": {
            "get": {
                "tags": [
                    "Service Health"
                ],
                "summary": "Check service status",
                "responses": {
                    "200": {
                        "description": "OK"
                    },
                    "503": {
                        "description": "Service Unavailable",
                        "schema": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "/resolve": {
            "post": {
                "description": "Provide an attribute type and attribute label list\nand receive a list of entity idenitifiers",
                "consumes": [
                    "application/json"
                ],
                "produces": [
                    "application/json"
                ],
                "summary": "Resolve a set of entity labels to their keycloak identifiers",
                "parameters": [
                    {
                        "description": "Entity Identifiers to be resolved",
                        "name": "Request\"",
                        "in": "body",
                        "required": true,
                        "schema": {
                            "$ref": "#/definitions/handlers.EntityResolutionRequest"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK",
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "array",
                                "items": {
                                    "$ref": "#/definitions/handlers.EntityResolution"
                                }
                            }
                        }
                    }
                }
            }
        }
    },
    "definitions": {
        "handlers.EntityIdentifier": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "example": "bob@sample.org"
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "email",
                        "username"
                    ],
                    "example": "email"
                }
            }
        },
        "handlers.EntityResolution": {
            "description": "Returns the original identifier that was used to query for the included EntityRepresentations. Includes all EntityRepresentations that are mapped to the original identifier. EntityRepresentations are generic JSON objects as returned and serialized from the entity store.",
            "type": "object",
            "properties": {
                "entityRepresentations": {
                    "description": "Generic JSON object containing a complete JSON representation of all the resolved entities and their\nproperties, as generated by the entity store.",
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": true
                    }
                },
                "original_id": {
                    "$ref": "#/definitions/handlers.EntityIdentifier"
                }
            }
        },
        "handlers.EntityResolutionRequest": {
            "description": "Request containing entity identifiers which will be used to query/resolve to an EntityRepresentation by querying the underlying store. This assumes that some entity store exists somewhere, and that user store keeps track of entities by canonical ID, and that each entity with a canonical ID might be \"searchable\" or \"identifiable\" by some other, non-canonical identifier. At least one entity identifier is required",
            "type": "object",
            "properties": {
                "entity_identifiers": {
                    "description": "enum: email,username",
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/handlers.EntityIdentifier"
                    }
                }
            }
        }
    }
}`

// SwaggerInfo holds exported Swagger Info so clients can modify it
var SwaggerInfo = &swag.Spec{
	Version:          "0.0.1",
	Host:             "",
	BasePath:         "",
	Schemes:          []string{},
	Title:            "entitlement-resolution-service",
	Description:      "An implementation of a an entity resolution service for keycloak",
	InfoInstanceName: "swagger",
	SwaggerTemplate:  docTemplate,
}

func init() {
	swag.Register(SwaggerInfo.InstanceName(), SwaggerInfo)
}
