/* api.js — fetch wrapper with JWT token handling and 401 auto-refresh */
(function () {
  const API_BASE = '/api';

  const TokenStorage = {
    getAccess() { return localStorage.getItem('access_token'); },
    getRefresh() { return localStorage.getItem('refresh_token'); },
    set(access, refresh) {
      if (access) localStorage.setItem('access_token', access);
      if (refresh) localStorage.setItem('refresh_token', refresh);
    },
    clear() {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    },
  };

  async function tryRefresh() {
    const refresh = TokenStorage.getRefresh();
    if (!refresh) return false;
    try {
      const res = await fetch(API_BASE + '/accounts/login/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (!res.ok) {
        TokenStorage.clear();
        return false;
      }
      const data = await res.json();
      TokenStorage.set(data.access, data.refresh || refresh);
      return true;
    } catch (_) {
      TokenStorage.clear();
      return false;
    }
  }

  async function apiRequest(path, options) {
    options = options || {};
    const url = path.startsWith('http') ? path : API_BASE + path;
    const headers = Object.assign(
      { 'Content-Type': 'application/json' },
      options.headers || {}
    );
    const access = TokenStorage.getAccess();
    if (access) headers['Authorization'] = 'Bearer ' + access;

    const init = Object.assign({}, options, { headers });
    delete init._retry;
    let response = await fetch(url, init);

    if (response.status === 401 && TokenStorage.getRefresh() && !options._retry) {
      const refreshed = await tryRefresh();
      if (refreshed) {
        return apiRequest(path, Object.assign({}, options, { _retry: true }));
      }
    }
    return response;
  }

  window.API_BASE = API_BASE;
  window.TokenStorage = TokenStorage;
  window.api = {
    get: (path) => apiRequest(path, { method: 'GET' }),
    post: (path, body) => apiRequest(path, { method: 'POST', body: JSON.stringify(body || {}) }),
    patch: (path, body) => apiRequest(path, { method: 'PATCH', body: JSON.stringify(body || {}) }),
    put: (path, body) => apiRequest(path, { method: 'PUT', body: JSON.stringify(body || {}) }),
    delete: (path) => apiRequest(path, { method: 'DELETE' }),
  };
})();
