(function () {
  "use strict";

  function copyText(text, button) {
    var original = button.textContent;
    var finish = function (label) {
      button.textContent = label;
      window.setTimeout(function () {
        button.textContent = original;
      }, 2400);
    };

    var fallbackCopy = function () {
      var field = document.createElement("textarea");
      field.value = text;
      field.setAttribute("readonly", "");
      field.style.position = "fixed";
      field.style.opacity = "0";
      document.body.appendChild(field);
      field.select();
      try {
        finish(document.execCommand("copy") ? "Copied" : "Copy failed");
      } catch (error) {
        finish("Copy failed");
      }
      document.body.removeChild(field);
    };

    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(function () {
        finish("Copied");
      }).catch(function () {
        fallbackCopy();
      });
      return;
    }

    fallbackCopy();
  }

  function initialiseCopyButtons() {
    document.querySelectorAll("[data-copy]").forEach(function (button) {
      button.addEventListener("click", function () {
        var target = document.querySelector(button.getAttribute("data-copy"));
        if (target) copyText(target.textContent.trim(), button);
      });
    });
  }

  function buildCommand(builder) {
    var page = builder.closest("[data-dataset-page]");
    if (!page) return;
    var repository = page.getAttribute("data-repository");
    var localDir = page.getAttribute("data-local-dir");
    var patterns = [];

    builder.querySelectorAll("input[type='checkbox']:checked").forEach(function (input) {
      (input.getAttribute("data-patterns") || "").split("||").forEach(function (pattern) {
        if (pattern && patterns.indexOf(pattern) === -1) patterns.push(pattern);
      });
    });

    var lines = [
      "hf download " + repository + " \\",
      "  --type dataset \\",
      "  --local-dir ./" + localDir + " \\"
    ];
    patterns.forEach(function (pattern) {
      lines.push("  --include \"" + pattern + "\" \\");
    });
    lines.push("  --dry-run");

    var output = builder.querySelector("#selective-command code");
    if (output) output.textContent = lines.join("\n");
  }

  function initialiseBuilders() {
    document.querySelectorAll("[data-download-builder]").forEach(function (builder) {
      builder.querySelectorAll("input[type='checkbox']").forEach(function (input) {
        input.addEventListener("change", function () {
          buildCommand(builder);
        });
      });
      buildCommand(builder);
    });
  }

  function initialiseFilters() {
    var toolbar = document.querySelector("[data-catalog-filter]");
    if (!toolbar) return;
    var cards = Array.prototype.slice.call(document.querySelectorAll("[data-catalog-item]"));
    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-catalog-row]"));
    var count = document.querySelector("[data-catalog-count]");

    toolbar.querySelectorAll("[data-filter]").forEach(function (button) {
      button.addEventListener("click", function () {
        var filter = button.getAttribute("data-filter");
        toolbar.querySelectorAll("[data-filter]").forEach(function (candidate) {
          var active = candidate === button;
          candidate.classList.toggle("is-active", active);
          candidate.setAttribute("aria-pressed", active ? "true" : "false");
        });

        var shown = 0;
        cards.forEach(function (card) {
          var visible = filter === "all" || card.getAttribute("data-domain") === filter;
          card.hidden = !visible;
          if (visible) shown += 1;
        });
        rows.forEach(function (row) {
          row.hidden = !(filter === "all" || row.getAttribute("data-domain") === filter);
        });
        if (count) count.textContent = String(shown);
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initialiseCopyButtons();
    initialiseBuilders();
    initialiseFilters();
  });
})();
