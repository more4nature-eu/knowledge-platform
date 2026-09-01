class TableCellModal {
    static selector() {
        return '[data-modal-trigger]';
    }

    constructor(node) {
        this.trigger = node;
        this.wrapper = node.closest('[data-table-cell]');
        this.dialog = this.wrapper.querySelector('[data-modal]');
        this.closeButton = this.wrapper.querySelector('[data-modal-close]');

        this.bindEventListeners();
    }

    bindEventListeners() {
        this.trigger.addEventListener('click', () => {
            this.dialog.showModal();
        });

        this.closeButton.addEventListener('click', () => {
            this.dialog.close();
        });

        this.dialog.addEventListener('click', (event) => {
            if (event.target === this.dialog) {
                this.dialog.close();
            }
        });
    }
}

export default TableCellModal;
