// Small browser-side features. The app works without them; they add:
//  - dark mode toggle (remembered in this browser)
//  - voice input (Web Speech API, built into Chrome, Edge and Safari)
//  - read-aloud of answers (speechSynthesis, built into all modern browsers)
(function () {
  "use strict";

  // ---------- dark mode ----------
  function currentTheme() {
    var set = document.documentElement.getAttribute("data-theme");
    if (set) return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  document.addEventListener("click", function (e) {
    if (!e.target.closest("#theme-toggle")) return;
    var next = currentTheme() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("ssa-theme", next); } catch (err) { /* ignore */ }
  });

  // ---------- voice input ----------
  var Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  function setupMic() {
    var mic = document.getElementById("mic");
    var input = document.getElementById("q");
    if (!mic || !input || mic.dataset.ready) return;
    mic.dataset.ready = "1";
    if (!Recognition) return;           // unsupported browser: keep the button hidden
    mic.hidden = false;
    var status = document.getElementById("voice-status");
    var rec = null;
    mic.addEventListener("click", function () {
      if (rec) { rec.stop(); return; }
      rec = new Recognition();
      rec.lang = mic.dataset.lang || "en-AU";
      rec.interimResults = true;
      rec.maxAlternatives = 1;
      mic.classList.add("listening");
      if (status) status.textContent = mic.dataset.listening || "Listening…";
      rec.onresult = function (event) {
        var text = "";
        for (var i = 0; i < event.results.length; i++) text += event.results[i][0].transcript;
        input.value = text;
        if (event.results[event.results.length - 1].isFinal) input.form.requestSubmit();
      };
      rec.onerror = function (event) { if (status) status.textContent = event.error === "not-allowed" ? "Microphone permission was denied." : ""; };
      rec.onend = function () {
        mic.classList.remove("listening");
        if (status && status.textContent === mic.dataset.listening) status.textContent = "";
        rec = null;
      };
      rec.start();
    });
  }

  // ---------- read aloud ----------
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-tts]");
    if (!btn || !("speechSynthesis" in window)) return;
    var section = btn.closest(".answer");
    var body = section && section.querySelector("[data-speak]");
    if (!body) return;
    if (window.speechSynthesis.speaking) { window.speechSynthesis.cancel(); return; }
    var clone = body.cloneNode(true);
    clone.querySelectorAll("svg, figure, .btn, table").forEach(function (n) { n.remove(); });
    var u = new SpeechSynthesisUtterance(clone.innerText.replace(/\s+/g, " ").trim());
    u.lang = section.getAttribute("lang") === "vi" ? "vi-VN" : "en-AU";
    window.speechSynthesis.speak(u);
  });

  // ---------- after each HTMX answer ----------
  document.addEventListener("htmx:afterSwap", function (e) {
    if (e.detail.target && e.detail.target.id === "answer") {
      var body = document.getElementById("answer-body");
      if (body) body.focus({ preventScroll: true });
      if (body) body.scrollIntoView({ behavior: "smooth", block: "start" });
      if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    }
  });
  document.addEventListener("htmx:load", setupMic);
  document.addEventListener("DOMContentLoaded", setupMic);
  if (!("speechSynthesis" in window)) {
    document.documentElement.classList.add("no-tts");
  }
})();
