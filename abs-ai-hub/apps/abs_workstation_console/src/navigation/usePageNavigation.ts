import { ref, computed, onMounted, onUnmounted } from 'vue'

export interface PageConfig {
    id: string
    title: string
    shortTitle: string
}

export const PAGES: PageConfig[] = [
    { id: 'overview', title: 'System Overview', shortTitle: 'Overview' },
    { id: 'performance', title: 'Performance', shortTitle: 'Performance' },
    { id: 'workloads', title: 'Active Workloads', shortTitle: 'Workloads' },
    { id: 'models', title: 'Installed Models', shortTitle: 'Models' },
    { id: 'orchestration', title: 'Model Orchestration', shortTitle: 'Orchestration' },
    { id: 'explore', title: 'Explore ABS', shortTitle: 'Explore' }
]

export function usePageNavigation() {
    const currentIndex = ref(0)
    const transitionDirection = ref<'left' | 'right'>('right')

    const currentPage = computed(() => PAGES[currentIndex.value])
    const canGoNext = computed(() => currentIndex.value < PAGES.length - 1)
    const canGoPrev = computed(() => currentIndex.value > 0)
    const totalPages = computed(() => PAGES.length)

    function goToPage(index: number) {
        if (index >= 0 && index < PAGES.length && index !== currentIndex.value) {
            transitionDirection.value = index > currentIndex.value ? 'right' : 'left'
            currentIndex.value = index
        }
    }

    function goNext() {
        if (canGoNext.value) {
            transitionDirection.value = 'right'
            currentIndex.value++
        }
    }

    function goPrev() {
        if (canGoPrev.value) {
            transitionDirection.value = 'left'
            currentIndex.value--
        }
    }

    function handleKeydown(e: KeyboardEvent) {
        // Ignore if user is typing in an input
        if ((e.target as HTMLElement).tagName === 'INPUT') return

        switch (e.key) {
            case 'ArrowRight':
            case 'PageDown':
                e.preventDefault()
                goNext()
                break
            case 'ArrowLeft':
            case 'PageUp':
                e.preventDefault()
                goPrev()
                break
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
                goToPage(parseInt(e.key) - 1)
                break
        }
    }

    onMounted(() => {
        window.addEventListener('keydown', handleKeydown)
    })

    onUnmounted(() => {
        window.removeEventListener('keydown', handleKeydown)
    })

    return {
        currentIndex,
        currentPage,
        pages: PAGES,
        totalPages,
        canGoNext,
        canGoPrev,
        transitionDirection,
        goToPage,
        goNext,
        goPrev
    }
}

