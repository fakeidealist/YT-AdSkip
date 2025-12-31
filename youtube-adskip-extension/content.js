(() => {
  console.log('[YouTube Ad-Skip Player] Content script initialized.');

  const state = {
    wasMutedForAd: false,
    nonSkippableDetected: false,
    titlePrinted: false
  };

  const getVideoElement = () => document.querySelector('video');

  const getVisibleCurrentTime = () => {
    const el = document.querySelector('span.ytp-time-current');
    return el ? el.textContent.trim() : 'unknown';
  };

  const isAdPlaying = () => {
    const video = getVideoElement();
    if (!video) return false;
    const classes = video.getAttribute('class') || '';
    // YouTube adds 'ad-showing' to the main <video> when an ad plays. [web:12][web:15][web:18]
    return classes.includes('ad-showing');
  };

  const muteVideo = () => {
    const video = getVideoElement();
    if (video) video.muted = true;
  };

  const unmuteVideo = () => {
    const video = getVideoElement();
    if (video) video.muted = false;
  };

  const isVideoEnded = () => {
    const video = getVideoElement();
    return video ? !!video.ended : false;
  };

  const goToNextVideo = () => {
    const nextBtn = document.querySelector('a.ytp-next-button.ytp-button');
    if (!nextBtn) return false;
    nextBtn.click();
    console.log('[YouTube Ad-Skip Player] Moved to next video in playlist.');
    return true;
  };

  const printVideoTitleOnce = () => {
    if (state.titlePrinted) return;
    const titleEl = document.querySelector(
      'yt-formatted-string.style-scope.ytd-watch-metadata'
    );
    if (!titleEl) return;
    const title = titleEl.textContent.trim();
    if (title) {
      console.log('[YouTube Ad-Skip Player] Video title:', title);
      state.titlePrinted = true;
    }
  };

  const findSkipButton = () => {
    const selectors = [
      '.ytp-ad-skip-button-modern',
      '.ytp-ad-skip-button',
      '.ytp-skip-ad-button',
      "button[aria-label*='Skip ad' i]",
      'button.ytp-ad-skip-button'
    ];
    for (const sel of selectors) {
      const btn = document.querySelector(sel);
      if (btn) return btn;
    }
    return null;
  };

  const skipSkippableAd = () => {
    const btn = findSkipButton();
    if (!btn) return false;

    // Match Python: 0.5s after skip becomes clickable. [file:22]
    setTimeout(() => {
      btn.click();
      const t = getVisibleCurrentTime();
      console.log(
        `[YouTube Ad-Skip Player] Skippable ad skipped at ${t} (0.5s delay applied).`
      );
      state.nonSkippableDetected = false;
    }, 500);

    return true;
  };

  const detectNonSkippableAd = () => {
    // Log once per ad when ad is playing and no skip button exists. [file:22]
    if (!isAdPlaying() || state.nonSkippableDetected) return;

    const btn = findSkipButton();
    if (btn) return; // There is a skip button, so treat as skippable.

    const t = getVisibleCurrentTime();
    console.log(
      `[YouTube Ad-Skip Player] Non-skippable ad played at ${t}.`
    );
    state.nonSkippableDetected = true;
  };

  const tick = () => {
    const video = getVideoElement();
    if (!video) {
      setTimeout(tick, 500);
      return;
    }

    // Print video title once per video (early in loop). [file:22]
    printVideoTitleOnce();

    // Always try to skip skippable ads. [file:22]
    skipSkippableAd();

    // Detect and log non-skippable ads. [file:22]
    detectNonSkippableAd();

    const adPlaying = isAdPlaying();

    // Mute/unmute handling. [file:22]
    if (adPlaying && !state.wasMutedForAd) {
      muteVideo();
      console.log('[YouTube Ad-Skip Player] Volume muted during ad.');
      state.wasMutedForAd = true;
    } else if (!adPlaying && state.wasMutedForAd) {
      unmuteVideo();
      console.log(
        '[YouTube Ad-Skip Player] Volume restored after ad.'
      );
      state.wasMutedForAd = false;
      state.nonSkippableDetected = false;
    }

    // Video end check when not in ad. [file:22]
    if (!adPlaying && isVideoEnded()) {
      console.log('[YouTube Ad-Skip Player] Video ended.');
      if (goToNextVideo()) {
        state.titlePrinted = false; // Allow new title for next video. [file:22]
        setTimeout(tick, 3000);
        return;
      } else {
        console.log(
          '[YouTube Ad-Skip Player] Single video finished. Playback complete.'
        );
        return;
      }
    }

    // Mirror Python loop sleep of ~0.5s. [file:22]
    setTimeout(tick, 500);
  };

  const startWhenReady = () => {
    const video = getVideoElement();
    if (!video) {
      setTimeout(startWhenReady, 500);
      return;
    }

    // Equivalent to play_video(): try clicking main play button. [file:22]
    const playBtn = document.querySelector(
      'button.ytp-play-button.ytp-button'
    );
    if (playBtn) {
      playBtn.click();
      console.log('[YouTube Ad-Skip Player] Video started playing.');
      setTimeout(tick, 1000);
    } else {
      console.log(
        '[YouTube Ad-Skip Player] Video already playing or play button not needed.'
      );
      tick();
    }
  };

  // Handle SPA navigation (YouTube changes URL without full reload). [web:18]
  let lastUrl = location.href;

  const onUrlChange = () => {
    if (location.href === lastUrl) return;
    lastUrl = location.href;
    console.log('[YouTube Ad-Skip Player] Navigation detected, resetting state.');
    state.wasMutedForAd = false;
    state.nonSkippableDetected = false;
    state.titlePrinted = false;
    setTimeout(startWhenReady, 1000);
  };

  const observeNavigation = () => {
    const observer = new MutationObserver(onUrlChange);
    observer.observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  };

  window.addEventListener('load', () => {
    setTimeout(startWhenReady, 1000);
    observeNavigation();
  });
})();