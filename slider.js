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