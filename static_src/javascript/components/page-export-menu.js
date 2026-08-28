class PageExportMenu {
    static selector() {
        return '[data-page-export-menu]';
    }

    constructor(node) {
        this.toggleButton = node;
        this.menu = node.parentElement.querySelector('[data-page-export-menu-content]');
        this.copyButton = this.menu.querySelector('[data-page-export-copy]');
        this.printButton = this.menu.querySelector('[data-page-export-print]');

        this.bindEvents();
    }

    isOpen() {
        return !this.menu.classList.contains('invisible');
    }

    openMenu() {
        this.menu.classList.remove('invisible', 'opacity-0', '-translate-y-2');
        this.menu.classList.add('opacity-100', 'translate-y-0');
        this.toggleButton.setAttribute('aria-expanded', 'true');
    }

    closeMenu() {
        this.menu.classList.add('invisible', 'opacity-0', '-translate-y-2');
        this.menu.classList.remove('opacity-100', 'translate-y-0');
        this.toggleButton.setAttribute('aria-expanded', 'false');
    }

    toggleMenu() {
        if (this.isOpen()) {
            this.closeMenu();
        } else {
            this.openMenu();
        }
    }

    async copyForLLMs() {
        const button = this.copyButton;
        const defaultLabel = button.dataset.defaultLabel || button.textContent;

        try {
            const response = await fetch(button.dataset.exportUrl);
            if (!response.ok) {
                throw new Error(`Unexpected response status: ${response.status}`);
            }
            const markdown = await response.text();

            await navigator.clipboard.writeText(markdown);
            button.textContent = button.dataset.successLabel || defaultLabel;
        } catch (error) {
            console.error('Unable to copy page content for LLMs', error);
            button.textContent = button.dataset.errorLabel || defaultLabel;
        }

        setTimeout(() => {
            button.textContent = defaultLabel;
        }, 2000);
    }

    bindEvents() {
        this.toggleButton.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.toggleMenu();
        });

        this.copyButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.copyForLLMs();
            this.closeMenu();
        });

        this.printButton.addEventListener('click', (e) => {
            e.preventDefault();
            this.closeMenu();
            window.print();
        });

        document.addEventListener('click', (e) => {
            if (
                this.isOpen() &&
                !this.toggleButton.contains(e.target) &&
                !this.menu.contains(e.target)
            ) {
                this.closeMenu();
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen()) {
                this.closeMenu();
            }
        });
    }
}

export default PageExportMenu;
