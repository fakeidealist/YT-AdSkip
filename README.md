This project is a small Selenium-based utility that opens a YouTube video or playlist in Chrome, automatically starts playback, aggressively skips skippable ads, logs non‑skippable ads, and mutes/unmutes during ads for a smoother watching experience.
​
Features:
Prints the current video’s title
Automatically opens a YouTube video or playlist URL in a maximized Chrome window and starts playback.
Detects ads via the ad-showing class on the main <video> element for reliable ad detection.
Skips skippable ads using multiple CSS selectors (e.g. .ytp-ad-skip-button-modern, .ytp-ad-skip-button) with a precise 0.5‑second delay after the skip button becomes clickable.
Logs when a non‑skippable ad is playing once per ad, including the visible current playback time.
Mutes audio during ads and restores volume after ads, tracking whether the video was muted for the current ad.
Detects when a video ends; if a playlist is playing, it automatically clicks the “Next” button and continues playback, printing the new video’s title once.
​
Requirements:
Python 3.8+ (recommended).
Google Chrome installed (matching the ChromeDriver binary shipped by chromedriver_py).
​
The following Python packages:
selenium
chromedriver_py
A reasonably stable network connection (for reliable YouTube and DOM loading).
​
You can install dependencies with:
pip install selenium chromedriver-py
