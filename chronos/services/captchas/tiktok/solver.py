import asyncio
import math
import random
import re
from typing import Optional

from loguru import logger
from playwright.async_api import FloatRect, expect

from chronos.schemas.enums.captchas import CaptchaType
from chronos.services.captchas.base import BaseCaptchaSolver
from chronos.services.captchas.tiktok.selectors import TiktokSelectors


class TiktokCaptchaSolver(BaseCaptchaSolver):
    async def captcha_is_present(self, timeout: int = 15) -> bool:
        try:
            tiktok_locator = self._page.locator(
                selector=f"{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}"
            )
            await expect(tiktok_locator.first).to_be_visible(timeout=timeout * 1000)
            logger.debug(f"[!] Selector '{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}' is visible")

        except (TimeoutError, AssertionError):
            logger.debug(f"[OK] Selector '{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}' not visible")
            return False

        return True

    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        try:
            tiktok_locator = self._page.locator(
                selector=f"{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}"
            )
            await expect(tiktok_locator.first).to_have_count(count=0, timeout=timeout * 1000)
            logger.debug(f"[X] Selector '{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}' is not present")

        except (TimeoutError, AssertionError):
            logger.debug(f"[!] Selector '{TiktokSelectors.Wrappers.V1}, {TiktokSelectors.Wrappers.V2}' still present")
            return False

        return True

    async def identify_captcha(self) -> Optional[CaptchaType]:  # noqa: C901
        for _ in range(60):
            try:
                if await self._any_selector_visible(selectors=[TiktokSelectors.PuzzleV1.UNIQUE_IDENTIFIER]):
                    logger.info(
                        f"[PUZZLE-1] Detected puzzle v1 with selector '{TiktokSelectors.PuzzleV1.UNIQUE_IDENTIFIER}'"
                    )
                    return CaptchaType.PUZZLE_V1

                if await self._any_selector_visible(selectors=[TiktokSelectors.PuzzleV2.UNIQUE_IDENTIFIER]):
                    logger.info(
                        f"[PUZZLE-2] Detected puzzle v2 with selector '{TiktokSelectors.PuzzleV2.UNIQUE_IDENTIFIER}'"
                    )
                    return CaptchaType.PUZZLE_V2

                if await self._any_selector_visible(selectors=[TiktokSelectors.ShapesV1.UNIQUE_IDENTIFIER]):
                    img_url = await self._get_image_url(selector=TiktokSelectors.ShapesV1.IMAGE)

                    if "/icon" in img_url:
                        logger.info("[ICON-1] Detected icon v1")
                        return CaptchaType.ICON_V1

                    if "/3d" in img_url:
                        logger.info("[SHAPES-1] Detected shapes v1")
                        return CaptchaType.SHAPES_V1

                    logger.warning(
                        f"[WARN] Did not see '/3d' in image source url ({img_url}) but returning shapes v1 anyway"
                    )
                    return CaptchaType.SHAPES_V1

                if await self._any_selector_visible(selectors=[TiktokSelectors.ShapesV2.UNIQUE_IDENTIFIER]):
                    img_url = await self._get_image_url(selector=TiktokSelectors.ShapesV2.IMAGE)

                    if "/icon" in img_url:
                        logger.info("[ICON-2] Detected icon v2")
                        return CaptchaType.ICON_V2

                    if "/3d" in img_url:
                        logger.info("[SHAPES-2] Detected shapes v2")
                        return CaptchaType.SHAPES_V2

                    logger.warning(
                        f"[WARN] Did not see '/3d' in image source url ({img_url}) but returning shapes v2 anyway"
                    )
                    return CaptchaType.SHAPES_V2

                if await self._any_selector_visible(selectors=[TiktokSelectors.RotateV1.UNIQUE_IDENTIFIER]):
                    logger.info(
                        f"[ROTATE-1] Detected rotate v1 with selector '{TiktokSelectors.RotateV1.UNIQUE_IDENTIFIER}'"
                    )
                    return CaptchaType.ROTATE_V1

                if await self._any_selector_visible(selectors=[TiktokSelectors.RotateV2.UNIQUE_IDENTIFIER]):
                    logger.info(
                        f"[ROTATE-2] Detected rotate v2 with selector '{TiktokSelectors.RotateV2.UNIQUE_IDENTIFIER}'"
                    )
                    return CaptchaType.ROTATE_V2

                await asyncio.sleep(0.5)

            except Exception:
                logger.error("[ERR] Exception occurred, trying again")
                await asyncio.sleep(0.5)

        return None

    async def solve_puzzle_v1(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[PUZZLE-1] Puzzle v1 solving attempt {retry_count + 1} of {retries}")

            await self._page.wait_for_timeout(random.uniform(5, 10))
            if not await self._any_selector_visible(selectors=[TiktokSelectors.PuzzleV1.PIECE]):
                logger.warning("[WARN] Piece image was not present")
                continue

            puzzle_url = await self._get_image_url(selector=TiktokSelectors.PuzzleV1.PUZZLE)
            piece_url = await self._get_image_url(selector=TiktokSelectors.PuzzleV1.PIECE)

            piece_left = await self._get_style_attribute(
                selector=TiktokSelectors.PuzzleV1.PIECE,
                attr="left",
                type_cast=float,
            )

            solution = await self._client.get_puzzle_solution(
                payload={
                    "puzzleImageUrl": puzzle_url,
                    "pieceImageUrl": piece_url,
                },
            )

            puzzle_box = await self._get_bounding_box(selector=TiktokSelectors.PuzzleV1.PUZZLE)
            puzzle_width = puzzle_box["width"], puzzle_box["height"]

            x_solution = math.ceil(float(solution.x1))
            await self._drag_element_horizontal(
                x_offset=x_solution - piece_left,
                puzzle_width=puzzle_width,
                selector=TiktokSelectors.PuzzleV1.SLIDER_DRAG_BUTTON,
            )

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.PuzzleV1.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def solve_puzzle_v2(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[PUZZLE-2] Puzzle v2 solving attempt {retry_count + 1} of {retries}")

            if not await self._any_selector_visible(selectors=[TiktokSelectors.PuzzleV2.PIECE]):
                logger.warning("[WARN] Piece image was not present")
                continue

            puzzle_url = await self._get_image_url(selector=TiktokSelectors.PuzzleV2.PUZZLE)
            piece_url = await self._get_image_url(selector=TiktokSelectors.PuzzleV2.PIECE)
            solution = await self._client.get_puzzle_solution(
                payload={
                    "puzzleImageUrl": puzzle_url,
                    "pieceImageUrl": piece_url,
                },
            )

            await self._drag_until_translate_x_matches(
                target_translate_x=int(solution.x1),
                drag_ele_selector=TiktokSelectors.PuzzleV2.SLIDER_DRAG_BUTTON,
                watch_ele_selector=TiktokSelectors.PuzzleV2.PIECE_IMAGE_CONTAINER,
            )

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.PuzzleV2.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def solve_shapes_v1(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[SHAPES-1] Shapes v1 solving attempt {retry_count + 1} of {retries}")

            if not await self._any_selector_visible(selectors=[TiktokSelectors.ShapesV1.IMAGE]):
                logger.warning("[WARN] Shapes image was not present")
                continue

            shapes_url = await self._get_image_url(selector=TiktokSelectors.ShapesV1.IMAGE)
            solution = await self._client.get_shapes_solution(
                payload={"shapesImageUrl": shapes_url},
            )

            image_bounding_box = await self._get_bounding_box(selector=TiktokSelectors.ShapesV1.IMAGE)
            await self._click_proportional(
                bounding_box=image_bounding_box,
                proportion_x=solution.point_one_proportion_x,
                proportion_y=solution.point_one_proportion_y,
            )
            await self._click_proportional(
                bounding_box=image_bounding_box,
                proportion_x=solution.point_two_proportion_x,
                proportion_y=solution.point_two_proportion_y,
            )
            await self._page.locator(selector=TiktokSelectors.ShapesV1.SUBMIT_BUTTON).click()

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.ShapesV1.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def solve_shapes_v2(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[SHAPES-2] Shapes v2 solving attempt {retry_count + 1} of {retries}")

            if not await self._any_selector_visible(selectors=[TiktokSelectors.ShapesV2.IMAGE]):
                logger.warning("[WARN] Shapes image was not present")
                continue

            shapes_url = await self._get_image_url(selector=TiktokSelectors.ShapesV2.IMAGE)
            solution = await self._client.get_shapes_solution(
                payload={"shapesImageUrl": shapes_url},
            )

            image_bounding_box = await self._get_bounding_box(selector=TiktokSelectors.ShapesV2.IMAGE)
            await self._click_proportional(
                bounding_box=image_bounding_box,
                proportion_x=solution.point_one_proportion_x,
                proportion_y=solution.point_one_proportion_y,
            )
            await self._click_proportional(
                bounding_box=image_bounding_box,
                proportion_x=solution.point_two_proportion_x,
                proportion_y=solution.point_two_proportion_y,
            )
            await self._page.locator(selector=TiktokSelectors.ShapesV2.SUBMIT_BUTTON).click()

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.ShapesV2.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def solve_icon_v1(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[ICON-1] Icon v1 solving attempt {retry_count + 1} of {retries}")

            if not await self._any_selector_visible(selectors=[TiktokSelectors.IconV1.IMAGE]):
                logger.warning("[WARN] Icon image was not present")
                continue

            challenge, image_url = await asyncio.gather(
                self._get_element_text(selector=TiktokSelectors.IconV1.TEXT),
                self._get_image_url(selector=TiktokSelectors.IconV1.IMAGE),
            )
            solution = await self._client.get_icon_solution(
                payload={
                    "iconImageUrl": image_url,
                    "iconChallenge": challenge,
                },
            )

            icon_bounding_box = await self._get_bounding_box(selector=TiktokSelectors.IconV1.IMAGE)
            for point in solution.proportional_points:
                await self._click_proportional(
                    bounding_box=icon_bounding_box,
                    proportion_x=point.proportion_x,
                    proportion_y=point.proportion_y,
                )
            await self._page.locator(TiktokSelectors.IconV1.SUBMIT_BUTTON).click()

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.IconV1.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def solve_icon_v2(self, retries: int = 3) -> bool:
        for retry_count in range(retries):
            logger.info(f"[ICON-2] Icon v2 solving attempt {retry_count + 1} of {retries}")

            if not await self._any_selector_visible(selectors=[TiktokSelectors.IconV2.IMAGE]):
                logger.warning("[WARN] Icon image was not present")
                continue

            challenge, image_url = await asyncio.gather(
                self._get_element_text(selector=TiktokSelectors.IconV2.TEXT),
                self._get_image_url(selector=TiktokSelectors.IconV2.IMAGE),
            )
            solution = await self._client.get_icon_solution(
                payload={
                    "iconImageUrl": image_url,
                    "iconChallenge": challenge,
                },
            )

            icon_bounding_box = await self._get_bounding_box(selector=TiktokSelectors.IconV2.IMAGE)
            for point in solution.proportional_points:
                await self._click_proportional(
                    bounding_box=icon_bounding_box,
                    proportion_x=point.proportion_x,
                    proportion_y=point.proportion_y,
                )
            await self._page.locator(TiktokSelectors.IconV2.SUBMIT_BUTTON).click()

            if await self.captcha_is_not_present(timeout=5):
                logger.info("[OK] Captcha solved successfully!")
                return True

            logger.info("[WAIT] Captcha still present after drag, retrying after sleep.")
            random_retry_chance = random.random()
            if random_retry_chance < 0.25:  # 25% chance: refresh captcha
                logger.info("[REFRESH] Refreshing captcha...")
                await self._page.click(TiktokSelectors.IconV2.REFRESH_BUTTON)

            elif random_retry_chance < 0.55:  # 30% chance: reload page (0.25 -> 0.55)
                logger.info("[RELOAD] Reloading page...")
                await self._page.reload(wait_until="load")

            await asyncio.sleep(random.uniform(5, 10))

        return False

    async def _get_element_text(self, selector: str) -> str:
        challenge_element = self._page.locator(selector)
        text = await challenge_element.text_content()
        if not text:
            msg = "selector was found but did not have any text."
            raise ValueError(msg)

        return text

    async def _click_proportional(
        self,
        bounding_box: FloatRect,
        proportion_x: float,
        proportion_y: float,
    ) -> None:
        """Click an element inside its bounding box at a point defined by the proportions of x and y
        to the width and height of the entire element

        Args:
            element: FloatRect to click inside
            proportion_x: float from 0 to 1 defining the proportion x location to click
            proportion_y: float from 0 to 1 defining the proportion y location to click
        """
        x_origin = bounding_box["x"]
        y_origin = bounding_box["y"]
        x_offset = proportion_x * bounding_box["width"]
        y_offset = proportion_y * bounding_box["height"]
        await self._page.mouse.move(x_origin + x_offset, y_origin + y_offset)
        await asyncio.sleep(random.randint(1, 10) / 11)
        await self._page.mouse.down()
        await asyncio.sleep(0.001337)
        await self._page.mouse.up()
        await asyncio.sleep(random.randint(1, 10) / 11)

    async def _drag_until_translate_x_matches(
        self,
        target_translate_x: int,
        drag_ele_selector: str,
        watch_ele_selector: str,
    ) -> None:
        """
        This method drags the element drag_ele_selector until the translateX value of
        watch_ele_selector is equal to translateX_target.
        This is necessary because there is a small difference between the amount the puzzle piece slides and
        the amount of pixels the drag element has been dragged in TikTok puzzle v2.
        """

        def get_translate_x_from_style(style: str) -> int:
            translate_x_match = re.search(r"(?<=translateX\()\d+", style)
            if not translate_x_match:
                raise ValueError("did not find translateX in style: " + style)
            return int(translate_x_match.group())

        drag_ele = self._page.locator(drag_ele_selector)
        watch_ele = self._page.locator(watch_ele_selector)
        style = await watch_ele.get_attribute("style")
        if not style:
            raise ValueError("element had no attribut style: " + watch_ele_selector)

        current_translate_x = get_translate_x_from_style(style)
        drag_ele_box = await drag_ele.bounding_box()
        if not drag_ele_box:
            raise AttributeError("element had no bounding box: " + drag_ele_selector)

        start_x = drag_ele_box["x"] + (drag_ele_box["width"] / 1.337)
        start_y = drag_ele_box["y"] + (drag_ele_box["height"] / 1.337)
        await self._page.mouse.move(start_x, start_y)
        await asyncio.sleep(random.randint(1, 10) / 11)
        await self._page.mouse.down()
        current_x = start_x

        while current_translate_x <= target_translate_x:
            current_x = current_x + self._mouse_step_size
            await self._page.mouse.move(current_x, start_y)
            await self._page.wait_for_timeout(self._mouse_step_delay_ms)
            style = await watch_ele.get_attribute("style")
            if not style:
                raise ValueError("element had no attribut style: " + watch_ele_selector)
            current_translate_x = get_translate_x_from_style(style)

        await asyncio.sleep(0.3)
        await self._page.mouse.up()

    async def _drag_element_horizontal(
        self,
        x_offset: float,
        selector: str,
        puzzle_width: float,
    ) -> None:
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
