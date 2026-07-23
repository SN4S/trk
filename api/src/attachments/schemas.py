from pydantic import BaseModel, computed_field

from src.schemas import UtcDatetime

class AttachmentOut(BaseModel):
    id: int
    filename: str
    file_path: str
    content_type: str
    created_at: UtcDatetime

    @computed_field
    @property
    def file_url(self) -> str:
        if self.file_path.startswith("/"):
            return self.file_path
        return f"/{self.file_path}"

    model_config = {"from_attributes": True}
