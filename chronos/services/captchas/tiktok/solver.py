import asyncio
import math
import random
from typing import Any, Dict, Optional

from loguru import logger
from playwright.async_api import expect

from chronos.schemas.enums.captchas import CaptchaType
from chronos.services.captchas.base import BaseCaptchaSolver
from chronos.services.captchas.tiktok.selectors import Selectors


class TiktokCaptchaSolver(BaseCaptchaSolver):
    async def captcha_is_present(self, timeout: int = 15) -> bool:
        try:
            tiktok_locator = self._page.locator(selector=f"{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}")
            await expect(tiktok_locator.first).to_be_visible(timeout=timeout * 1000)
            logger.debug(f"❌ Selector '{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}' is visible")

        except (TimeoutError, AssertionError):
            logger.debug(f"✅ Selector '{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}' not visible")
            return False

        return True

    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        try:
            tiktok_locator = self._page.locator(selector=f"{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}")
            await expect(tiktok_locator.first).to_have_count(count=0, timeout=timeout * 1000)
            logger.debug(f"👁️ Selector '{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}' is not present")

        except (TimeoutError, AssertionError):
            logger.debug(f"❌ Selector '{Selectors.Wrappers.V1}, {Selectors.Wrappers.V2}' still present")
            return False

        return True

    async def identify_captcha(self) -> Optional[CaptchaType]:  # noqa: C901
        for _ in range(60):
            try:
                if await self._any_selector_visible(selectors=[Selectors.PuzzleV1.UNIQUE_IDENTIFIER]):
                    logger.info(f"🧩 Detected puzzle v1 with selector '{Selectors.PuzzleV1.UNIQUE_IDENTIFIER}'")
                    return CaptchaType.PUZZLE_V1

                if await self._any_selector_visible(selectors=[Selectors.PuzzleV2.UNIQUE_IDENTIFIER]):
                    logger.info(f"🧩 Detected puzzle v2 with selector '{Selectors.PuzzleV2.UNIQUE_IDENTIFIER}'")
                    return CaptchaType.PUZZLE_V2

                if await self._any_selector_visible(selectors=[Selectors.ShapesV1.UNIQUE_IDENTIFIER]):
                    img_url = await self._get_image_url(selector=Selectors.ShapesV1.IMAGE)

                    if "/icon" in img_url:
                        logger.info("🔤 Detected icon v1")
                        return CaptchaType.ICON_V1

                    if "/3d" in img_url:
                        logger.info("🔷 Detected shapes v1")
                        return CaptchaType.SHAPES_V1

                    logger.warning(
                        f"⚠️ Did not see '/3d' in image source url ({img_url}) but returning shapes v1 anyway"
                    )
                    return CaptchaType.SHAPES_V1

                if await self._any_selector_visible(selectors=[Selectors.ShapesV2.UNIQUE_IDENTIFIER]):
                    img_url = await self._get_image_url(selector=Selectors.ShapesV2.IMAGE)

                    if "/icon" in img_url:
                        logger.info("🔤 Detected icon v2")
                        return CaptchaType.ICON_V2

                    if "/3d" in img_url:
                        logger.info("🔷 Detected shapes v2")
                        return CaptchaType.SHAPES_V2

                    logger.warning(
                        f"⚠️ Did not see '/3d' in image source url ({img_url}) but returning shapes v2 anyway"
                    )
                    return CaptchaType.SHAPES_V2

                if await self._any_selector_visible(selectors=[Selectors.RotateV1.UNIQUE_IDENTIFIER]):
                    logger.info(f"🔄 Detected rotate v1 with selector '{Selectors.RotateV1.UNIQUE_IDENTIFIER}'")
                    return CaptchaType.ROTATE_V1

                if await self._any_selector_visible(selectors=[Selectors.RotateV2.UNIQUE_IDENTIFIER]):
                    logger.info(f"🔄 Detected rotate v2 with selector '{Selectors.RotateV2.UNIQUE_IDENTIFIER}'")
                    return CaptchaType.ROTATE_V2

                await asyncio.sleep(0.5)

            except Exception:
                logger.error("❌ Exception occurred, trying again")
                await asyncio.sleep(0.5)

        return None

    async def solve_puzzle_v1(self, retries: int = 3) -> bool:
        for i in range(retries):
            logger.info(f"🧩 Puzzle v1 solving attempt {i + 1} of {retries}")

            await self._page.wait_for_timeout(random.uniform(5, 10))
            if not await self._any_selector_visible(selectors=[Selectors.PuzzleV1.PIECE]):
                logger.warning("⚠️ Piece image was not present")
                continue

            puzzle_url = await self._get_image_url(selector=Selectors.PuzzleV1.PUZZLE)
            puzzle_box = await self._get_bounding_box(selector=Selectors.PuzzleV1.PUZZLE)
            puzzle_width, puzzle_height = puzzle_box["width"], puzzle_box["height"]

            piece_url = await self._get_image_url(selector=Selectors.PuzzleV1.PIECE)
            piece_box = await self._get_bounding_box(selector=Selectors.PuzzleV1.PIECE)
            piece_width, piece_height = piece_box["width"], piece_box["height"]

            piece_left = await self._get_style_attribute(
                selector=Selectors.PuzzleV1.PIECE,
                attr="left",
                type_cast=float,
            )
            piece_top = await self._get_style_attribute(
                selector=Selectors.PuzzleV1.PIECE,
                attr="top",
                type_cast=float,
            )

            solution = await self._client.get_puzzle_solution(
                payload={
                    "puzzleImageUrl": puzzle_url,
                    "pieceImageUrl": piece_url,
                    "shrinkSize": puzzle_width,
                    "pieceShrinkWidth": piece_width,
                },
            )

            x_solution = math.ceil(float(solution.x1))
            drag_info = await self._drag_element_horizontal(
                x_offset=x_solution - piece_left,
                puzzle_width=puzzle_width,
                selector=Selectors.PuzzleV1.SLIDER_DRAG_BUTTON,
            )

            if await self.captcha_is_not_present(timeout=5):
                logger.info("✅ Captcha solved successfully!")
                await self._save_captcha_logs(
                    type="puzzle_v1",
                    status="solved",
                    platform="tiktok",
                    extra={
                        **(
                            {
                                "puzzle": {
                                    "url": puzzle_url,
                                    "width": puzzle_width,
                                    "height": puzzle_height,
                                },
                                "piece": {
                                    "url": piece_url,
                                    "width": piece_width,
                                    "height": piece_height,
                                    "left": piece_left,
                                    "top": piece_top,
                                },
                            }
                        ),
                        "solution": solution.model_dump(),
                        **drag_info,
                    },
                )
                return True

            logger.info("⏳ Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("🔄 Refreshing captcha...")
                await self._page.click(Selectors.PuzzleV1.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("🔄 Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def _drag_element_horizontal(self, x_offset: float, selector: str, puzzle_width: float) -> Dict[str, Any]:
        def ease_out_cubic(t: float) -> float:
            return 1 - pow(1 - t, 3)

        element_box = await self._get_bounding_box(selector=selector)
        start_x = element_box["x"] + (element_box["width"] / random.uniform(1.1, 1.9))
        start_y = element_box["y"] + (element_box["height"] / random.uniform(1.1, 1.9))

        # Hover around the slider before dragging
        for _ in range(random.randint(2, 4)):
            hover_x = start_x + random.uniform(-10, 10)
            hover_y = start_y + random.uniform(-5, 5)
            await self._page.mouse.move(x=hover_x, y=hover_y, steps=random.randint(5, 15))
            await asyncio.sleep(random.uniform(0.05, 0.15))

        # Occasionally click and release before the actual drag
        if random.random() < 0.3:
            await self._page.mouse.down()
            await asyncio.sleep(random.uniform(0.05, 0.1))
            await self._page.mouse.up()
            await asyncio.sleep(random.uniform(0.1, 0.2))

        # Move to the starting position
        await self._page.mouse.move(x=start_x, y=start_y, steps=random.randint(8, 15))
        await asyncio.sleep(random.uniform(0.1, 0.2))
        await self._page.mouse.down()
        await asyncio.sleep(random.uniform(0.2, 0.4))

        random_offset = random.uniform(1, 3)
        scaled_x = (x_offset + random_offset) * (puzzle_width / 552)
        target_x = math.floor(start_x + scaled_x)
        target_y = start_y

        # Drag with overshoot (drag a bit too far)
        overshoot_x = target_x + random.uniform(6.0, 18.0)
        total_steps = random.randint(45, 65)
        for step in range(total_steps):
            t = step / (total_steps - 1)
            eased = ease_out_cubic(t)
            x = start_x + (overshoot_x - start_x) * eased + random.uniform(-1.5, 1.5)
            y = start_y + math.sin(t * math.pi) * random.uniform(-2, 2)
            await self._page.mouse.move(x=x, y=y)
            await self._page.wait_for_timeout(random.uniform(4, 10))

        await asyncio.sleep(random.uniform(0.08, 0.18))

        # Drag back to the correct position
        back_steps = random.randint(15, 25)
        for step in range(1, back_steps + 1):
            t = step / back_steps
            eased = ease_out_cubic(t)
            x = overshoot_x - (overshoot_x - target_x) * eased + random.uniform(-0.8, 0.8)
            y = target_y + math.sin(t * math.pi) * random.uniform(-1, 1)
            await self._page.mouse.move(x=x, y=y)
            await self._page.wait_for_timeout(random.uniform(3, 8))

        # Small jitter around the final position
        for _ in range(random.randint(2, 4)):
            jitter_x = random.uniform(-1.2, 1.2)
            jitter_y = random.uniform(-0.7, 0.7)
            await self._page.mouse.move(x=target_x + jitter_x, y=target_y + jitter_y)
            await asyncio.sleep(random.uniform(0.01, 0.04))

        # Release the mouse
        await self._page.mouse.move(target_x, target_y, steps=random.randint(60, 90))
        await asyncio.sleep(random.uniform(3, 4))
        await self._page.mouse.up()

        # Move the mouse away after releasing
        if random.random() < 0.7:
            await self._page.mouse.move(
                target_x + random.uniform(30, 80),
                target_y + random.uniform(-10, 10),
                steps=random.randint(10, 20),
            )
            await asyncio.sleep(random.uniform(0.05, 0.15))

        return {"random_offset": random_offset, "scaled_x": scaled_x}
