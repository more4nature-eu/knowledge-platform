import ThemeToggle from "./components/theme-toggle";
import HeaderSearchPanel from "./components/header-search-panel";
import MobileMenu from "./components/mobile-menu";
import SkipLink from './components/skip-link';

import '../css/main.css';


function initComponent(ComponentClass) {
    const items = document.querySelectorAll(ComponentClass.selector());
    items.forEach((item) => new ComponentClass(item));
}

document.addEventListener('DOMContentLoaded', () => {
    initComponent(ThemeToggle);
    initComponent(ThemeToggle);
    initComponent(SkipLink);
    initComponent(HeaderSearchPanel);
    initComponent(MobileMenu);
});

let lastScrollPosition = 0;

window.addEventListener('scroll', function() {
  const currentScrollPosition = window.pageYOffset;

  if (currentScrollPosition > lastScrollPosition) {
    // Scrolling down
    document.querySelector('header').style.transform = 'translateY(-100%)'; // Hide the header
  } else {
    // Scrolling up
    document.querySelector('header').style.transform = 'translateY(0)'; // Show the header
  }

  lastScrollPosition = currentScrollPosition; // Update last scroll position
});