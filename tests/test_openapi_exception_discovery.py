import fastapi
from fastapi import FastAPI, HTTPException


# Module level helpers for testing recursion
def check_item_module(item_id: str):
    if item_id == "foo":
        raise HTTPException(status_code=404, detail="Item not found nested")


def deep_check_module(item_id: str):
    if item_id == "foo":
        raise HTTPException(status_code=401, detail="Unauthorized deep")


def intermediate_check_module(item_id: str):
    deep_check_module(item_id)


def test_openapi_exception_discovery_simple():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        if item_id == "foo":
            raise HTTPException(status_code=404, detail="Item not found")
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "404" in responses
    assert responses["404"]["description"] == "Item not found"
    assert "detail" in responses["404"]["content"]["application/json"]["schema"]["properties"]
    assert "HTTPException" not in openapi_schema.get("components", {}).get("schemas", {})

def test_openapi_exception_discovery_multiple():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        if item_id == "foo":
            raise HTTPException(status_code=404, detail="Item not found")
        if item_id == "bar":
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "404" in responses
    assert "403" in responses


def test_openapi_exception_discovery_nested():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        check_item_module(item_id)
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "404" in responses
    assert responses["404"]["description"] == "Item not found nested"


def test_openapi_exception_discovery_deep_nested():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        intermediate_check_module(item_id)
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "401" in responses
    assert responses["401"]["description"] == "Unauthorized deep"


def test_openapi_exception_discovery_no_duplicates():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}", responses={404: {"description": "Already documented"}})
    def read_item(item_id: str):
        if item_id == "foo":
            raise HTTPException(status_code=404, detail="Item not found")
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "404" in responses
    assert responses["404"]["description"] == "Already documented"


def test_openapi_exception_discovery_attribute_name():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        if item_id == "foo":
            raise fastapi.HTTPException(
                status_code=400, detail="Bad request via attribute"
            )
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "400" in responses
    assert responses["400"]["description"] == "Bad request via attribute"


def test_openapi_exception_discovery_unsupported_dynamic_status():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        status = 405
        if item_id == "foo":
            raise HTTPException(status_code=status, detail="Dynamic status")
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    # The current implementation uses ast.unparse, so status_code will be the string "status"
    assert "status" in responses
    assert responses["status"]["description"] == "Dynamic status"


class CustomHTTPException(HTTPException):
    pass


def test_openapi_exception_discovery_custom_inheritance():
    app = FastAPI(discover_exceptions=True)

    @app.get("/items/{item_id}")
    def read_item(item_id: str):
        if item_id == "foo":
            raise CustomHTTPException(status_code=418, detail="I am a teapot")
        return {"item_id": item_id}

    openapi_schema = app.openapi()
    responses = openapi_schema["paths"]["/items/{item_id}"]["get"]["responses"]
    assert "418" in responses
    assert responses["418"]["description"] == "I am a teapot"
