const API_URL = "http://127.0.0.1:8000";

function guardarToken(token) {
    localStorage.setItem("token", token);
}

function obtenerToken() {
    return localStorage.getItem("token");
}

function fetchAuth(url, options = {}) {
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

function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("rol");

    window.location.href = "/frontend/bedelia/login.html";
}