// theme.js – shared light/dark mode across all pages
const THEME_KEY = 'myhospital-theme';

function applyStoredTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  const html = document.documentElement;

  if (stored === 'dark' || stored === 'light') {
    html.setAttribute('data-theme', stored);
  } else {
    html.setAttribute('data-theme', 'light');
  }

  const lightBtn = document.getElementById('lightModeToggle');
  if (lightBtn) {
    const current = html.getAttribute('data-theme');
    lightBtn.textContent = current === 'light' ? 'Dark mode' : 'Light mode';
  }
}

function toggleThemeFromButton() {
  const html = document.documentElement;
  const current = html.getAttribute('data-theme') || 'light';
  const next = current === 'light' ? 'dark' : 'light';

  html.setAttribute('data-theme', next);
  localStorage.setItem(THEME_KEY, next);

  const lightBtn = document.getElementById('lightModeToggle');
  if (lightBtn) {
    lightBtn.textContent = next === 'light' ? 'Dark mode' : 'Light mode';
  }
}

applyStoredTheme();
