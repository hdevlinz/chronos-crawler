from typing import List

from pydantic import BaseModel, Field


class PuzzleCaptchaResponse(BaseModel):
    status: str
    confidence: float
    slide_x_proportion: float = Field(..., validation_alias="slideXProportion")
    image_width: float = Field(..., validation_alias="imageWidth")
    image_height: float = Field(..., validation_alias="imageHeight")
    x: float
    x1: float
    slide_distance: float = Field(..., validation_alias="slideDistance")
    box: List[float]


class RotateCaptchaResponse(BaseModel):
    angle: int


class ProportionalPoint(BaseModel):
    proportion_x: float
    proportion_y: float


class IconCaptchaResponse(BaseModel):
    proportional_points: list[ProportionalPoint]


class ShapesCaptchaResponse(BaseModel):
    point_one_proportion_x: float
    point_one_proportion_y: float
    point_two_proportion_x: float
    point_two_proportion_y: float
