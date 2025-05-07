class Selectors:
    class Wrappers:
        V1 = ".captcha-disable-scroll"
        V2 = ".captcha-verify-container"

    class PuzzleV1:
        UNIQUE_IDENTIFIER = ".captcha-disable-scroll img.captcha_verify_img_slide"
        PUZZLE = "#captcha-verify-image"
        PIECE = "img.captcha_verify_img_slide"
        SLIDER_DRAG_BUTTON = ".secsdk-captcha-drag-icon"
        REFRESH_BUTTON = ".secsdk_captcha_refresh"

    class PuzzleV2:
        UNIQUE_IDENTIFIER = ".captcha-verify-container #captcha-verify-image"
        PUZZLE = "#captcha-verify-image"
        PIECE_IMAGE_CONTAINER = ".captcha-verify-container div[draggable=true]:has(img[draggable=false])"
        PIECE = ".captcha-verify-container .cap-absolute img"
        SLIDER_DRAG_BUTTON = ".secsdk-captcha-drag-icon"

    class ShapesV1:
        UNIQUE_IDENTIFIER = ".captcha-disable-scroll .verify-captcha-submit-button"
        IMAGE = "#captcha-verify-image"
        SUBMIT_BUTTON = ".verify-captcha-submit-button"

    class ShapesV2:
        UNIQUE_IDENTIFIER = ".captcha-verify-container .cap-relative button.cap-w-full"
        IMAGE = ".captcha-verify-container div.cap-relative img"
        SUBMIT_BUTTON = ".captcha-verify-container .cap-relative button.cap-w-full"

    class IconV1:
        UNIQUE_IDENTIFIER = ".captcha-disable-scroll .verify-captcha-submit-button"
        IMAGE = "#captcha-verify-image"
        TEXT = ".captcha_verify_bar"
        SUBMIT_BUTTON = ".verify-captcha-submit-button"

    class IconV2:
        UNIQUE_IDENTIFIER = ".captcha-verify-container .cap-relative button.cap-w-full"
        IMAGE = ".captcha-verify-container div.cap-relative img"
        TEXT = ".captcha-verify-container > div > div > span"
        SUBMIT_BUTTON = ".captcha-verify-container .cap-relative button.cap-w-full"

    class RotateV1:
        UNIQUE_IDENTIFIER = ".captcha-disable-scroll [data-testid=whirl-inner-img]"
        INNER = "[data-testid=whirl-inner-img]"
        OUTER = "[data-testid=whirl-outer-img]"
        SLIDE_BAR = ".captcha_verify_slide--slidebar"
        SLIDER_DRAG_BUTTON = ".secsdk-captcha-drag-icon"

    class RotateV2:
        UNIQUE_IDENTIFIER = ".captcha-verify-container > div > div > div > img.cap-absolute"
        INNER = ".captcha-verify-container > div > div > div > img.cap-absolute"
        OUTER = ".captcha-verify-container > div > div > div > img:first-child"
        SLIDE_BAR = ".captcha-verify-container > div > div > div.cap-w-full > div.cap-rounded-full"
        SLIDER_DRAG_BUTTON = ".captcha-verify-container div[draggable=true]"
        REFRESH_BUTTON = "#captcha_refresh_button"
