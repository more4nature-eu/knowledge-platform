class Carousel {
  static selector() {
    return '.carousel';
  }

  constructor(node) {
    this.container = node;
    this.left = this.container.querySelector(".carousel-left");
    this.right = this.container.querySelector(".carousel-right");
    this.imageContainer = this.container.querySelector(".carousel-image-container");
    this.captionContainer = this.container.querySelector(".carousel-caption-container");
    this.left.addEventListener("click", this.previous.bind(this));
    this.right.addEventListener("click", this.next.bind(this));
  }

  showElement(element, animated=false) {
    element.classList.remove("hidden");
    if(animated) {
      element.classList.add("opacity-0");
      requestAnimationFrame(() => {
        element.classList.remove("opacity-0");
      });
    }
  }

  hideElement(element, animated=false) {
    if(animated) {
      element.classList.add("opacity-0");
      element.addEventListener("transitionend", () => {
        element.classList.add("hidden");
        element.classList.remove("opacity-0");
      });
    } else {
      element.classList.add("hidden");
    }
  }

  previous(event) {
    event.preventDefault();
    let previousActiveImage = this.imageContainer.querySelector(":scope > :not(.hidden)")
    let previousActiveCaption = this.captionContainer.querySelector(":scope > :not(.hidden)")
    let activeImage = previousActiveImage.previousElementSibling || this.imageContainer.lastElementChild;
    let activeCaption = previousActiveCaption.previousElementSibling || this.captionContainer.lastElementChild;
    this.hideElement(previousActiveImage, true);
    this.hideElement(previousActiveCaption);
    this.showElement(activeImage, true);
    this.showElement(activeCaption)
  }

  next(event) {
    event.preventDefault();
    let previousActiveImage = this.imageContainer.querySelector(":scope > :not(.hidden)")
    let previousActiveCaption = this.captionContainer.querySelector(":scope > :not(.hidden)")
    let activeImage = previousActiveImage.nextElementSibling || this.imageContainer.firstElementChild;
    let activeCaption = previousActiveCaption.nextElementSibling || this.captionContainer.firstElementChild;
    this.hideElement(previousActiveImage, true);
    this.hideElement(previousActiveCaption);
    this.showElement(activeImage, true);
    this.showElement(activeCaption)
  }

}

export default Carousel;
