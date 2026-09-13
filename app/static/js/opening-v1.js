(function () {
  "use strict";

  function readConfig() {
    var el = document.getElementById("opening-v1-config");
    if (!el) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch (err) {
      return null;
    }
  }

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function daysSince(ms) {
    return (Date.now() - ms) / 86400000;
  }

  function eligible(cfg) {
    try {
      if (prefersReducedMotion()) {
        return false;
      }
      if (window.sessionStorage.getItem(cfg.sessionKey) === "1") {
        return false;
      }
      var last = window.localStorage.getItem(cfg.lastShownKey);
      if (last) {
        var shown = parseInt(last, 10);
        if (!isNaN(shown) && daysSince(shown) < cfg.suppressDays) {
          return false;
        }
      }
      return true;
    } catch (err) {
      return false;
    }
  }

  function markShown(cfg) {
    try {
      window.sessionStorage.setItem(cfg.sessionKey, "1");
      window.localStorage.setItem(cfg.lastShownKey, String(Date.now()));
    } catch (err) {
      /* fail open */
    }
  }

  function dismiss(overlay, cfg, recordVisit) {
    if (!overlay || overlay.getAttribute("data-opening-done") === "1") {
      return;
    }
    overlay.setAttribute("data-opening-done", "1");
    overlay.classList.add("is-done");
    overlay.style.removeProperty("display");
    overlay.setAttribute("hidden", "hidden");
    overlay.setAttribute("aria-hidden", "true");
    if (recordVisit) {
      markShown(cfg);
    } else {
      try {
        window.sessionStorage.setItem(cfg.sessionKey, "1");
      } catch (err) {
        /* fail open */
      }
    }
    var video = overlay.querySelector("video");
    if (video) {
      try {
        video.pause();
      } catch (err) {
        /* ignore */
      }
    }
  }

  function buildOverlay(cfg) {
    var overlay = document.createElement("div");
    overlay.id = "opening-v1-overlay";
    overlay.className = "opening-v1-overlay";
    overlay.setAttribute("role", "dialog");
    overlay.setAttribute("aria-label", "CalibraytAI opening");
    overlay.setAttribute("aria-modal", "true");

    var video = document.createElement("video");
    video.setAttribute("playsinline", "");
    video.setAttribute("muted", "");
    video.muted = true;
    video.setAttribute("preload", "auto");
    video.setAttribute("disablepictureinpicture", "");
    video.poster = cfg.poster;
    video.setAttribute("aria-hidden", "true");

    var webm = document.createElement("source");
    webm.src = cfg.webm;
    webm.type = "video/webm";
    var mp4 = document.createElement("source");
    mp4.src = cfg.mp4;
    mp4.type = "video/mp4";
    video.appendChild(webm);
    video.appendChild(mp4);

    var skip = document.createElement("button");
    skip.type = "button";
    skip.className = "opening-v1-skip";
    skip.id = "opening-v1-skip";
    skip.textContent = "Skip";

    overlay.appendChild(video);
    overlay.appendChild(skip);
    document.body.appendChild(overlay);

    function close(recordVisit) {
      dismiss(overlay, cfg, recordVisit !== false);
    }

    skip.addEventListener("click", function () {
      close(true);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        event.preventDefault();
        close(true);
      }
    });
    video.addEventListener("ended", function () {
      close(true);
    });
    video.addEventListener("error", function () {
      close(false);
    });
    video.addEventListener("abort", function () {
      close(false);
    });

    window.setTimeout(function () {
      if (overlay.getAttribute("data-opening-done") === "1") {
        return;
      }
      close(false);
    }, cfg.timeoutMs);

    var playAttempt = video.play();
    if (playAttempt && typeof playAttempt.then === "function") {
      playAttempt.catch(function () {
        /* Autoplay blocked: keep poster + Skip visible; timeout still fail-opens. */
      });
    }

    skip.focus();
    return overlay;
  }

  function init() {
    var cfg = readConfig();
    if (!cfg) {
      return;
    }
    if (!eligible(cfg)) {
      return;
    }
    try {
      buildOverlay(cfg);
    } catch (err) {
      /* fail open — login remains */
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
