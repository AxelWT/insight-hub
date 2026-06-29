import { ref, onMounted, onUnmounted, provide, inject, type InjectionKey, type Ref } from 'vue'

export const ThemeKey: InjectionKey<{ theme: Ref<string>; toggleTheme: () => void }> = Symbol('theme')

function getSystemTheme(): string {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getInitialTheme(): string {
  const stored = localStorage.getItem('theme')
  if (stored === 'dark' || stored === 'light') return stored
  return getSystemTheme()
}

export function useThemeProvider() {
  const theme = ref(getInitialTheme())

  function applyTheme(t: string) {
    document.documentElement.dataset.theme = t
    theme.value = t
  }

  function toggleTheme() {
    const next = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('theme', next)
    applyTheme(next)
  }

  provide(ThemeKey, { theme, toggleTheme })

  let mediaQuery: MediaQueryList | null = null
  function onMediaChange() {
    if (localStorage.getItem('theme')) return
    applyTheme(getSystemTheme())
  }

  onMounted(() => {
    applyTheme(theme.value)
    mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', onMediaChange)
  })

  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', onMediaChange)
  })

  return { theme, toggleTheme }
}

export function useTheme() {
  return inject(ThemeKey, { theme: ref('dark') as Ref<string>, toggleTheme: () => {} })
}
