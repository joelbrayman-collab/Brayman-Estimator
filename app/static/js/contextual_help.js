(function () {
  "use strict";

  function message(form, name, fallback) {
    var value = form ? form.getAttribute(name) : "";
    return value || fallback;
  }

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function speechRecognition() {
    return window.SpeechRecognition || window.webkitSpeechRecognition || null;
  }

  function setAnswer(form, text) {
    var answer = form.querySelector(".contextual-help-answer");
    var speakRow = form.querySelector(".contextual-help-speak-row");
    if (!answer) {
      return;
    }
    answer.hidden = !text;
    answer.textContent = text || "";
    if (speakRow) {
      speakRow.hidden = !text || !window.speechSynthesis;
    }
  }

  function ask(form) {
    var details = form.closest(".contextual-help");
    var input = form.querySelector(".contextual-help-question");
    var question = input ? String(input.value || "").trim() : "";
    var url = form.getAttribute("action");
    if (!details || !url) {
      return;
    }
    window.fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify({
        surface: details.getAttribute("data-help-surface") || "",
        key: details.getAttribute("data-help-topic") || "",
        question: question,
      }),
    })
      .then(function (response) {
        if (!response.ok) {
          throw new Error("help-ask-failed");
        }
        return response.json();
      })
      .then(function (payload) {
        setAnswer(form, payload && payload.answer ? payload.answer : "");
      })
      .catch(function () {
        setAnswer(
          form,
          message(form, "data-help-ask-unavailable", "Help couldn't answer right now.")
        );
      });
  }

  function startVoice(form) {
    var Recognition = speechRecognition();
    var input = form.querySelector(".contextual-help-question");
    if (!Recognition) {
      setAnswer(
        form,
        message(form, "data-help-mic-unsupported", "Voice isn't available in this browser.")
      );
      return;
    }
    var recognition = new Recognition();
    recognition.lang = "en-CA";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = function (event) {
      var transcript =
        event.results && event.results[0] && event.results[0][0]
          ? event.results[0][0].transcript
          : "";
      if (input) {
        input.value = transcript;
      }
      if (transcript) {
        ask(form);
      } else {
        setAnswer(
          form,
          message(form, "data-help-no-speech", "No speech was heard.")
        );
      }
    };
    recognition.onerror = function (event) {
      var error = event && event.error ? event.error : "";
      if (error === "not-allowed" || error === "service-not-allowed") {
        setAnswer(
          form,
          message(
            form,
            "data-help-mic-denied",
            "Microphone access isn't available."
          )
        );
        return;
      }
      if (error === "no-speech") {
        setAnswer(
          form,
          message(form, "data-help-no-speech", "No speech was heard.")
        );
        return;
      }
      setAnswer(
        form,
        message(form, "data-help-voice-error", "Voice couldn't be used.")
      );
    };
    try {
      recognition.start();
    } catch (err) {
      setAnswer(
        form,
        message(form, "data-help-voice-error", "Voice couldn't be used.")
      );
    }
  }

  function speak(form) {
    var answer = form.querySelector(".contextual-help-answer");
    var stopBtn = form.querySelector("[data-help-stop]");
    if (!window.speechSynthesis || !answer || !answer.textContent) {
      return;
    }
    window.speechSynthesis.cancel();
    var utterance = new window.SpeechSynthesisUtterance(answer.textContent);
    utterance.lang = "en-CA";
    if (stopBtn) {
      stopBtn.hidden = false;
    }
    utterance.onend = function () {
      if (stopBtn) {
        stopBtn.hidden = true;
      }
    };
    window.speechSynthesis.speak(utterance);
  }

  function stopSpeak() {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
  }

  document.addEventListener("submit", function (event) {
    var form = event.target.closest(".contextual-help-ask");
    if (!form) {
      return;
    }
    event.preventDefault();
    ask(form);
  });

  document.addEventListener("click", function (event) {
    var voiceBtn = event.target.closest("[data-help-voice]");
    if (voiceBtn) {
      event.preventDefault();
      startVoice(voiceBtn.closest(".contextual-help-ask"));
      return;
    }
    var speakBtn = event.target.closest("[data-help-speak]");
    if (speakBtn) {
      event.preventDefault();
      speak(speakBtn.closest(".contextual-help-ask"));
      return;
    }
    var stopBtn = event.target.closest("[data-help-stop]");
    if (stopBtn) {
      event.preventDefault();
      stopSpeak();
      stopBtn.hidden = true;
    }
  });
})();
