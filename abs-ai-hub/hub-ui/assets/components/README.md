# Hub UI Component System

A lightweight template-based component system for the ABS Hub UI.

## Quick Start

Include the component loader in your HTML:
```html
<script src="js/components.js"></script>
```

## Usage

### Loading a Component

```javascript
// Load into a container element
Components.load('app-card', '#my-container', {
    id: 'contract-reviewer',
    name: 'Contract Reviewer',
    description: 'AI-powered contract analysis',
    icon: '📄',
    status: 'online'
});

// Or get rendered HTML without inserting
const html = await Components.render('stat-card', { 
    icon: '📱', 
    value: 8, 
    label: 'Applications' 
});
```

### Declarative Usage

```html
<div data-component="stat-card" 
     data-props='{"icon":"📱","value":"8","label":"Applications"}'>
</div>
```

Components will auto-initialize on page load.

---

## Template Syntax

### Variables
```html
<h3>{{name}}</h3>
<span>{{user.email}}</span>
```

### Conditionals
```html
{{#if isAdmin}}
    <button>Delete</button>
{{/if}}

{{#if premium}}
    <span>Premium</span>
{{else}}
    <span>Free</span>
{{/if}}
```

### Loops
```html
{{#each items}}
    <li>{{name}} - {{value}}</li>
{{/each}}

{{#each tags}}
    <span class="tag">{{.}}</span>
{{/each}}
```

---

## Available Components

| Component | Props | Description |
| :--- | :--- | :--- |
| `app-card` | id, name, description, icon, url, status, dependencies | Application card |
| `service-card` | id, name, description, icon, status, critical | Service control card |
| `model-card` | id, name, displayName, status, isDefault, size, provider | Model item |
| `stat-card` | icon, value, label | Statistics display |
| `status-card` | id, name, icon, version, status | Status indicator |

---

## API Reference

| Method | Description |
| :--- | :--- |
| `Components.load(name, container, props)` | Load component into container |
| `Components.render(name, props)` | Render and return HTML |
| `Components.register(name, template)` | Register inline template |
| `Components.preload([names])` | Preload templates |
| `Components.initAll()` | Initialize all data-component elements |
