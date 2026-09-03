(function () {
  "use strict";

  var DB_NAME = "calibai-field-v1";
  var DB_VERSION = 1;
  var LAST_PROJECT_KEY = "calibai-field-last-project-id";
  var SESSION_PROJECT_KEY = "calibai-field-project-id";
  var AUDIO_TYPES = [
    "audio/mp4",
    "audio/mp4;codecs=mp4a.40.2",
    "audio/aac",
    "audio/webm;codecs=opus",
  ];

  var dbPromise = null;
  var recorder = null;
  var recordedBlob = null;
  var recordedMime = "";
  var photos = [];
  var persistenceReady = false;

  function csrfToken() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function setStatus(text) {
    var live = document.getElementById("field-live-status");
    if (live) live.textContent = text || "";
  }

  function setFeedback(text, state) {
    var node = document.getElementById("field-feedback");
    if (!node) return;
    node.textContent = text || "";
    if (state) node.setAttribute("data-state", state);
  }

  function refreshCsrfFromHtml(html) {
    var match = /<meta name="csrf-token" content="([^"]+)"/.exec(html || "");
    if (!match) return false;
    var meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) meta.setAttribute("content", match[1]);
    return true;
  }

  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise(function (resolve, reject) {
      if (!window.indexedDB) {
        reject(new Error("IndexedDB is not available."));
        return;
      }
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function () {
        var db = req.result;
        if (!db.objectStoreNames.contains("pending_captures")) {
          db.createObjectStore("pending_captures", { keyPath: "client_capture_uuid" });
        }
        if (!db.objectStoreNames.contains("pending_originals")) {
          db.createObjectStore("pending_originals", { keyPath: "client_original_uuid" });
        }
      };
      req.onsuccess = function () {
        resolve(req.result);
      };
      req.onerror = function () {
        reject(req.error || new Error("IndexedDB could not open."));
      };
    });
    return dbPromise;
  }

  function txDone(tx) {
    return new Promise(function (resolve, reject) {
      tx.oncomplete = function () {
        resolve();
      };
      tx.onerror = function () {
        reject(tx.error || new Error("IndexedDB transaction failed."));
      };
      tx.onabort = function () {
        reject(tx.error || new Error("IndexedDB transaction aborted."));
      };
    });
  }

  function isQuotaError(err) {
    if (!err) return false;
    var name = String(err.name || "");
    var message = String(err.message || "");
    return (
      name === "QuotaExceededError" ||
      name === "NS_ERROR_DOM_QUOTA_REACHED" ||
      /quota/i.test(message)
    );
  }

  function persistFailure(stage, err) {
    var wrapped = new Error((err && err.message) || "IndexedDB persist failed.");
    wrapped.stage = isQuotaError(err) ? "quota" : stage;
    wrapped.causeName = (err && err.name) || "";
    return wrapped;
  }

  function logFieldPersistFailure(err) {
    try {
      console.warn("Field capture local persist failed", {
        stage: (err && err.stage) || "idb_put",
        name: (err && (err.causeName || err.name)) || "",
        message: String((err && err.message) || "").slice(0, 180),
      });
    } catch (ignored) {
      /* diagnostic only */
    }
  }

  function bytesFromBlob(source, stage) {
    if (!source || typeof source.arrayBuffer !== "function") {
      return Promise.reject(
        persistFailure(stage, new Error("Binary byte read is not available."))
      );
    }
    return source.arrayBuffer().then(
      function (buffer) {
        return new Uint8Array(buffer);
      },
      function (err) {
        throw persistFailure(stage, err);
      }
    );
  }

  function bytesFromImageFile(source) {
    return bytesFromBlob(source, "IMAGE_ARRAYBUFFER_READ");
  }

  function normalizeImageOriginals(originals) {
    var chain = Promise.resolve();
    originals.forEach(function (row) {
      chain = chain.then(function () {
        if ((row.kind !== "image" && row.kind !== "audio") || !row.blob) return;
        var stage = row.kind === "audio" ? "AUDIO_ARRAYBUFFER_READ" : "IMAGE_ARRAYBUFFER_READ";
        return bytesFromBlob(row.blob, stage).then(function (bytes) {
          row.bytes = bytes;
          delete row.blob;
        });
      });
    });
    return chain;
  }

  function fileBlobForUpload(original) {
    if (original.kind === "image" || original.kind === "audio") {
      var reconstructStage =
        original.kind === "audio" ? "AUDIO_BLOB_RECONSTRUCT" : "IMAGE_BLOB_RECONSTRUCT";
      if (!original.bytes) {
        throw persistFailure(
          reconstructStage,
          new Error("Pending " + original.kind + " bytes are missing.")
        );
      }
      try {
        return new Blob([original.bytes], { type: original.mime || "" });
      } catch (err) {
        throw persistFailure(reconstructStage, err);
      }
    }
    if (original.blob) return original.blob;
    throw persistFailure("MULTIPART_PREPARE", new Error("Pending binary original is missing."));
  }

  function putStore(storeName, value) {
    var putStage =
      storeName === "pending_originals" ? "INDEXEDDB_PENDING_ORIGINAL_PUT" : "idb_put";
    return openDb()
      .then(
        function (db) {
          var tx = db.transaction(storeName, "readwrite");
          tx.objectStore(storeName).put(value);
          return txDone(tx);
        },
        function (err) {
          throw persistFailure("idb_open", err);
        }
      )
      .catch(function (err) {
        if (err && err.stage) throw err;
        throw persistFailure(putStage, err);
      });
  }

  function deleteStore(storeName, key) {
    return openDb().then(function (db) {
      var tx = db.transaction(storeName, "readwrite");
      tx.objectStore(storeName).delete(key);
      return txDone(tx);
    });
  }

  function getAllStore(storeName) {
    return openDb().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(storeName, "readonly");
        var req = tx.objectStore(storeName).getAll();
        req.onsuccess = function () {
          resolve(req.result || []);
        };
        req.onerror = function () {
          reject(req.error);
        };
      });
    });
  }

  function wipePending() {
    return openDb().then(function (db) {
      var tx = db.transaction(["pending_captures", "pending_originals"], "readwrite");
      tx.objectStore("pending_captures").clear();
      tx.objectStore("pending_originals").clear();
      return txDone(tx);
    });
  }

  function newUuid() {
    if (window.crypto && typeof crypto.randomUUID === "function") {
      return crypto.randomUUID();
    }
    if (window.crypto && typeof crypto.getRandomValues === "function") {
      var bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      bytes[6] = (bytes[6] & 0x0f) | 0x40;
      bytes[8] = (bytes[8] & 0x3f) | 0x80;
      var hex = "";
      var i;
      for (i = 0; i < bytes.length; i += 1) {
        hex += (bytes[i] + 256).toString(16).slice(-2);
      }
      return (
        hex.slice(0, 8) +
        "-" +
        hex.slice(8, 12) +
        "-" +
        hex.slice(12, 16) +
        "-" +
        hex.slice(16, 20) +
        "-" +
        hex.slice(20, 32)
      );
    }
    throw new Error("This browser cannot create a capture identity.");
  }

  function jsonHeaders() {
    return {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken(),
    };
  }

  function postJson(url, body) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: jsonHeaders(),
      body: JSON.stringify(body),
    });
  }

  function postForm(url, form) {
    return fetch(url, {
      method: "POST",
      credentials: "same-origin",
      headers: { "X-CSRFToken": csrfToken() },
      body: form,
    });
  }

  function refreshCsrf() {
    return fetch(window.location.pathname, {
      method: "GET",
      credentials: "same-origin",
      headers: { Accept: "text/html" },
    }).then(function (response) {
      return response.text().then(function (html) {
        refreshCsrfFromHtml(html);
        return response;
      });
    });
  }

  function isCsrfFailure(response, payload) {
    if (response.status !== 400) return false;
    var err = (payload && payload.error) || "";
    return /csrf/i.test(err) || /token/i.test(err);
  }

  function parseJsonSafe(response) {
    return response.text().then(function (text) {
      if (!text) return {};
      try {
        return JSON.parse(text);
      } catch (err) {
        return { error: text.slice(0, 180) };
      }
    });
  }

  function requestOnce(send) {
    return send().then(function (response) {
      return parseJsonSafe(response).then(function (payload) {
        if (isCsrfFailure(response, payload)) {
          return refreshCsrf().then(function () {
            return send().then(function (retry) {
              return parseJsonSafe(retry).then(function (body) {
                return { response: retry, payload: body };
              });
            });
          });
        }
        return { response: response, payload: payload };
      });
    });
  }

  function bindLogout() {
    var form = document.getElementById("field-logout-form");
    if (!form) return;
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var proceed = function () {
        form.submit();
      };
      getAllStore("pending_captures")
        .then(function (captures) {
          if (captures.length && !window.confirm("Unsent captures will be removed from this phone. Log out?")) {
            return;
          }
          return wipePending().then(proceed);
        })
        .catch(proceed);
    });
  }

  function updateRetryPanel() {
    var panel = document.getElementById("field-retry-panel");
    var count = document.getElementById("field-retry-count");
    var link = document.getElementById("field-retry-link");
    if (!panel || !count) return Promise.resolve();
    return getAllStore("pending_captures")
      .then(function (captures) {
        var retry = captures.filter(function (row) {
          return row.state === "needs_retry" || row.state === "saving";
        });
        if (!retry.length) {
          panel.hidden = true;
          return;
        }
        panel.hidden = false;
        count.textContent =
          retry.length === 1 ? "1 capture needs retry." : retry.length + " captures need retry.";
        if (link) {
          var first = retry[0];
          link.href = "/field/projects/" + first.project_id + "/capture";
        }
      })
      .catch(function () {
        panel.hidden = true;
      });
  }

  function rememberProject(projectId) {
    try {
      sessionStorage.setItem(SESSION_PROJECT_KEY, String(projectId));
      localStorage.setItem(LAST_PROJECT_KEY, String(projectId));
    } catch (err) {
      /* hint only */
    }
  }

  function pendingForOtherProject(projectId) {
    return getAllStore("pending_captures").then(function (rows) {
      return rows.filter(function (row) {
        return String(row.project_id) !== String(projectId);
      });
    });
  }

  function pickAudioType() {
    if (!window.MediaRecorder || typeof MediaRecorder.isTypeSupported !== "function") {
      return "";
    }
    for (var i = 0; i < AUDIO_TYPES.length; i += 1) {
      if (MediaRecorder.isTypeSupported(AUDIO_TYPES[i])) return AUDIO_TYPES[i];
    }
    return "";
  }

  function enableVoice() {
    var record = document.getElementById("field-record");
    var note = document.getElementById("field-voice-note");
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia || !window.MediaRecorder) {
      if (record) record.disabled = true;
      if (note) note.textContent = "Voice capture is not available on this phone. Photo and text still work.";
      return;
    }
    if (record) {
      record.addEventListener("click", startRecord);
    }
    var stop = document.getElementById("field-stop");
    if (stop) stop.addEventListener("click", stopRecord);
    var discard = document.getElementById("field-discard-audio");
    if (discard) discard.addEventListener("click", discardAudio);
  }

  function startRecord() {
    var note = document.getElementById("field-voice-note");
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then(function (stream) {
        var type = pickAudioType();
        recorder = type ? new MediaRecorder(stream, { mimeType: type }) : new MediaRecorder(stream);
        recordedMime = recorder.mimeType || type || "audio/mp4";
        var chunks = [];
        recorder.ondataavailable = function (event) {
          if (event.data && event.data.size) chunks.push(event.data);
        };
        recorder.onstop = function () {
          stream.getTracks().forEach(function (track) {
            track.stop();
          });
          recordedBlob = new Blob(chunks, { type: recordedMime });
          var preview = document.getElementById("field-audio-preview");
          if (preview) {
            preview.src = URL.createObjectURL(recordedBlob);
            preview.hidden = false;
          }
          var discard = document.getElementById("field-discard-audio");
          if (discard) discard.hidden = false;
        };
        recorder.start();
        document.getElementById("field-record").hidden = true;
        document.getElementById("field-stop").hidden = false;
        if (note) note.textContent = "Recording…";
      })
      .catch(function () {
        document.getElementById("field-record").disabled = true;
        if (note) note.textContent = "Microphone permission was denied. Photo and text still work.";
      });
  }

  function stopRecord() {
    if (recorder && recorder.state !== "inactive") recorder.stop();
    document.getElementById("field-record").hidden = false;
    document.getElementById("field-stop").hidden = true;
    var note = document.getElementById("field-voice-note");
    if (note) note.textContent = "";
  }

  function discardAudio() {
    recordedBlob = null;
    var preview = document.getElementById("field-audio-preview");
    if (preview) {
      preview.removeAttribute("src");
      preview.hidden = true;
    }
    var discard = document.getElementById("field-discard-audio");
    if (discard) discard.hidden = true;
  }

  function addPhoto(file) {
    photos.push(file);
    renderPhotos();
  }

  function renderPhotos() {
    var list = document.getElementById("field-photo-list");
    if (!list) return;
    list.innerHTML = "";
    photos.forEach(function (file, index) {
      var item = document.createElement("li");
      var img = document.createElement("img");
      img.alt = file.name || "Photo " + (index + 1);
      img.src = URL.createObjectURL(file);
      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "field-btn field-btn-ghost";
      remove.textContent = "Remove photo";
      remove.addEventListener("click", function () {
        photos.splice(index, 1);
        renderPhotos();
      });
      item.appendChild(img);
      item.appendChild(remove);
      list.appendChild(item);
    });
  }

  function bindFiles() {
    var take = document.getElementById("field-take-photo");
    var choose = document.getElementById("field-choose-photo");
    if (take) {
      take.addEventListener("change", function () {
        if (take.files && take.files[0]) addPhoto(take.files[0]);
        take.value = "";
      });
    }
    if (choose) {
      choose.addEventListener("change", function () {
        Array.prototype.forEach.call(choose.files || [], addPhoto);
        choose.value = "";
      });
    }
  }

  function persistCapture(capture, originals) {
    return putStore("pending_captures", capture).then(function () {
      var chain = Promise.resolve();
      originals.forEach(function (row) {
        chain = chain.then(function () {
          return putStore("pending_originals", row);
        });
      });
      return chain;
    });
  }

  function markNeedsRetry(capture, originals) {
    capture.state = "needs_retry";
    var chain = putStore("pending_captures", capture);
    originals.forEach(function (row) {
      if (row.state !== "acked") {
        row.state = "needs_retry";
        chain = chain.then(function () {
          return putStore("pending_originals", row);
        });
      }
    });
    return chain;
  }

  function postEvent(projectId, capture) {
    var url = "/api/v1/projects/" + projectId + "/field-events";
    return requestOnce(function () {
      return postJson(url, { client_capture_uuid: capture.client_capture_uuid });
    }).then(function (result) {
      if (result.response.status === 401) {
        window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
        throw new Error("Sign in required.");
      }
      if (result.response.status !== 201 && result.response.status !== 200) {
        throw new Error(result.payload.error || "Event could not be saved.");
      }
      capture.server_event_id = result.payload.id;
      capture.state = "saving";
      return putStore("pending_captures", capture).then(function () {
        return result.payload;
      });
    });
  }

  function postOriginal(projectId, eventId, original) {
    var url =
      "/api/v1/projects/" + projectId + "/field-events/" + eventId + "/originals";
    return requestOnce(function () {
      if (original.kind === "text") {
        return postJson(url, {
          kind: "text",
          text: original.text_body,
          client_original_uuid: original.client_original_uuid,
        });
      }
      var form = new FormData();
      form.append("kind", original.kind);
      form.append("client_original_uuid", original.client_original_uuid);
      var fileBlob = fileBlobForUpload(original);
      form.append("file", fileBlob, original.filename || "capture");
      return postForm(url, form);
    }).then(function (result) {
      if (result.response.status === 401) {
        window.location.href = "/login?next=" + encodeURIComponent(window.location.pathname);
        throw new Error("Sign in required.");
      }
      if (result.response.status !== 201 && result.response.status !== 200) {
        throw new Error(result.payload.error || "Original could not be saved.");
      }
      original.state = "acked";
      return deleteStore("pending_originals", original.client_original_uuid);
    });
  }

  function finishCapture(capture, originals) {
    var pending = originals.filter(function (row) {
      return row.state !== "acked";
    });
    if (pending.length) {
      return markNeedsRetry(capture, pending).then(function () {
        setFeedback("NEEDS RETRY", "needs_retry");
        setStatus("NEEDS RETRY");
      });
    }
    return deleteStore("pending_captures", capture.client_capture_uuid).then(function () {
      setFeedback("SAVED", "saved");
      setStatus("SAVED");
    });
  }

  function uploadCapture(capture, originals) {
    setFeedback("SAVING", "saving");
    setStatus("SAVING");
    capture.state = "saving";
    return putStore("pending_captures", capture)
      .then(function () {
        return postEvent(capture.project_id, capture);
      })
      .then(function () {
        var chain = Promise.resolve();
        originals.forEach(function (row) {
          chain = chain.then(function () {
            if (row.state === "acked") return;
            row.state = "saving";
            return putStore("pending_originals", row).then(function () {
              return postOriginal(capture.project_id, capture.server_event_id, row);
            });
          });
        });
        return chain;
      })
      .then(function () {
        return finishCapture(capture, originals);
      })
      .catch(function (err) {
        return markNeedsRetry(capture, originals).then(function () {
          setFeedback((err && err.message) || "NEEDS RETRY", "needs_retry");
          setStatus("NEEDS RETRY");
        });
      });
  }

  function retryExisting(projectId) {
    return getAllStore("pending_captures").then(function (captures) {
      var mine = captures.filter(function (row) {
        return String(row.project_id) === String(projectId);
      });
      if (!mine.length) return;
      return getAllStore("pending_originals").then(function (originals) {
        var chain = Promise.resolve();
        mine.forEach(function (capture) {
          chain = chain.then(function () {
            var rows = originals.filter(function (row) {
              return row.client_capture_uuid === capture.client_capture_uuid;
            });
            return uploadCapture(capture, rows);
          });
        });
        return chain;
      });
    });
  }

  function saveNew(projectId) {
    var text = (document.getElementById("field-text").value || "").trim();
    if (!text && !recordedBlob && !photos.length) {
      setFeedback("Add a photo, recording, or short text before saving.");
      return;
    }
    if (!persistenceReady) {
      setFeedback("Cannot safely keep this capture on this phone. Try photo or text later, or free storage.");
      return;
    }
    var captureUuid;
    var originals = [];
    try {
      captureUuid = newUuid();
      if (text) {
        originals.push({
          client_original_uuid: newUuid(),
          client_capture_uuid: captureUuid,
          kind: "text",
          text_body: text,
          filename: "note.txt",
          mime: "text/plain",
          state: "pending",
        });
      }
      if (recordedBlob) {
        originals.push({
          client_original_uuid: newUuid(),
          client_capture_uuid: captureUuid,
          kind: "audio",
          blob: recordedBlob,
          filename: recordedMime.indexOf("webm") !== -1 ? "note.webm" : "note.m4a",
          mime: recordedMime,
          state: "pending",
        });
      }
      photos.forEach(function (file, index) {
        originals.push({
          client_original_uuid: newUuid(),
          client_capture_uuid: captureUuid,
          kind: "image",
          blob: file,
          filename: file.name || "photo-" + (index + 1) + ".jpg",
          mime: file.type || "image/jpeg",
          state: "pending",
        });
      });
    } catch (err) {
      setFeedback("Unable to prepare this capture for saving. Please retry.");
      return;
    }
    var capture = {
      client_capture_uuid: captureUuid,
      project_id: projectId,
      capture_started_at: new Date().toISOString(),
      server_event_id: null,
      state: "draft_local",
      text: text || null,
    };
    normalizeImageOriginals(originals)
      .then(function () {
        return persistCapture(capture, originals);
      })
      .then(function () {
        return uploadCapture(capture, originals);
      })
      .then(function () {
        if (document.getElementById("field-feedback").getAttribute("data-state") === "saved") {
          document.getElementById("field-text").value = "";
          discardAudio();
          photos = [];
          renderPhotos();
        }
      })
      .catch(function (err) {
        logFieldPersistFailure(err);
        setFeedback("Cannot safely keep this capture on this phone. Try photo or text later, or free storage.");
        setStatus("");
      });
  }

  function initCapture() {
    var root = document.querySelector(".field-capture");
    if (!root) return;
    var projectId = root.getAttribute("data-project-id");
    rememberProject(projectId);
    pendingForOtherProject(projectId).then(function (other) {
      if (!other.length) return;
      var first = other[0];
      if (
        window.confirm(
          "A pending capture is still bound to another Project. Open that Project to finish retry, or discard it?"
        )
      ) {
        window.location.href = "/field/projects/" + first.project_id + "/capture";
        return;
      }
      if (window.confirm("Discard the pending capture for the other Project?")) {
        return getAllStore("pending_originals").then(function (originals) {
          var chain = Promise.resolve();
          other.forEach(function (capture) {
            chain = chain.then(function () {
              return deleteStore("pending_captures", capture.client_capture_uuid);
            });
            originals.forEach(function (row) {
              if (row.client_capture_uuid === capture.client_capture_uuid) {
                chain = chain.then(function () {
                  return deleteStore("pending_originals", row.client_original_uuid);
                });
              }
            });
          });
          return chain;
        });
      }
    });
    enableVoice();
    bindFiles();
    var save = document.getElementById("field-save");
    if (save) {
      save.addEventListener("click", function () {
        saveNew(projectId);
      });
    }
    retryExisting(projectId);
  }

  function init() {
    bindLogout();
    openDb()
      .then(function () {
        persistenceReady = true;
        setStatus("");
        updateRetryPanel();
        initCapture();
      })
      .catch(function (err) {
        persistenceReady = false;
        logFieldPersistFailure(persistFailure("idb_open", err));
        setFeedback("Cannot safely keep this capture on this phone. Try photo or text later, or free storage.");
        var save = document.getElementById("field-save");
        if (save) save.disabled = true;
        bindLogout();
        enableVoice();
        bindFiles();
      });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
