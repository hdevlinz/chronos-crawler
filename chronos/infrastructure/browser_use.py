import json
import os

from browser_use import Browser, BrowserContextConfig
from browser_use.browser.context import BrowserContext
from loguru import logger
from playwright.async_api import Browser as PlaywrightBrowser
from playwright.async_api import BrowserContext as PlaywrightBrowserContext


class PatchedBrowserContext(BrowserContext):
    async def _create_context(self, browser: PlaywrightBrowser) -> PlaywrightBrowserContext:
        """Creates a new browser context with anti-detection measures and loads cookies if available."""
        if self.browser.config.cdp_url and len(browser.contexts) > 0:
            context = browser.contexts[0]

        elif self.browser.config.chrome_instance_path and len(browser.contexts) > 0:
            # Connect to existing Chrome instance instead of creating new one
            context = browser.contexts[0]

        else:
            # Original code for creating new context
            context = await browser.new_context(
                viewport=self.config.browser_window_size,
                no_viewport=False,
                user_agent=self.config.user_agent,
                java_script_enabled=True,
                bypass_csp=self.config.disable_security,
                ignore_https_errors=self.config.disable_security,
                record_video_dir=self.config.save_recording_path,
                record_video_size=self.config.browser_window_size,
                locale=self.config.locale,
            )

        if self.config.trace_path:
            await context.tracing.start(screenshots=True, snapshots=True, sources=True)

        # Load cookies if they exist
        if self.config.cookies_file and os.path.exists(self.config.cookies_file):
            with open(self.config.cookies_file, "r") as f:
                cookies = json.load(f)
                logger.info(f"Loaded {len(cookies)} cookies from {self.config.cookies_file}")  # noqa: G004
                await context.add_cookies(cookies)

        # Expose anti-detection scripts
        await context.add_init_script(
            """
               // Webdriver property
               Object.defineProperty(navigator, 'webdriver', {
                  get: () => false
               });

               // Languages
               Object.defineProperty(navigator, 'languages', {
                  get: () => ['en-US']
               });

               // Plugins
               // Object.defineProperty(navigator, 'plugins', {
               //    get: () => [1, 2, 3, 4, 5]
               // });

               // Uncomment this if need to use chrome extensions
               // if (!window.chrome) { window.chrome = {} };
               // if (!window.chrome.runtime) { window.chrome.runtime = {} };

               // Chrome runtime
               window.chrome = { runtime: {} };

               // Permissions
               const originalQuery = window.navigator.permissions.query;
               window.navigator.permissions.query = (parameters) => (
                  parameters.name === 'notifications' ?
                     Promise.resolve({ state: Notification.permission }) :
                     originalQuery(parameters)
               );
               (function () {
                  const originalAttachShadow = Element.prototype.attachShadow;
                  Element.prototype.attachShadow = function attachShadow(options) {
                     return originalAttachShadow.call(this, { ...options, mode: "open" });
                  };
               })();
            """
        )

        context.set_default_timeout(timeout=10000)  # 10 seconds
        context.set_default_navigation_timeout(timeout=60000)  # 60 seconds

        return context


class BrowserClient(Browser):
    async def new_context(self, config: BrowserContextConfig = BrowserContextConfig()) -> PatchedBrowserContext:
        return PatchedBrowserContext(config=config, browser=self)
