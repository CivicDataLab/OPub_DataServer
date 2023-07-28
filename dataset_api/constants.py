from DatasetServer import settings

FORMAT_MAPPING = {
    "text/csv": "CSV",
    "csv": "CSV",
    "application/csv": "CSV",
    "application/json": "JSON",
    "json": "JSON",
    # "application/msword": "DOC",
    # "application/doc": "DOC",
    # "application/ms-doc": "DOC",
    # "application/pdf": "PDF",
    # "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/xml": "XML",
    "xml": "XML",
    "text/xml": "XML",
    "application/geo+json": "JSON",
    "application/gml+xml": "XML",
    "application/xhtml+xml": "XML",
    # "text/plain": "TXT",
}

IMAGE_FORMAT_MAPPING = {
    "image/png": "PNG",
    "image/jpeg": "JPEG",
    "image/svg+xml": "SVG",
}

DATAREQUEST_SWAGGER_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "version": "1.0.0",
        "title": "Access Resource"
    },
    "servers": [
        {
            "url": settings.BASE_DOMAIN
        }
    ],
    "paths": {
        "/refresh_data_token": {
            "get": {
                "description": "Returns updated data token",
                "tags": [
                    "Token"
                ],
                "operationId": "refreshDataToken",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": True,
                        "description": "Access Token",
                        "schema": {
                            "type": "string"
                        },
                        "example": "refreshToken"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            }
        },
        "/get_dist_data": {
            "get": {
                "description": "Fetches data from provider",
                "tags": [
                    "Distribution"
                ],
                "operationId": "getDistributionData",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": True,
                        "description": "Access Token",
                        "schema": {
                            "type": "string"
                        }
                    }],
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            }
        }
    }
}

GET_RESOURCE = {"/getresource": {
    "get": {
        "description": "Returns file with requested resource",
        "tags": [
            "Distribution"
        ],
        "operationId": "getResource",
        "parameters": [
            {
                "name": "token",
                "in": "query",
                "required": True,
                "description": "Access Token",
                "schema": {
                    "type": "string"
                }
            },
            {
                "name": "format",
                "in": "query",
                "required": True,
                "description": "Format of return",
                "schema": {
                    "type": "string",
                    "enum": ["CSV", "XML", "JSON"]
                }
            },
            {
                "name": "size",
                "in": "query",
                "required": True,
                "description": "number of records to return",
                "schema": {
                    "type": "integer",
                    "miniumum": 1
                },
                "example": 5
            },
            {
                "name": "from",
                "in": "query",
                "required": True,
                "description": "start of records to return",
                "schema": {
                    "type": "integer",
                    "miniumum": 0
                },
                "example": 0
            },
        ],
        "responses": {
            "200": {
                "description": "OK"
            }
        }
    }
}
}
