import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from chromedriver_py import binary_path  # For chromedriver-py


class YouTubePlayer:
    def __init__(self):
        self.driver = webdriver.Chrome(service=ChromeService(binary_path))
        self.wait = WebDriverWait(self.driver, 20)
        self.video_element = None
        self.was_muted_for_ad = False
        self.non_skippable_detected = False
        self.title_printed = False  # To print title only once

    def open_video(self, url: str):
        self.driver.maximize_window()
        print("Browser window maximized.")
        self.driver.get(url)

        # Wait for video player and get the <video> element
        self.video_element = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
        print("Video player loaded.")

    def play_video(self):
        try:
            play_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.ytp-play-button.ytp-button"))
            )
            play_button.click()
            time.sleep(1)
            print("Video started playing.")
        except TimeoutException:
            print("Video already playing or play button not needed.")

    def print_video_title(self):
        """Fetch and print the video title once using the yt-formatted-string in ytd-watch-metadata."""
        if not self.title_printed:
            try:
                title_element = self.wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "yt-formatted-string.style-scope.ytd-watch-metadata"))
                )
                title_text = title_element.text.strip()
                if title_text:
                    print(f"Video title: {title_text}")
                    self.title_printed = True
            except TimeoutException:
                print("Could not find video title element.")

    def is_ad_playing(self) -> bool:
        """Reliable ad detection using the 'ad-showing' class on the main video element."""
        if self.video_element:
            try:
                classes = self.video_element.get_attribute("class")
                if classes and "ad-showing" in classes:
                    return True
            except Exception:
                pass
        return False

    def get_visible_current_time(self) -> str:
        """Get the text from the visible .ytp-time-current element."""
        try:
            current_time_elem = self.driver.find_element(By.CSS_SELECTOR, "span.ytp-time-current")
            return current_time_elem.text.strip()
        except NoSuchElementException:
            return "unknown"

    def skip_skippable_ad(self):
        """Continuously monitor and skip skippable ads with a precise 0.5-second delay."""
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
                time.sleep(0.5)  # Precise 0.5s delay after clickable
                skip_button.click()

                current_time_text = self.get_visible_current_time()
                print(f"Skippable ad skipped at {current_time_text} (0.5s delay applied).")
                self.non_skippable_detected = False  # Reset for next ad
                return True
            except TimeoutException:
                continue
        return False

    def detect_non_skippable_ad(self):
        """Log non-skippable ad start only once per ad."""
        if self.is_ad_playing() and not self.non_skippable_detected:
            # Confirm no skip button
            try:
                self.driver.find_element(By.CSS_SELECTOR,
                    ".ytp-ad-skip-button-modern, .ytp-ad-skip-button, .ytp-skip-ad-button")
                return
            except NoSuchElementException:
                pass

            current_time_text = self.get_visible_current_time()
            print(f"Non-skippable ad played at {current_time_text}.")
            self.non_skippable_detected = True

    def mute_for_ad(self):
        if self.is_ad_playing() and not self.was_muted_for_ad:
            if self.video_element:
                self.driver.execute_script("arguments[0].muted = true;", self.video_element)
                print("Volume muted during ad.")
                self.was_muted_for_ad = True

    def unmute_after_ad(self):
        if not self.is_ad_playing() and self.was_muted_for_ad:
            if self.video_element:
                self.driver.execute_script("arguments[0].muted = false;", self.video_element)
                print("Volume restored after ad.")
                self.was_muted_for_ad = False
                self.non_skippable_detected = False

    def is_video_ended(self) -> bool:
        if self.video_element:
            try:
                ended = self.driver.execute_script("return arguments[0].ended;", self.video_element)
                return bool(ended)
            except Exception:
                pass
        return False

    def go_to_next_video(self):
        try:
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a.ytp-next-button.ytp-button"))
            )
            next_button.click()
            print("Moved to next video in playlist.")
            time.sleep(3)
            self.video_element = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            self.play_video()
            self.title_printed = False  # Allow new title for next video
            return True
        except TimeoutException:
            return False

    def run(self):
        url = input("Enter the YouTube video or playlist URL: ").strip()
        self.open_video(url)
        self.play_video()

        try:
            while True:
                # Print video title once per video (early in loop)
                self.print_video_title()

                # Always try to skip skippable ads
                self.skip_skippable_ad()

                # Detect and log non-skippable ads
                self.detect_non_skippable_ad()

                # Mute/unmute handling
                self.mute_for_ad()
                self.unmute_after_ad()

                # Video end check
                if not self.is_ad_playing() and self.is_video_ended():
                    print("Video ended.")

                    if self.go_to_next_video():
                        continue
                    else:
                        print("Single video finished. Playback complete.")
                        break

                time.sleep(0.5)

        finally:
            input("\nPress Enter to close the browser...")
            self.driver.quit()


if __name__ == "__main__":
    player = YouTubePlayer()
    player.run()