import time
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from chromedriver_py import binary_path

class YouTubePlayer:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self.driver = webdriver.Chrome(service=ChromeService(binary_path), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 20)
        self.video_element = None
        self.non_skippable_detected = False
        self.title_printed = False

    def open_video(self, url: str):
        self.driver.maximize_window()
        self.driver.get(url)
        self.video_element = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        time.sleep(2)

    def is_video_playing(self) -> bool:
        if self.video_element:
            try:
                return not self.driver.execute_script("return arguments[0].paused;", self.video_element)
            except Exception:
                pass
        return False

    def play_video(self):
        if self.is_video_playing():
            return

        try:
            play_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-play-button.ytp-button"))
            )
            play_button.click()
            time.sleep(1)
        except TimeoutException:
            pass

    def print_video_title(self):
        if not self.title_printed:
            page_title = self.driver.title.strip()
            cleaned_title = page_title
            if cleaned_title.endswith(" - YouTube"):
                cleaned_title = cleaned_title[:-10].strip()
            import re
            cleaned_title = re.sub(r"\s*\(\d.+?views\)\s*$", "", cleaned_title).strip()
            if cleaned_title:
                print(f"Video title: {cleaned_title}")
                self.title_printed = True

    def is_ad_playing(self) -> bool:
        if self.video_element:
            try:
                classes = self.video_element.get_attribute("class")
                if classes and "ad-showing" in classes:
                    return True
            except Exception:
                pass
        return False

    def get_visible_current_time(self) -> str:
        try:
            current_time_elem = self.driver.find_element(By.CSS_SELECTOR, "span.ytp-time-current")
            return current_time_elem.text.strip()
        except NoSuchElementException:
            return "unknown"

    def skip_skippable_ad(self):
        skip_selectors = [
            ".ytp-ad-skip-button-modern",
            ".ytp-ad-skip-button",
            ".ytp-skip-ad-button",
            "button[aria-label*='Skip ad' i]",
            "button.ytp-ad-skip-button"
        ]

        for selector in skip_selectors:
            try:
                skip_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                time.sleep(0.5)
                skip_button.click()
                current_time_text = self.get_visible_current_time()
                print(f"Skippable ad skipped at {current_time_text}")
                self.non_skippable_detected = False
                return True
            except TimeoutException:
                continue
        return False

    def detect_non_skippable_ad(self):
        if self.is_ad_playing() and not self.non_skippable_detected:
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                    ".ytp-ad-skip-button-modern, .ytp-ad-skip-button, .ytp-skip-ad-button")
                return
            except NoSuchElementException:
                pass
            current_time_text = self.get_visible_current_time()
            print(f"Non-skippable ad played at {current_time_text}")
            self.non_skippable_detected = True

    # Mute functions commented out as requested
    # def mute_for_ad(self):
    #     ...

    # def unmute_after_ad(self):
    #     ...

    def is_video_ended(self) -> bool:
        if self.video_element:
            try:
                return self.driver.execute_script("return arguments[0].ended;", self.video_element)
            except Exception:
                pass
        return False

    def go_to_next_video(self):
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ytp-next-button.ytp-button"))
            )
            next_button.click()
            time.sleep(3)
            self.video_element = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            self.play_video()
            self.title_printed = False
            return True
        except TimeoutException:
            return False

    def check_network_errors(self):
        logs = self.driver.get_log('performance')
        for entry in logs:
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.responseReceived':
                response = message['params']['response']
                url = response['url']
                status = response['status']
                if 'googlevideo.com' in url or 'videoplayback' in url:
                    if status >= 400:
                        print(f"NETWORK ERROR: {status} on {url}")

    def run(self):
        url = input("Enter the YouTube video or playlist URL: ").strip()
        self.open_video(url)
        self.play_video()

        try:
            while True:
                self.print_video_title()
                self.skip_skippable_ad()
                self.detect_non_skippable_ad()

                # Mute calls commented out
                # self.mute_for_ad()
                # self.unmute_after_ad()

                if not self.is_ad_playing() and self.is_video_ended():
                    print("Video ended.")
                    if self.go_to_next_video():
                        continue
                    else:
                        print("Single video finished. Playback complete.")
                        break

                self.check_network_errors()

                # Reduced aggressive polling with slight randomization (2-3 seconds)
                time.sleep(random.uniform(2.0, 3.0))

        finally:
            input("\nPress Enter to close the browser...")
            self.driver.quit()


if __name__ == "__main__":
    player = YouTubePlayer()
    player.run()