// ── Yasal Belgeler – otomatik listele ──────────────────────────────────────
(function () {
  const list = document.getElementById("legal-docs-list");
  if (!list) return;

  fetch("LegalDocuments/manifest.json")
    .then(function (r) {
      if (!r.ok) throw new Error("manifest okunamadı");
      return r.json();
    })
    .then(function (docs) {
      if (!Array.isArray(docs) || docs.length === 0) {
        list.innerHTML = "<li>Henüz belge eklenmemiş.</li>";
        return;
      }
      list.innerHTML = docs
        .map(function (doc) {
          var safeName = String(doc.name || doc.file).replace(/</g, "&lt;");
          var safeFile = String(doc.file).replace(/[^a-zA-Z0-9_.\-\u00C0-\u024F]/g, function (c) {
            return encodeURIComponent(c);
          });
          return (
            '<li><a href="LegalDocuments/' +
            safeFile +
            '" download>' +
            safeName +
            "</a></li>"
          );
        })
        .join("");
    })
    .catch(function () {
      list.innerHTML = "<li>Belgeler yüklenemedi.</li>";
    });
})();

// ── Etkinlik Galerisi – manifestten yükle ──────────────────────────────────
function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;");
}

function encodeFileName(value) {
  return String(value).replace(/[^a-zA-Z0-9_.\-\u00C0-\u024F]/g, function (char) {
    return encodeURIComponent(char);
  });
}

function setGalleryStatus(text, isError) {
  var status = document.getElementById("gallery-status");
  if (!status) return;

  if (!text) {
    status.classList.add("is-hidden");
    status.textContent = "";
    return;
  }

  status.classList.remove("is-hidden");
  status.style.color = isError ? "#b42318" : "";
  status.textContent = text;
}

function renderGallerySlides(items) {
  var slidesContainer = document.querySelector("[data-slides]");
  if (!slidesContainer || !Array.isArray(items) || items.length === 0) return false;

  slidesContainer.innerHTML = items
    .map(function (item, index) {
      var safeFile = encodeFileName(item.file || "");
      var safeAlt = escapeHtml(item.alt || "KTBF etkinlik gorseli");
      var activeClass = index === 0 ? " is-active" : "";

      if (!safeFile) return "";

      return (
        '<figure class="slide' +
        activeClass +
        '" data-slide><img src="EtkinlikGalerisi/' +
        safeFile +
        '" alt="' +
        safeAlt +
        '" loading="lazy" /></figure>'
      );
    })
    .join("");

  return slidesContainer.querySelectorAll("[data-slide]").length > 0;
}

// ── Slider ─────────────────────────────────────────────────────────────────
function initSlider() {
  const slider = document.querySelector("[data-slider]");
  if (!slider) return;

  const slidesContainer = slider.querySelector("[data-slides]");
  const slides = Array.from(slidesContainer.querySelectorAll("[data-slide]"));
  const prevButton = slider.querySelector("[data-prev]");
  const nextButton = slider.querySelector("[data-next]");
  const dotsContainer = slider.querySelector("[data-dots]");

  if (!dotsContainer) return;
  dotsContainer.innerHTML = "";

  if (slides.length <= 1) {
    slidesContainer.style.transform = "translateX(0)";
    if (prevButton) prevButton.style.display = "none";
    if (nextButton) nextButton.style.display = "none";
    return;
  }

  if (!prevButton || !nextButton) return;

  if (prevButton) prevButton.style.display = "";
  if (nextButton) nextButton.style.display = "";

  let currentIndex = 0;
  const autoPlayDelay = 4000;
  let autoPlayTimer;

  const createDots = () => {
    slides.forEach((_, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("aria-label", `${index + 1}. gorsele git`);
      dot.addEventListener("click", () => {
        goToSlide(index);
        restartAutoPlay();
      });
      dotsContainer.appendChild(dot);
    });
  };

  const updateDots = () => {
    const dots = Array.from(dotsContainer.querySelectorAll("button"));
    dots.forEach((dot, index) => {
      dot.classList.toggle("is-active", index === currentIndex);
    });
  };

  const goToSlide = (index) => {
    currentIndex = (index + slides.length) % slides.length;
    slidesContainer.style.transform = `translateX(-${currentIndex * 100}%)`;
    updateDots();
  };

  const nextSlide = () => {
    goToSlide(currentIndex + 1);
  };

  const prevSlide = () => {
    goToSlide(currentIndex - 1);
  };

  const startAutoPlay = () => {
    clearInterval(autoPlayTimer);
    autoPlayTimer = setInterval(nextSlide, autoPlayDelay);
  };

  const restartAutoPlay = () => {
    clearInterval(autoPlayTimer);
    startAutoPlay();
  };

  createDots();
  goToSlide(0);
  startAutoPlay();

  nextButton.addEventListener("click", () => {
    nextSlide();
    restartAutoPlay();
  });

  prevButton.addEventListener("click", () => {
    prevSlide();
    restartAutoPlay();
  });

  slider.addEventListener("mouseenter", () => clearInterval(autoPlayTimer));
  slider.addEventListener("mouseleave", startAutoPlay);
}

(function () {
  fetch("EtkinlikGalerisi/manifest.json")
    .then(function (r) {
      if (!r.ok) throw new Error("galeri manifest okunamadi");
      return r.json();
    })
    .then(function (items) {
      if (!renderGallerySlides(items)) {
        setGalleryStatus("Henüz galeri görseli eklenmemiş.", false);
        return;
      }
      setGalleryStatus("", false);
    })
    .catch(function () {
      setGalleryStatus("Galeri görselleri yüklenemedi, varsayılan görsel gösteriliyor.", true);
    })
    .finally(function () {
      initSlider();
    });
})();