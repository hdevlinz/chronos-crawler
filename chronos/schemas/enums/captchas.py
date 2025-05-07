from enum import StrEnum


class CaptchaType(StrEnum):
    PUZZLE_V1 = "PUZZLE_V1"
    PUZZLE_V2 = "PUZZLE_V2"
    SHAPES_V1 = "SHAPES_V1"
    SHAPES_V2 = "SHAPES_V2"
    ICON_V1 = "ICON_V1"
    ICON_V2 = "ICON_V2"
    ROTATE_V1 = "ROTATE_V1"
    ROTATE_V2 = "ROTATE_V2"
