/* The sign-in page is only shown when nobody is signed in on this browser. Any Field pages kept for
   offline use by an earlier user are removed here, so the next person never sees them, even when the
   earlier user's session simply expired without signing out (Joel, 15 Oct 2026, B2).
   Site Plans (23 Oct 2026): the plans kept on the phone for offline use are removed the same way. */
(function () {
  try {
    if (!("caches" in window)) {
      return;
    }
    caches.keys().then(function (keys) {
      keys.forEach(function (key) {
        if (key.indexOf("calibrayt-field-shell") === 0 || key.indexOf("calibrayt-site-plans") === 0) {
          caches.delete(key);
        }
      });
    }).catch(function () {});
  } catch (err) {
    /* storage unavailable: nothing is kept */
  }
})();
