import ThemeToggle from "./components/theme-toggle";
import HeaderSearchPanel from "./components/header-search-panel";
import MobileMenu from "./components/mobile-menu";
import SkipLink from './components/skip-link';

import 'tom-select/dist/css/tom-select.css';
import '../css/main.css';

import TomSelect from 'tom-select';

function initComponent(ComponentClass) {
    const items = document.querySelectorAll(ComponentClass.selector());
    items.forEach((item) => new ComponentClass(item));
}

function initTagSelects() {
    const select = new TomSelect('#tags', {
        plugins: {
            remove_button: {
                title: 'Remove'
            }
        },

        create: false,
        maxOptions: 1000,
        persist: false,
        placeholder: 'Search tags...',
        closeAfterSelect: true,
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initComponent(ThemeToggle);
    initComponent(ThemeToggle);
    initComponent(SkipLink);
    initComponent(HeaderSearchPanel);
    initComponent(MobileMenu);

    initTagSelects();
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
