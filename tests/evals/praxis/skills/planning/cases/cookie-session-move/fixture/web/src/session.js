import { api } from "./api.js";

export async function login(email, password) {
  const { token } = await api("/api/login", { method: "POST", body: JSON.stringify({ email, password }) });
  localStorage.setItem("token", token);
}

export async function logout() {
  await api("/api/logout", { method: "POST" });
  localStorage.removeItem("token");
}
