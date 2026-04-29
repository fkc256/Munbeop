/* auth.js — login / signup / logout / current-user / header rendering */
(function () {
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  async function fetchCurrentUser() {
    if (!window.TokenStorage.getAccess()) return null;
    const res = await window.api.get('/accounts/me/');
    if (!res.ok) return null;
    return res.json();
  }

  async function login(username, password) {
    const res = await fetch(window.API_BASE + '/accounts/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || '로그인에 실패했습니다.');
    }
    const data = await res.json();
    window.TokenStorage.set(data.access, data.refresh);
    return data;
  }

  async function signup(payload) {
    const res = await fetch(window.API_BASE + '/accounts/signup/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw err; // field-level errors for the form to render
    }
    return res.json();
  }

  async function logout() {
    const refresh = window.TokenStorage.getRefresh();
    if (refresh) {
      try { await window.api.post('/accounts/logout/', { refresh }); } catch (_) {}
    }
    window.TokenStorage.clear();
    window.location.href = '/';
  }

  async function renderAuthArea() {
    const area = document.querySelector('.auth-area');
    if (!area) return;
    const user = await fetchCurrentUser();
    if (user) {
      area.innerHTML =
        '<a href="/me/" class="auth-link">' + escapeHtml(user.nickname) + '님</a>' +
        '<button id="logout-btn" class="btn-ghost btn-sm" type="button">로그아웃</button>';
      const btn = document.getElementById('logout-btn');
      if (btn) btn.addEventListener('click', logout);
    } else {
      area.innerHTML =
        '<a href="/login/" class="auth-link">로그인</a>' +
        '<a href="/signup/" class="btn-primary btn-sm">회원가입</a>';
    }
  }

  window.auth = { login, signup, logout, fetchCurrentUser, renderAuthArea };
  window.escapeHtml = escapeHtml;

  document.addEventListener('DOMContentLoaded', renderAuthArea);
})();
