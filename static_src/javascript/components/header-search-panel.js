import { hideDropdownElement, showDropdownElement } from './utils';

class HeaderSearch {
    static selector() {
        return '[data-toggle-search-panel]';
    }

    constructor(node) {
        this.searchToggleButton = node;

        this.searchDropdown = document.querySelector(
            '[data-search-panel]'
        );

        this.searchDropdownContent = document.querySelector(
            '[data-search-content]',
        );

        this.searchInput = this.searchDropdown.querySelector(
            '[data-search-input]',
        );

        this.closeSearchButton = document.querySelector(
            '[data-search-close-button]',
        );

        this.searchControls = document.querySelector(
            ".search-controls"
        );

        this.bindEvents();
    }

    openSearch() {
        showDropdownElement(this.searchDropdown);
        this.searchControls.classList.add("search-open");

        // Make sure that the page is not scrollable.
        document.body.style.overflowY = 'hidden';

        // Focus on the input.
        this.searchInput.focus();
    }

    closeSearch() {
        hideDropdownElement(this.searchDropdown);
        this.searchControls.classList.remove("search-open");

        // Set the page to be scrollable.
        document.body.style.overflowY = 'visible';
    }

    bindEvents() {
        this.searchToggleButton.addEventListener('click', (e) => {
            e.preventDefault();

            if (this.searchDropdown.classList.contains('invisible')) {
                this.openSearch();
            } else {
                this.closeSearch();
            }
        });

        this.searchDropdown.addEventListener('click', (e) => {
            // Close the dropdown if clicking anywhere else on the page
            if (!this.searchDropdownContent.contains(e.target)) {
                this.closeSearch();
            }
        });

        this.closeSearchButton.addEventListener('click', (e) => {
            this.closeSearch();
        });
    }
}

export default HeaderSearch;
