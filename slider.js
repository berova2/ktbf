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
  let slides = Array.from(slidesContainer.querySelectorAll("[data-slide]"));
  const prevButton = slider.querySelector("[data-prev]");
  const nextButton = slider.querySelector("[data-next]");
  const dotsContainer = slider.querySelector("[data-dots]");
  const uploadInput = document.getElementById("gallery-upload-input");
  const uploadButton = document.getElementById("gallery-upload-button");
  const uploadStatus = document.getElementById("gallery-upload-status");

  if (slidesContainer) {
    let currentIndex = 0;
    const autoPlayDelay = 4000;
    let autoPlayTimer;

    const setUploadStatus = (message, hasError) => {
      if (!uploadStatus) return;
      uploadStatus.textContent = message || "";
      uploadStatus.classList.toggle("is-error", Boolean(hasError));
    };

    const updateControls = () => {
      const hasMultipleSlides = slides.length > 1;
      if (prevButton) prevButton.hidden = !hasMultipleSlides;
      if (nextButton) nextButton.hidden = !hasMultipleSlides;
      if (dotsContainer) dotsContainer.hidden = !hasMultipleSlides;
    };

    const createDots = () => {
      if (!dotsContainer) return;
      dotsContainer.innerHTML = "";
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
      if (!dotsContainer) return;
      const dots = Array.from(dotsContainer.querySelectorAll("button"));
      dots.forEach((dot, index) => {
        dot.classList.toggle("is-active", index === currentIndex);
      });
    };

    const goToSlide = (index) => {
      if (!slides.length) return;
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
      if (slides.length > 1) {
        autoPlayTimer = setInterval(nextSlide, autoPlayDelay);
      }
    };

    const restartAutoPlay = () => {
      clearInterval(autoPlayTimer);
      startAutoPlay();
    };

    const addSlideFromFile = (result, fileName) => {
      const slide = document.createElement("figure");
      slide.className = "slide";
      slide.setAttribute("data-slide", "");

      const image = document.createElement("img");
      image.src = result;
      image.alt = fileName ? `${fileName} galerisi` : "Yüklenen galeri fotoğrafı";

      slide.appendChild(image);
      slidesContainer.appendChild(slide);

      slides = Array.from(slidesContainer.querySelectorAll("[data-slide]"));
      createDots();
      updateControls();
      goToSlide(slides.length - 1);
      restartAutoPlay();
    };

    const handleUpload = () => {
      if (!uploadInput || !uploadInput.files || uploadInput.files.length === 0) {
        setUploadStatus("Lütfen galeriden en az bir fotoğraf seçin.", true);
        return;
      }

      const imageFiles = Array.from(uploadInput.files).filter((file) => file.type.startsWith("image/"));
      if (!imageFiles.length) {
        setUploadStatus("Sadece görsel dosyaları yükleyebilirsiniz.", true);
        return;
      }

      let loadedCount = 0;
      imageFiles.forEach((file) => {
        const reader = new FileReader();
        reader.onload = () => {
          addSlideFromFile(reader.result, file.name);
          loadedCount += 1;
          if (loadedCount === imageFiles.length) {
            setUploadStatus(`${loadedCount} fotoğraf galeriye eklendi.`);
            uploadInput.value = "";
          }
        };
        reader.onerror = () => {
          setUploadStatus("Fotoğraf yüklenirken bir hata oluştu.", true);
        };
        reader.readAsDataURL(file);
      });
    };

    createDots();
    updateControls();
    goToSlide(0);
    startAutoPlay();

    if (nextButton) {
      nextButton.addEventListener("click", () => {
        nextSlide();
        restartAutoPlay();
      });
    }

    if (prevButton) {
      prevButton.addEventListener("click", () => {
        prevSlide();
        restartAutoPlay();
      });
    }

    if (uploadButton) {
      uploadButton.addEventListener("click", handleUpload);
    }

    if (uploadInput) {
      uploadInput.addEventListener("change", () => setUploadStatus(""));
    }

    slider.addEventListener("mouseenter", () => clearInterval(autoPlayTimer));
    slider.addEventListener("mouseleave", startAutoPlay);
  }
}
