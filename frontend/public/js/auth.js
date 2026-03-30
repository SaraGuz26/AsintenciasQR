const API_URL = "http://127.0.0.1:8000";

export function guardarToken(token) {
    localStorage.setItem("token", token);
}

export function obtenerToken() {
    return localStorage.getItem("token");
}

export function fetchAuth(url, options = {}) {
    const token = obtenerToken();

    return fetch(API_URL + url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
            "Authorization": "Bearer " + token
        }
    });
}