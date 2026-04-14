class ThemeToggle {
    static selector() {
        return '[data-theme-toggle]';
    }
    
    constructor(node) {
        this.toggleSwitch = node;
        document.documentElement.classList.toggle(
            "dark",
            localStorage.theme === "dark" ||
                (!("theme" in localStorage) && window.matchMedia("(prefers-color-scheme: dark)").matches),
        );
        this.currentTheme = localStorage.theme || (window.matchMedia("(prefers-color-scheme: dark)").matches ? 'dark' : 'light');

        if (this.currentTheme) {
            document.documentElement.dataset.theme = this.currentTheme;
            if (this.currentTheme === 'dark') {
                this.toggleSwitch.checked = true;
            }
        }
        this.bindEvents()
    }
    

    bindEvents() {
        this.toggleSwitch.addEventListener('change', this.switchTheme, false);
    }

    switchTheme(e) {
        if (e.target.checked) {
            localStorage.theme = 'dark';
            document.documentElement.dataset.theme = localStorage.theme;
        } else {
            localStorage.theme = 'light';
            document.documentElement.dataset.theme = localStorage.theme;
        }
    }
}

export default ThemeToggle;