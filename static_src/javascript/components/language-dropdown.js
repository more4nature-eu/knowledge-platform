class LanguageDropdown {
    static selector() {
        return '[data-language-dropdown]';
    }

    constructor(node) {
        this.languageDropdown = node;

        this.languageDropdownContent = node.parentElement.querySelector(
            '[data-language-dropdown-content]'
        );

        this.languageDropdownItems = this.languageDropdownContent.querySelectorAll(
            '[data-language-dropdown-item]'
        );

        this.bindEvents();
    }

    openLanguageSelect() {
        this.languageDropdownContent.classList.remove('invisible');

        this.languageDropdown.classList.add(
            'bg-m4n-neutral',
            'text-white',
            'border-white'
        );

        this.languageDropdownItems.forEach((item, index) => {
            item.style.transitionDelay = `${index * 80}ms`;

            item.classList.remove('opacity-0', '-translate-x-6');
            item.classList.add('opacity-100', 'translate-x-0');
        });
    }

    closeLanguageSelect() {
        [...this.languageDropdownItems]
            .reverse()
            .forEach((item, index) => {
                item.style.transitionDelay = `${index * 60}ms`;

                item.classList.add('opacity-0', '-translate-x-6');
                item.classList.remove('opacity-100', 'translate-x-0');
            });

        this.languageDropdown.classList.remove(
            'bg-m4n-neutral',
            'text-white',
            'border-white'
        );

        setTimeout(() => {
            this.languageDropdownContent.classList.add('invisible');
        }, this.languageDropdownItems.length * 60 + 500);
    }

    bindEvents() {
        this.languageDropdown.addEventListener('click', (e) => {
            e.preventDefault();

            if (this.languageDropdownContent.classList.contains('invisible')) {
                this.openLanguageSelect();
            } else {
                this.closeLanguageSelect();
            }
        });

    }
}

export default LanguageDropdown;
