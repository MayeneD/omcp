/**
 * Navigation module — links between real pages
 */
export function goTo(screen) {
  if (screen === 'login') {
    window.location.href = '/login';
  } else {
    window.location.href = '/' + screen;
  }
}

/**
 * Mark the active nav button based on current URL path
 */
export function markActiveNav() {
  const path = window.location.pathname.replace('/', '') || 'dashboard';
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  const active = document.querySelector(`.nav-btn[data-page="${path}"]`);
  if (active) active.classList.add('active');
}
