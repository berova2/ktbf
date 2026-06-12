(function () {
  var list = document.getElementById("announcements-list");
  var status = document.getElementById("announcements-status");

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;");
  }

  function formatDate(value) {
    if (!value) return "Tarih belirtilmedi";
    var d = new Date(value);
    if (isNaN(d.getTime())) return escapeHtml(value);
    return d.toLocaleDateString("tr-TR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  }

  function render(items) {
    if (!Array.isArray(items) || items.length === 0) {
      list.innerHTML = "<p>Henüz duyuru paylaşılmadı.</p>";
      status.textContent = "";
      status.classList.add("is-hidden");
      return;
    }

    list.innerHTML = items
      .map(function (item) {
        var title = escapeHtml(item.title || "Duyuru");
        var dateText = formatDate(item.date);
        var text = escapeHtml(item.content || "");
        var link = String(item.link || "").trim();
        var linkHtml = link
          ? '<a class="btn secondary-btn" href="' +
            encodeURI(link) +
            '" target="_blank" rel="noopener noreferrer">WhatsApp gönderisini aç</a>'
          : "";

        return (
          '<article class="announcement-card">' +
          '<p class="announcement-date">' +
          dateText +
          "</p>" +
          "<h3>" +
          title +
          "</h3>" +
          "<p>" +
          text +
          "</p>" +
          linkHtml +
          "</article>"
        );
      })
      .join("");

    status.textContent = "";
    status.classList.add("is-hidden");
  }

  if (!list || !status) return;

  fetch("Duyurular/manifest.json")
    .then(function (r) {
      if (!r.ok) throw new Error("manifest okunamadı");
      return r.json();
    })
    .then(render)
    .catch(function () {
      list.innerHTML = "<p>Duyurular yüklenemedi.</p>";
      status.textContent = "Duyuru verisi yüklenemedi.";
      status.classList.remove("is-hidden");
    });
})();
