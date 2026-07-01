from datetime import datetime
from pydantic import BaseModel


class ImgflipRaw(BaseModel):
    id: str
    name: str
    url: str
    width: int
    height: int
    box_count: int
    rank: int


class KYMRaw(BaseModel):
    slug: str
    name: str
    url: str
    about: str
    origin: str | None = None
    spread: str | None = None
    fetched_at: datetime


class RawTemplate(BaseModel):
    imgflip: ImgflipRaw
    kym: KYMRaw | None = None


class EnrichedFields(BaseModel):
    description: str
    caption_pattern: str
    box_labels: list[str]
    tags: list[str]


class EnrichedTemplate(BaseModel):
    id: str
    name: str
    description: str
    caption_pattern: str
    box_labels: list[str]
    tags: list[str]
    box_count: int
    image_url: str
    enriched_at: datetime
    enrichment_model: str

    def to_ini_section(self) -> str:
        return "\n".join([
            f"[{self.id}]",
            f"name = {self.name}",
            f"description = {self.description}",
            f"caption_pattern = {self.caption_pattern}",
            f"box_labels = {', '.join(self.box_labels)}",
            f"tags = {', '.join(self.tags)}",
            f"box_count = {self.box_count}",
            f"image_url = {self.image_url}",
        ])
