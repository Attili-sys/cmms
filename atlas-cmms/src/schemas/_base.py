"""Base Pydantic models with camelCase aliasing for React frontend contract."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base Pydantic v2 model configured for camelCase serialization."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class IdDTO(CamelModel):
    """Id reference DTO matching com.grash.dto.IdDTO."""

    id: int


IdRef = IdDTO


class SuccessResponse(CamelModel):
    """Generic operation response matching com.grash.dto.SuccessResponse."""

    success: bool
    message: str
