/**
 * Hub UI Component System
 * A lightweight component loader for template-based HTML components.
 * 
 * Usage:
 *   <div data-component="service-card" data-props='{"name":"Ollama","status":"online"}'></div>
 *   
 *   Components.load('service-card', container, { name: 'Ollama', status: 'online' });
 */

const Components = (function () {
    // Component template cache
    const templateCache = {};

    // Component directory
    const COMPONENT_DIR = 'components/';

    /**
     * Load a component template file
     */
    async function loadTemplate(name) {
        if (templateCache[name]) {
            return templateCache[name];
        }

        try {
            const response = await fetch(`${COMPONENT_DIR}${name}.html`);
            if (!response.ok) {
                console.error(`Component not found: ${name}`);
                return null;
            }
            const template = await response.text();
            templateCache[name] = template;
            return template;
        } catch (error) {
            console.error(`Error loading component ${name}:`, error);
            return null;
        }
    }

    /**
     * Render template with props using simple string replacement
     * Supports: {{propName}}, {{#if condition}}...{{/if}}, {{#each items}}...{{/each}}
     */
    function renderTemplate(template, props) {
        if (!template || !props) return template || '';

        let result = template;

        // Simple variable replacement: {{propName}}
        result = result.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return props[key] !== undefined ? props[key] : '';
        });

        // Nested property access: {{object.property}}
        result = result.replace(/\{\{(\w+)\.(\w+)\}\}/g, (match, obj, key) => {
            return props[obj] && props[obj][key] !== undefined ? props[obj][key] : '';
        });

        // Conditional: {{#if condition}}content{{/if}}
        result = result.replace(/\{\{#if (\w+)\}\}([\s\S]*?)\{\{\/if\}\}/g, (match, condition, content) => {
            return props[condition] ? content : '';
        });

        // Conditional with else: {{#if condition}}content{{else}}other{{/if}}
        result = result.replace(/\{\{#if (\w+)\}\}([\s\S]*?)\{\{else\}\}([\s\S]*?)\{\{\/if\}\}/g,
            (match, condition, ifContent, elseContent) => {
                return props[condition] ? ifContent : elseContent;
            }
        );

        // Each loop: {{#each items}}...{{/each}} - items are available as {{.}} or {{this}}
        result = result.replace(/\{\{#each (\w+)\}\}([\s\S]*?)\{\{\/each\}\}/g, (match, key, content) => {
            const items = props[key];
            if (!Array.isArray(items)) return '';
            return items.map((item, index) => {
                let itemContent = content;
                if (typeof item === 'object') {
                    // Replace {{propName}} with item.propName
                    itemContent = itemContent.replace(/\{\{(\w+)\}\}/g, (m, k) => {
                        return item[k] !== undefined ? item[k] : '';
                    });
                } else {
                    // Replace {{.}} or {{this}} with the item value
                    itemContent = itemContent.replace(/\{\{\.\}\}|\{\{this\}\}/g, item);
                }
                // Replace {{@index}} with current index
                itemContent = itemContent.replace(/\{\{@index\}\}/g, index);
                return itemContent;
            }).join('');
        });

        return result;
    }

    /**
     * Load and render a component into a container
     */
    async function load(componentName, container, props = {}) {
        const template = await loadTemplate(componentName);
        if (!template) {
            container.innerHTML = `<div class="component-error">Component '${componentName}' not found</div>`;
            return null;
        }

        const html = renderTemplate(template, props);

        if (typeof container === 'string') {
            container = document.querySelector(container);
        }

        if (container) {
            container.innerHTML = html;
        }

        return html;
    }

    /**
     * Render a component and return HTML (without inserting into DOM)
     */
    async function render(componentName, props = {}) {
        const template = await loadTemplate(componentName);
        if (!template) return '';
        return renderTemplate(template, props);
    }

    /**
     * Initialize all data-component elements on the page
     */
    async function initAll() {
        const elements = document.querySelectorAll('[data-component]');

        for (const el of elements) {
            const componentName = el.dataset.component;
            let props = {};

            try {
                if (el.dataset.props) {
                    props = JSON.parse(el.dataset.props);
                }
            } catch (e) {
                console.error(`Invalid props for component ${componentName}:`, e);
            }

            await load(componentName, el, props);
        }
    }

    /**
     * Register a component template (for inline templates)
     */
    function register(name, template) {
        templateCache[name] = template;
    }

    /**
     * Preload components for faster rendering
     */
    async function preload(componentNames) {
        await Promise.all(componentNames.map(name => loadTemplate(name)));
    }

    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAll);
    } else {
        // DOM already ready, but defer to allow manual control
        setTimeout(initAll, 0);
    }

    // Public API
    return {
        load,
        render,
        register,
        preload,
        initAll,
        renderTemplate
    };
})();

// Export for ES modules if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Components;
}
