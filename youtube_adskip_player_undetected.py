import time
import json
import random
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class YouTubePlayer:
    def __init__(self):
        options = uc.ChromeOptions()

        # Stealth improvements built-in with undetected-chromedriver
        # Additional useful options
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-extensions")
        options.add_argument("--start-maximized")

        # Enable performance logging for network monitoring
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        # Use undetected_chromedriver (automatically patches detection vectors)
        self.driver = uc.Chrome(options=options, use_subprocess=True)
        self.wait = WebDriverWait(self.driver, 20)
        self.video_element = None
        self.non_skippable_detected = False
        self.title_printed = False

    def open_video(self, url: str):
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
            return self.driver.find_element(By.CSS_SELECTOR, "span.ytp-time-current").text.strip()
        except NoSuchElementException:
            return "unknown"

    def skip_skippable_ad(self):
        selectors = [
            ".ytp-ad-skip-button-modern",
            ".ytp-ad-skip-button",
            ".ytp-skip-ad-button",
            "button[aria-label*='Skip ad' i]",
            "button.ytp-ad-skip-button"
        ]
        for selector in selectors:
            try:
                skip_button = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                time.sleep(0.5)
                skip_button.click()
                print(f"Skippable ad skipped at {self.get_visible_current_time()}")
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
            print(f"Non-skippable ad played at {self.get_visible_current_time()}")
            self.non_skippable_detected = True

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
        try:
            logs = self.driver.get_log('performance')
            for entry in logs:
                message = json.loads(entry['message'])['message']
                if message['method'] == 'Network.responseReceived':
                    response = message['params']['response']
                    url = response['url']
                    status = response['status']
                    if ('googlevideo.com' in url or 'videoplayback' in url) and status >= 400:
                        print(f"NETWORK ERROR: {status} {url}")
        except Exception:
            pass

    def run(self):
        url = input("Enter the YouTube video or playlist URL: ").strip()
        self.open_video(url)
        self.play_video()

        try:
            while True:
                self.print_video_title()
                self.skip_skippable_ad()
                self.detect_non_skippable_ad()

                if not self.is_ad_playing() and self.is_video_ended():
                    print("Video ended.")
                    if self.go_to_next_video():
                        continue
                    else:
                        print("Single video finished. Playback complete.")
                        break

                self.check_network_errors()
                time.sleep(random.uniform(2.0, 3.0))

        finally:
            input("\nPress Enter to close the browser...")
            self.driver.quit()


if __name__ == "__main__":
    player = YouTubePlayer()
    player.run()