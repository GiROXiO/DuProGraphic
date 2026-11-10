import axios from "axios";

const TOKEN_KEY = "duprographic_token";
const USER_KEY = "duprographic_user";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "",
});

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY));
  } catch {
    return null;
  }
}

export function saveSession(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

// Adjunta el token en cada petición.
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Si el backend dice que la sesión no vale (401), se limpia y se va al login.
// El propio login devuelve 401 con credenciales malas: ese caso lo maneja Login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const esLogin = error.config?.url?.includes("/api/auth/login");
    if (error.response?.status === 401 && !esLogin) {
      clearSession();
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  },
);

export default api;
