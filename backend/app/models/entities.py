from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


def utc_now() -> datetime:
    return datetime.now(UTC)

class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: str = ""
    role: str = "General Assistant"
    theme: str = "Nebula"
    system_prompt: str = ""
    created_at: datetime = Field(default_factory=utc_now)

class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(index=True)
    filename: str
    content_type: str = "application/octet-stream"
    status: str = "processing"
    path: str = ""
    pages: int = 0
    chunks: int = 0
    created_at: datetime = Field(default_factory=utc_now)

class Chunk(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(index=True)
    document_id: int = Field(index=True)
    text: str
    embedding: str
    metadata_json: str = "{}"

class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(index=True)
    kind: str
    prompt: str = ""
    response: str
    metadata_json: str = "{}"
    created_at: datetime = Field(default_factory=utc_now)
