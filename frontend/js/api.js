const API_BASE = "http://127.0.0.1:8000";

async function fetchJSON(endpoint) {
    const res = await fetch(`${API_BASE}${endpoint}`);
    return res.json();
}
