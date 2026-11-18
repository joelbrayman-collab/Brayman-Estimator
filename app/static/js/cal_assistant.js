/* Cal Assistant, Phase 1 — Find It.
 * Opens only when the header icon is clicked. Sends a GET query and shows links.
 * Never submits a change: results are ordinary links to records the user can open. */
(function () {
    "use strict";

    var launch = document.getElementById("cal-launch");
    var panel = document.getElementById("cal-panel");
    if (!launch || !panel) {
        return;
    }
    var form = document.getElementById("cal-form");
    var input = document.getElementById("cal-query");
    var results = document.getElementById("cal-results");
    var closeBtn = document.getElementById("cal-close");
    var findUrl = panel.getAttribute("data-cal-find-url");
    var pending = null;

    function open() {
        panel.hidden = false;
        launch.setAttribute("aria-expanded", "true");
        window.setTimeout(function () { input.focus(); }, 0);
    }

    function close(returnFocus) {
        if (panel.hidden) {
            return;
        }
        panel.hidden = true;
        launch.setAttribute("aria-expanded", "false");
        if (returnFocus) {
            launch.focus();
        }
    }

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) {
            node.className = className;
        }
        if (text) {
            node.textContent = text;
        }
        return node;
    }

    function render(data) {
        results.textContent = "";
        if (data.open) {
            // One clear answer: go straight there (Joel, 18 Nov 2026, FG-042). Opening only; nothing is saved.
            results.appendChild(el("p", "cal-message", panel.getAttribute("data-cal-opening")));
            window.location.assign(data.open);
            return;
        }
        if (data.message) {
            var msg = el("p", "cal-message" + (data.status === "none" ? " is-none" : ""), data.message);
            results.appendChild(msg);
        }
        if (data.hint) {
            results.appendChild(el("p", "cal-message is-none", data.hint));
        }
        (data.groups || []).forEach(function (group) {
            var section = el("section", "cal-group");
            section.appendChild(el("h3", "cal-group-title", group.title));
            var list = el("ul");
            group.items.forEach(function (item) {
                var li = el("li");
                var a = el("a", "cal-result");
                a.href = item.url;
                a.setAttribute("data-cal-kind", item.kind || "");
                a.appendChild(el("span", "cal-result-title", item.title));
                if (item.detail) {
                    a.appendChild(el("span", "cal-result-detail", item.detail));
                }
                li.appendChild(a);
                list.appendChild(li);
            });
            section.appendChild(list);
            results.appendChild(section);
        });
    }

    function search(query) {
        if (pending) {
            pending.abort();
        }
        pending = window.AbortController ? new AbortController() : null;
        results.textContent = "";
        results.appendChild(el("p", "cal-message is-none", panel.getAttribute("data-cal-searching")));
        fetch(findUrl + "?q=" + encodeURIComponent(query) + "&here=" + encodeURIComponent(window.location.pathname + window.location.search), {
            method: "GET",
            credentials: "same-origin",
            headers: { "Accept": "application/json" },
            signal: pending ? pending.signal : undefined
        }).then(function (response) {
            var type = response.headers.get("Content-Type") || "";
            if (response.redirected || response.status === 401 || type.indexOf("application/json") === -1) {
                throw new Error("signed-out");
            }
            if (!response.ok) {
                throw new Error("error");
            }
            return response.json();
        }).then(render).catch(function (err) {
            if (err && err.name === "AbortError") {
                return;
            }
            results.textContent = "";
            var key = err && err.message === "signed-out" ? "data-cal-signed-out" : "data-cal-error";
            results.appendChild(el("p", "cal-message is-none", panel.getAttribute(key)));
        });
    }

    // ---- Voice (FG-042). The browser's own speech recognition, as on the Help microphone. It fills the box and
    // searches; it never submits anything but a read-only search.
    var micBtn = document.getElementById("cal-mic");
    var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
    var listening = false;

    function say(key) {
        results.textContent = "";
        results.appendChild(el("p", "cal-message is-none", panel.getAttribute(key)));
    }

    function listen() {
        if (listening) {
            return;
        }
        open();
        if (!Recognition) {
            say("data-cal-mic-unsupported");
            return;
        }
        var recognition = new Recognition();
        recognition.lang = "en-CA";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;
        listening = true;
        document.body.classList.add("cal-is-listening");
        if (micBtn) {
            micBtn.classList.add("is-listening");
        }
        say("data-cal-listening");
        function done() {
            listening = false;
            document.body.classList.remove("cal-is-listening");
            if (micBtn) {
                micBtn.classList.remove("is-listening");
            }
        }
        recognition.onresult = function (event) {
            var transcript = event.results && event.results[0] && event.results[0][0] ? event.results[0][0].transcript : "";
            transcript = (transcript || "").trim();
            if (!transcript) {
                say("data-cal-no-speech");
                return;
            }
            input.value = transcript;
            search(transcript);
        };
        recognition.onerror = function (event) {
            var error = event && event.error ? event.error : "";
            if (error === "not-allowed" || error === "service-not-allowed") {
                say("data-cal-mic-denied");
            } else if (error === "no-speech") {
                say("data-cal-no-speech");
            } else if (error !== "aborted") {
                say("data-cal-voice-error");
            }
        };
        recognition.onend = done;
        try {
            recognition.start();
        } catch (err) {
            done();
            say("data-cal-voice-error");
        }
    }

    if (micBtn) {
        micBtn.addEventListener("click", listen);
    }
    document.addEventListener("click", function (event) {
        var talk = event.target.closest("[data-cal-talk]");
        if (talk) {
            event.preventDefault();
            event.stopPropagation();
            listen();
        }
    }, true);

    launch.addEventListener("click", function () {
        if (panel.hidden) {
            open();
        } else {
            close(true);
        }
    });
    closeBtn.addEventListener("click", function () { close(true); });
    form.addEventListener("submit", function (event) {
        event.preventDefault();
        var query = (input.value || "").trim();
        if (query) {
            search(query);
        }
    });
    panel.addEventListener("click", function (event) {
        var example = event.target.closest("[data-cal-example]");
        if (example) {
            input.value = example.getAttribute("data-cal-example");
            search(input.value);
        }
    });
    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !panel.hidden) {
            close(true);
        }
    });
    document.addEventListener("click", function (event) {
        if (panel.hidden) {
            return;
        }
        if (panel.contains(event.target) || launch.contains(event.target)) {
            return;
        }
        close(false);
    });
}());
