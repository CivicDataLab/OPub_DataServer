FORMAT_MAPPING = {
    "text/csv": "CSV",
    "csv": "CSV",
    "application/json": "JSON",
    "json": "JSON",
    "application/msword": "DOC",
    "application/doc": "DOC",
    "application/ms-doc": "DOC",
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "application/xml": "XML",
    "xml": "XML",
    "application/geo+json": "JSON",
    "application/gml+xml": "XML",
    "application/gzip": "GZIP",
    "application/xhtml+xml": "XML",

}

DATAREQUEST_SWAGGER_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "version": "1.0.0",
        "title": "Access Resource"
    },
    "servers": [
        {
            "url": "https://idpbe.civicdatalab.in/"
        }
    ],
    "paths": {
        "/refreshtoken": {
            "get": {
                "description": "Returns updaed access token",
                "tags": [
                    "Token"
                ],
                "operationId": "refreshToken",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": "true",
                        "description": "Access Token",
                        "schema": {
                            "type": "string"
                        },
                        "example": "asdfaasdfasdfsdfasdfasdf"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "OK"
                    }
                }
            }
        },
        "/getresource": {
            "get": {
                "description": "Returns file with requested resource",
                "tags": [
                    "Resource"
                ],
                "operationId": "getResource",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": "true",
                        "description": "Access Token",
                        "schema": {
                            "type": "string"
                        }
                    },
                    {
                        "name": "format",
                        "in": "query",
                        "required": "true",
                        "description": "Format of return",
                        "schema": {
                            "type": "string",
                            "enum": ["CSV", "XML", "JSON"]
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
