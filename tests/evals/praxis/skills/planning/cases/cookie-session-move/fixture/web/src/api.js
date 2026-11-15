const API = "https://api.acme.com";

export async function api(path, options = {}) {
  const token = localStorage.getItem("token");
  const res = await fetch(API + path, {
    ...options,
    headers: { ...options.headers, "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) {
    localStorage.removeItem("token");
    location.href = "/login";
  }
  return res.status === 204 ? null : res.json();
}
