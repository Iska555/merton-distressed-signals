'use client'

/**
 * Explicit theme control.
 *
 * Light is the default and lives on bare :root, so the first paint is correct
 * before this component hydrates. Dark is the opt-in, stamped as
 * data-theme="dark". Nothing here reads prefers-color-scheme: a reader who
 * wants dark presses the control, and that choice is what persists.
 */
const STORAGE_KEY = 'dcs-theme'

function applyTheme(theme: 'light' | 'dark') {
  if (theme === 'dark') {
    document.documentElement.dataset.theme = 'dark'
  } else {
    delete document.documentElement.dataset.theme
  }
}

export default function ThemeToggle() {
  function toggleTheme() {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'
    applyTheme(next)
    try {
      window.localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // The visible toggle still works when storage is unavailable.
    }
  }

  return (
    <button
      className="theme-toggle"
      type="button"
      data-theme-toggle="true"
      aria-label="Toggle colour theme"
      title="Toggle colour theme"
      onClick={toggleTheme}
    >
      <span aria-hidden="true">◐</span>
    </button>
  )
}
