/**
 * Component Loader for Modular Frontend
 * Loads HTML components dynamically into the main application
 */

class ComponentLoader {
    constructor() {
        this.components = new Map();
    }

    /**
     * Load a component and insert it into the DOM
     * @param {string} componentName - Name of the component file (without .html extension)
     * @param {string} targetSelector - CSS selector for insertion point
     */
    async loadComponent(componentName, targetSelector) {
        try {
            // Check if already loaded
            if (this.components.has(componentName)) {
                console.log(`Component ${componentName} already loaded`);
                return this.components.get(componentName);
            }

            // Fetch the component HTML
            const response = await fetch(`/static/components/${componentName}.html`);
            if (!response.ok) {
                throw new Error(`Failed to load component: ${componentName}`);
            }

            const html = await response.text();
            
            // Store the component
            this.components.set(componentName, html);

            // Insert into DOM if target selector provided
            if (targetSelector) {
                const target = document.querySelector(targetSelector);
                if (target) {
                    target.insertAdjacentHTML('beforeend', html);
                }
            }

            console.log(`✅ Loaded component: ${componentName}`);
            return html;
        } catch (error) {
            console.error(`❌ Error loading component ${componentName}:`, error);
            return '';
        }
    }

    /**
     * Load multiple components at once
     * @param {Array<{name: string, target: string}>} components - Array of component configs
     */
    async loadComponents(components) {
        const promises = components.map(comp => 
            this.loadComponent(comp.name, comp.target)
        );
        return Promise.all(promises);
    }
}

// Global instance
window.componentLoader = new ComponentLoader();




