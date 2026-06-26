from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    location: str | None = None


class BranchOut(BaseModel):
    id: int
    name: str
    location: str | None = None

    model_config = {"from_attributes": True}
