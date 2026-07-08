// ── Basın Bildirileri – otomatik listele ───────────────────────────────────
(function () {
  var list = document.getElementById("press-list");
  var status = document.getElementById("press-status");
  if (!list) return;

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;");
  }

  function formatDate(value) {
    if (!value) return "";
    var d = new Date(value);
    if (isNaN(d.getTime())) return "";
    return d.toLocaleDateString("tr-TR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  fetch("BasinBildirileri/manifest.json")
    .then(function (r) {
      if (!r.ok) throw new Error("manifest okunamadı");
      return r.json();
    })
    .then(function (items) {
      if (status) {
        status.textContent = "";
        status.classList.add("is-hidden");
      }
      if (!Array.isArray(items) || items.length === 0) {
        list.innerHTML = "<li class='loading'>Henüz basın bildirisi eklenmemiş.</li>";
        return;
      }
      list.innerHTML = items
        .map(function (item) {
          var safeName = escapeHtml(item.name || item.file);
          var safeFile = String(item.file).replace(
            /[^a-zA-Z0-9_.\-\u00C0-\u024F]/g,
            function (c) {
              return encodeURIComponent(c);
            }
          );
          var dateText = formatDate(item.date);
          var dateHtml = dateText
            ? '<span class="press-date">' + dateText + "</span>"
            : "";

          return (
            '<li>' +
            dateHtml +
            '<a href="BasinBildirileri/' +
            safeFile +
            '" download>' +
            safeName +
            "</a>" +
            "</li>"
          );
        })
        .join("");
    })
    .catch(function () {
      list.innerHTML = "<li class='loading'>Basın bildirileri yüklenemedi.</li>";
      if (status) {
        status.textContent = "Basın bildirisi verisi yüklenemedi.";
        status.classList.remove("is-hidden");
      }
    });
})();
