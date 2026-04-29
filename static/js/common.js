/* common.js — toast, mobile nav, active link highlighting */
(function () {
  function showToast(message, type) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = 'toast' + (type ? ' toast-' + type : '');
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
      toast.classList.remove('show');
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }

  function setupMobileNav() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.main-nav');
    if (!toggle || !nav) return;
    toggle.addEventListener('click', () => nav.classList.toggle('open'));
  }

  function highlightActiveNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.main-nav a').forEach((a) => {
      const href = a.getAttribute('href') || '';
      if (href === '/' && path === '/') a.classList.add('active');
      else if (href !== '/' && path.startsWith(href)) a.classList.add('active');
    });
  }

  window.showToast = showToast;
  document.addEventListener('DOMContentLoaded', () => {
    setupMobileNav();
    highlightActiveNav();
  });
})();
