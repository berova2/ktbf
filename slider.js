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

// ── Slider ─────────────────────────────────────────────────────────────────
const slider = document.querySelector("[data-slider]");

if (slider) {
  const slidesContainer = slider.querySelector("[data-slides]");
  const slides = Array.from(slidesContainer.querySelectorAll("[data-slide]"));
  const prevButton = slider.querySelector("[data-prev]");
  const nextButton = slider.querySelector("[data-next]");
  const dotsContainer = slider.querySelector("[data-dots]");

  if (slides.length <= 1) {
    slidesContainer.style.transform = "translateX(0)";
  } else if (prevButton && nextButton && dotsContainer) {
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
}