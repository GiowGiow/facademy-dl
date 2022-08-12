import base64
import json
import pickle

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from misc import file_path


class PageLoader:
    def __init__(self, cookie_file="cookies.json"):
        self.cookie_file = cookie_file
        self.start_selenium_driver(cookie_file)

    def start_selenium_driver(self, cookie_file="cookies.json"):
        user_agent = "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
        self.driver = self.load_chrome_driver(user_agent)
        self.set_cookies(cookie_file)

    def load_chrome_driver(self, user_agent: str) -> webdriver.Chrome:
        """Loads chrome driver with a custom User Agent"""
        opts = Options()
        opts.add_argument(user_agent)
        opts.add_argument("--headless")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(options=opts)

    def set_cookies(self, cookie_file: str):
        # Load browser cookies from json
        with open(file_path(cookie_file), "r") as f:
            cookies = json.loads(f.read())

        # Enables network tracking so we may use Network.setCookie method
        self.driver.execute_cdp_cmd("Network.enable", {})

        # Iterate through the dict and add all the cookies
        for cookie in cookies:
            # Set the actual cookie
            self.driver.execute_cdp_cmd("Network.setCookie", cookie)

        # Disable network tracking
        self.driver.execute_cdp_cmd("Network.disable", {})

    def save_cookie(self, cookies_file: str = "cookies.pkl"):
        with open(file_path(cookies_file), "wb") as cookie_file:
            pickle.dump(self.driver.get_cookies(), cookie_file)

    def load_page(self, page_url) -> str | None:
        html = None
        try:
            self.driver.get(page_url)
            html = self.driver.page_source
        except Exception as e:
            print(f"Something failed while loading the page: {page_url}")
            print(e)
            if "page crash" in str(e):
                print("Trying to restart the driver...")
                self.start_selenium_driver(self.cookie_file)
                print("Trying to request the page again...")
                self.driver.get(page_url)
                html = self.driver.page_source
        finally:
            return html

    def save_screenshot(self, screen_shot_path: str = "screenshot") -> None:
        # Ref: https://stackoverflow.com/a/52572919/
        original_size = self.driver.get_window_size()
        required_width = self.driver.execute_script(
            "return document.body.parentNode.scrollWidth"
        )
        required_height = self.driver.execute_script(
            "return document.body.parentNode.scrollHeight"
        )
        self.driver.set_window_size(required_width, required_height)
        self.driver.find_element_by_tag_name("body").screenshot(
            screen_shot_path + ".png"
        )  # avoids scrollbar
        self.driver.set_window_size(
            original_size["width"], original_size["height"]
        )

    def save_screenshot_as_pdf(self, file_path: str):
        self.send_devtools("Emulation.setEmulatedMedia", {"media": "screen"})
        pdf_options = {
            "paperHeight": 92,
            "paperWidth": 8,
            "printBackground": True,
        }
        self.save_as_pdf(file_path + ".pdf", pdf_options)

    def send_devtools(self, cmd, params={}):
        resource = (
            "/session/%s/chromium/send_command_and_get_result"
            % self.driver.session_id
        )
        url = self.driver.command_executor._url + resource
        body = json.dumps({"cmd": cmd, "params": params})
        response = self.driver.command_executor._request("POST", url, body)
        if response.get("value") is not None:
            return response.get("value")
        else:
            return None

    def save_as_pdf(self, path, options={}):
        result = self.send_devtools("Page.printToPDF", options)
        if result is not None:
            with open(path, "wb") as file:
                file.write(base64.b64decode(result["data"]))
            return True
        else:
            return False

    def save_html(self, html_file_path: str = "out"):
        with open(file_path(html_file_path) + ".html", "w") as f:
            f.write(self.driver.page_source)
