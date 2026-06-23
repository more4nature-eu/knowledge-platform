import ThemeToggle from "./components/theme-toggle";
import HeaderSearchPanel from "./components/header-search-panel";
import MobileMenu from "./components/mobile-menu";
import SkipLink from './components/skip-link';
import Carousel from './components/carousel';

import 'tom-select/dist/css/tom-select.css';
import '../css/main.css';

import TomSelect from 'tom-select';

let lastScrollPosition = 0;

function initComponent(ComponentClass) {
    const items = document.querySelectorAll(ComponentClass.selector());
    items.forEach((item) => new ComponentClass(item));
}

function initTagSelects() {
  try {
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
  } catch (error) {
    console.log("No tags");
  }
}

// Function to highlight text based on query param
// Based on material for mkdocs template code
function highlightTextFromFragment() {
  const params = new URLSearchParams(window.location.search);
  const searchText = params.get('query');
  if (!searchText) return;

  const contentElement = document.getElementById('main-content');
  if (!contentElement) return;

  highlightInTextNodes(contentElement, searchText);
  propagateQueryToLinks(searchText, "article-card");
}

// Recursively walk text nodes and highlights matches
function highlightInTextNodes(root, searchText) {
  const regex = new RegExp(searchText, "gi");

  const walker = document.createTreeWalker(
    root,
    NodeFilter.SHOW_TEXT,
    {
      acceptNode(node) {
        // Skip empty or whitespace-only nodes
        if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;

        // Skip text inside script/style tags
        const parent = node.parentNode;
        if (["SCRIPT", "STYLE", "MARK"].includes(parent.nodeName)) {
          return NodeFilter.FILTER_REJECT;
        }

        return NodeFilter.FILTER_ACCEPT;
      }
    }
  );

    const nodesToProcess = [];

    while (walker.nextNode()) {
        nodesToProcess.push(walker.currentNode);
    }

    nodesToProcess.forEach(node => {
        const text = node.nodeValue;

        if (!regex.test(text)) return;

        const span = document.createElement("span");
        span.innerHTML = text.replace(regex, "<mark>$&</mark>");

        node.parentNode.replaceChild(span, node);
    });
}

// Adds query param to links of a given class
function propagateQueryToLinks(searchText, className) {
    const links = document.querySelectorAll(`a.${className}`);

    links.forEach(link => {
        const url = new URL(link.href, window.location.origin);
        url.searchParams.set("query", searchText);
        link.href = url.toString();
    });
}

document.addEventListener('DOMContentLoaded', () => {
  initComponent(ThemeToggle);
  initComponent(ThemeToggle);
  initComponent(SkipLink);
  initComponent(HeaderSearchPanel);
  initComponent(MobileMenu);
  initComponent(Carousel);
  highlightTextFromFragment();
  initTagSelects();
});

window.addEventListener('scroll', function() {
  const currentScrollPosition = window.pageYOffset;

  if (currentScrollPosition > lastScrollPosition) {
    // Scrolling down
    document.querySelector('header').style.transform = 'translateY(-100%)'; // Hide the header
  } else if (currentScrollPosition < (lastScrollPosition - 5) ) {
    // Scrolling up
    document.querySelector('header').style.transform = 'translateY(0)'; // Show the header
  }

  if (currentScrollPosition < 50) {
    document.querySelector('header').style.transform = 'translateY(0)'; // Show the header
  }

  lastScrollPosition = currentScrollPosition <= 0 ? 0 : currentScrollPosition; ; // Update last scroll position
});

