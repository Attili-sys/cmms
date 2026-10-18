"""Tests for base schemas, camelCase serialization, and exception handlers."""

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from src.schemas._base import CamelModel, IdDTO, SuccessResponse
from src.schemas.errors import CustomException, register_exception_handlers


class SampleModel(CamelModel):
    user_id: int
    first_name: str
    is_active: bool = True


def test_camel_model_serialization_and_population():
    # Populate by snake_case
    obj1 = SampleModel(user_id=1, first_name="Alice", is_active=True)
    dump1 = obj1.model_dump(by_alias=True)
    assert dump1 == {"userId": 1, "firstName": "Alice", "isActive": True}

    # Populate by camelCase
    obj2 = SampleModel.model_validate({"userId": 2, "firstName": "Bob", "isActive": False})
    assert obj2.user_id == 2
    assert obj2.first_name == "Bob"
    assert not obj2.is_active


def test_id_dto():
    dto = IdDTO(id=99)
    assert dto.id == 99
    assert dto.model_dump(by_alias=True) == {"id": 99}


def test_success_response():
    resp = SuccessResponse(success=True, message="Resource created")
    assert resp.success is True
    assert resp.message == "Resource created"
    assert resp.model_dump(by_alias=True) == {"success": True, "message": "Resource created"}


def test_custom_exception_properties():
    e1 = CustomException(404, "Entity missing")
    assert e1.status_code == 404
    assert e1.message == "Entity missing"

    e2 = CustomException(status_code=403, message="Denied")
    assert e2.status_code == 403
    assert e2.message == "Denied"

    e3 = CustomException("Bad request", 400)
    assert e3.status_code == 400
    assert e3.message == "Bad request"


def test_exception_handlers_endpoints():
    test_app = FastAPI()
    register_exception_handlers(test_app)

    @test_app.get("/test/custom")
    def raise_custom():
        raise CustomException(status_code=402, message="Payment required")

    @test_app.get("/test/http")
    def raise_http():
        raise HTTPException(status_code=404, detail="Item not found")

    @test_app.post("/test/validation")
    def test_validation(body: SampleModel):
        return body

    @test_app.get("/test/integrity")
    def raise_integrity():
        raise IntegrityError("INSERT INTO...", params={}, orig=Exception("unique violation"))

    @test_app.get("/test/permission")
    def raise_permission():
        raise PermissionError("Action denied by policy")

    client = TestClient(test_app)

    # CustomException
    r1 = client.get("/test/custom")
    assert r1.status_code == 402
    assert r1.json() == {"message": "Payment required", "success": False}

    # HTTPException
    r2 = client.get("/test/http")
    assert r2.status_code == 404
    assert r2.json() == {"message": "Item not found", "success": False}

    # RequestValidationError -> 400
    r3 = client.post("/test/validation", json={"userId": "not-an-int"})
    assert r3.status_code == 400
    assert "message" in r3.json()
    assert r3.json()["success"] is False

    # IntegrityError -> 409
    r4 = client.get("/test/integrity")
    assert r4.status_code == 409
    assert r4.json() == {"message": "Database integrity violation", "success": False}

    # PermissionError -> 403
    r5 = client.get("/test/permission")
    assert r5.status_code == 403
    assert r5.json() == {"message": "Action denied by policy", "success": False}
