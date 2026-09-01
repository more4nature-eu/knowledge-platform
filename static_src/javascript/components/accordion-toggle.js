class AccordionToggle {
    static selector() {
        return '[data-accordion-toggle]';
    }

    constructor(node) {
        this.toggle = node;
        this.bindEventListeners();
    }

    bindEventListeners() {
        this.toggle.addEventListener('click', () => {
            const isExpanded = this.toggle.getAttribute('aria-expanded') === 'true';
            this.toggle.setAttribute('aria-expanded', String(!isExpanded));
        });
    }
}

export default AccordionToggle;
