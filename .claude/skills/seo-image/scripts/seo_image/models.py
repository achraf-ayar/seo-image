from dataclasses import dataclass, field

CORNERS = ("top-left", "top-right", "bottom-left", "bottom-right")
CORNER_LABELS = ("free", "subject", "face_or_text")


@dataclass
class Settings:
    domain: str | None = None
    watermark_enabled: bool = True
    position: str = "bottom-right"
    opacity: float = 0.6
    size: float = 2.5
    output_dir: str = "seo-images"
    context: str | None = None

    def to_dict(self):
        return {
            "domain": self.domain,
            "watermark": {
                "enabled": self.watermark_enabled,
                "position": self.position,
                "opacity": self.opacity,
                "size": self.size,
            },
            "output_dir": self.output_dir,
            "context": self.context,
        }


@dataclass
class InspectedImage:
    path: str
    original_filename: str
    status: str = "ok"  # ok | unsupported | unreadable
    reason: str | None = None
    format: str | None = None  # jpeg | png | webp
    width: int | None = None  # displayed size, after EXIF orientation
    height: int | None = None
    has_gps: bool = False
    upright: bool = True
    animated: bool = False
    corner_busyness: dict = field(default_factory=dict)

    def to_dict(self):
        return dict(self.__dict__)


@dataclass
class Result:
    original_filename: str
    new_filename: str | None = None
    status: str = "ok"  # ok | failed | skipped
    reason: str | None = None
    alt: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list | None = None
    domain: str | None = None
    watermark_status: str = "none"  # applied | none | disabled | skipped
    watermark_reason: str | None = None
    watermark_position: str | None = None
    width: int | None = None
    height: int | None = None

    def to_dict(self):
        d = {k: v for k, v in self.__dict__.items() if v is not None or k in (
            "new_filename", "domain", "watermark_position")}
        return d
