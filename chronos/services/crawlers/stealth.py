import asyncio
import math
import random
from dataclasses import dataclass
from typing import Literal, Optional, Tuple

from loguru import logger
from playwright.async_api import Page


@dataclass
class StealthConfig:
    typo_probability: float = 0.08
    typing_delay: Tuple[float, float] = (0.12, 0.4)
    typo_pause: Tuple[float, float] = (0.15, 0.35)
    reading_delay: Tuple[float, float] = (2.0, 5.0)
    hover_delay: Tuple[float, float] = (0.7, 1.8)
    idle_delay: Tuple[float, float] = (2.0, 4.0)
    # Mouse move
    mouse_move_steps_range: Tuple[int, int] = (10, 25)
    mouse_move_amplitude: int = 20
    mouse_move_noise: float = 2.0
    mouse_move_pause: Tuple[float, float] = (0.01, 0.03)
    mouse_path_pause: Tuple[float, float] = (0.4, 0.8)
    # Scroll
    scroll_delta_range: Tuple[int, int] = (120, 350)
    search_scroll_delta_range: Tuple[int, int] = (180, 350)
    scroll_pause: Tuple[float, float] = (0.3, 0.7)
    search_scroll_pause: Tuple[float, float] = (0.2, 0.5)
    search_scroll_between_pause: Tuple[float, float] = (0.7, 1.5)
    scroll_extra_pause_chance: float = 0.3
    scroll_extra_pause: Tuple[float, float] = (1.0, 2.0)


class AsyncStealth:
    def __init__(self, config: StealthConfig = StealthConfig()):
        self._config = config

    async def simulate_typing(self, page: Page, selector: str, text: str) -> None:
        """Simulates human-like typing on a given selector, including random delays and occasional typos."""
        logger.debug(f"⌨️ Typing text on selector: '{selector}'")

        await page.locator(selector=selector).focus()
        await self.random_sleep(1.0, 2.0)

        for char in text:
            await page.keyboard.type(text=char)
            await self.random_sleep(*self._config.typing_delay)
            if random.random() < self._config.typo_probability:
                await page.keyboard.press(key="Backspace")
                await self.random_sleep(*self._config.typo_pause)
                await page.keyboard.type(text=char)

    async def simulate_human_reading(
        self,
        page: Page,
        duration: float = 20.0,
        context_type: str = "default",
    ) -> None:
        """
        Simulates human reading behavior by randomly performing actions (scroll, mouse move, hover, idle) on the page.
        The action distribution can be adjusted by context_type.
        """
        logger.debug("📖 Simulating human reading behavior on the page")

        action_map = {
            "search": ["search"] * 5 + ["scroll"] * 2 + ["mouse"] * 2 + ["hover"] * 2 + ["idle"],
            "default": ["scroll"] * 4 + ["mouse"] * 2 + ["hover"] * 2 + ["idle"],
        }
        actions = action_map.get(context_type, action_map["default"])

        action_funcs = {
            "search": lambda: self.random_scroll(page, cycles=1, mode="search"),
            "scroll": lambda: self.random_scroll(page, cycles=1, mode="normal"),
            "mouse": lambda: self.random_move_mouse(page),
            "hover": lambda: self.random_hover_element(page),
            "idle": lambda: self.random_sleep(*self._config.idle_delay),
        }

        total = 0.0
        while total < duration:
            action = random.choice(actions)
            await action_funcs[action]()
            delay = random.uniform(*self._config.reading_delay)
            await self.random_sleep(delay, delay + 1.2)
            total += delay

    async def random_scroll(
        self,
        page: Page,
        cycles: int = 1,
        mode: Literal["normal", "search"] = "normal",
    ) -> None:
        """Simulates random scrolling on the page. Supports both normal and search-like scroll patterns."""
        match mode:
            case "search":
                logger.debug("🔍 Scrolling the page in search mode")

                for _ in range(cycles):
                    # Scroll down several times with random delta and pause
                    for _ in range(random.randint(3, 5)):
                        await page.mouse.wheel(0, random.randint(*self._config.search_scroll_delta_range))
                        await self.random_sleep(*self._config.search_scroll_pause)
                    await self.random_sleep(*self._config.search_scroll_between_pause)

                    # Scroll up several times with random delta and pause
                    for _ in range(random.randint(2, 4)):
                        await page.mouse.wheel(0, -random.randint(*self._config.search_scroll_delta_range))
                        await self.random_sleep(*self._config.search_scroll_pause)
                    await self.random_sleep(*self._config.search_scroll_between_pause)

            case "normal":
                logger.debug("🖱️ Scrolling the page in normal mode")

                direction = 1
                for _ in range(cycles):
                    # Scroll in one direction
                    for _ in range(random.randint(2, 4)):
                        delta = random.randint(*self._config.scroll_delta_range) * direction
                        await page.mouse.wheel(0, delta)
                        await self.random_sleep(*self._config.scroll_pause)

                    direction *= -1  # Reverse direction
                    for _ in range(random.randint(2, 4)):
                        delta = random.randint(*self._config.scroll_delta_range) * direction
                        await page.mouse.wheel(0, delta)
                        await self.random_sleep(*self._config.scroll_pause)

                # Occasionally add an extra pause to mimic human unpredictability
                if random.random() < self._config.scroll_extra_pause_chance:
                    await self.random_sleep(*self._config.scroll_extra_pause)

    async def random_move_mouse(
        self,
        page: Page,
        target_x: Optional[int] = None,
        target_y: Optional[int] = None,
    ) -> None:
        """
        Moves the mouse in a human-like, curved path within the viewport. If target_x and target_y are provided,
        the mouse will move toward the specified target; otherwise, it moves to a random location.
        """
        if target_x is not None and target_y is not None:
            logger.debug(f"🖱️ Moving mouse towards target ({target_x}, {target_y}) with human-like path")
        else:
            logger.debug("🖱️ Moving mouse randomly with human-like path")

        viewport = page.viewport_size
        if not viewport:
            return

        width = viewport["width"]
        height = viewport["height"]

        for _ in range(random.randint(3, 5)):
            x_start = random.randint(0, width)
            y_start = random.randint(0, height)
            x_end = target_x if target_x is not None else random.randint(0, width)
            y_end = target_y if target_y is not None else random.randint(0, height)
            steps = random.randint(*self._config.mouse_move_steps_range)

            for step in range(steps + 1):
                t = step / steps  # progress: 0 -> 1

                # Linear movement from start to end
                x_linear = x_start + (x_end - x_start) * t
                y_linear = y_start + (y_end - y_start) * t

                # Apply sine wave perturbation to simulate a curved, human-like path
                amplitude = self._config.mouse_move_amplitude  # pixels deviation from path
                curve = math.sin(t * math.pi)  # smooth curve from 0 -> 1 -> 0

                # Calculate perpendicular offset for the curve
                dx = x_end - x_start
                dy = y_end - y_start
                length = math.hypot(dx, dy)
                if length == 0:
                    continue
                offset_x = -dy / length * amplitude * curve
                offset_y = dx / length * amplitude * curve

                # Add small random noise to the path for realism
                x = x_linear + offset_x + random.uniform(-self._config.mouse_move_noise, self._config.mouse_move_noise)
                y = y_linear + offset_y + random.uniform(-self._config.mouse_move_noise, self._config.mouse_move_noise)

                await page.mouse.move(x, y)
                await self.random_sleep(*self._config.mouse_move_pause)

            await self.random_sleep(*self._config.mouse_path_pause)

    async def random_hover_element(self, page: Page, selector: str = "a, button, div, img, span") -> None:
        """
        Randomly hovers the mouse over a visible element (a, button, div, img, span)
        on the page to simulate user curiosity.
        """
        logger.debug("🖱️ Hovering over a random visible element on the page")

        elements = await page.query_selector_all(selector=selector)
        visible = []

        for element in elements:
            try:
                # Only consider visible elements
                visible.append(element) if await element.is_visible() else None
            except Exception:
                continue

        if visible:
            element = random.choice(visible)
            try:
                await element.hover()
                await self.random_sleep(*self._config.hover_delay)
            except Exception:
                logger.debug("Failed to hover an element, skipping.")

    async def random_sleep(self, min_delay: float = 1.5, max_delay: float = 4.0) -> None:
        """Sleeps for a random duration between min_delay and max_delay to simulate human reaction time."""
        value = random.uniform(min_delay, max_delay)
        await asyncio.sleep(value)
