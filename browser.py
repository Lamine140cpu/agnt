from playwright.sync_api import sync_playwright
import os

class Browser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def start(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1280,800"
            ]
        )
        context = self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = context.new_page()

    def stop(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def navigate(self, url: str):
        self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

    def screenshot(self, path: str) -> str:
        self.page.screenshot(path=path, full_page=False)
        return path

    def click(self, x: int, y: int):
        self.page.mouse.click(x, y)
        self.page.wait_for_load_state("domcontentloaded", timeout=5000)

    def type_text(self, text: str):
        self.page.keyboard.type(text, delay=50)

    def scroll(self, direction: str, amount: int):
        if direction == "down":
            self.page.mouse.wheel(0, amount)
        elif direction == "up":
            self.page.mouse.wheel(0, -amount)

    def get_url(self) -> str:
        return self.page.url

    def get_title(self) -> str:
        return self.page.title()
