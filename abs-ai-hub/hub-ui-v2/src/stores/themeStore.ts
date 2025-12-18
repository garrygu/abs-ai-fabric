import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export type Theme = 'dark' | 'light'

export const useThemeStore = defineStore('theme', () => {
    // Initialize from localStorage or system preference
    const getInitialTheme = (): Theme => {
        const stored = localStorage.getItem('hub-theme')
        if (stored === 'light' || stored === 'dark') return stored

        // Check system preference
        if (window.matchMedia?.('(prefers-color-scheme: light)').matches) {
            return 'light'
        }
        return 'dark'
    }

    const theme = ref<Theme>(getInitialTheme())

    // Apply theme to document
    function applyTheme(t: Theme) {
        document.documentElement.setAttribute('data-theme', t)
        localStorage.setItem('hub-theme', t)
    }

    // Toggle between themes
    function toggleTheme() {
        theme.value = theme.value === 'dark' ? 'light' : 'dark'
    }

    // Set specific theme
    function setTheme(t: Theme) {
        theme.value = t
    }

    // Watch for changes and apply
    watch(theme, (newTheme) => {
        applyTheme(newTheme)
    }, { immediate: true })

    return {
        theme,
        toggleTheme,
        setTheme
    }
})
