/**
 * api.js — funções de comunicação com o servidor
 */

export async function api(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  return res.json();
}

export const get  = (path)        => api("GET",    path);
export const post = (path, body)  => api("POST",   path, body);
export const put  = (path, body)  => api("PUT",    path, body);
export const del  = (path)        => api("DELETE", path);

/** Mostra toast de feedback */
export function toast(msg, tipo = "ok") {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = msg;
  el.className = `toast toast-${tipo} show`;
  setTimeout(() => el.classList.remove("show"), 3000);
}

/** Usuário logado (do localStorage como cache) */
export function getUsuario() {
  return localStorage.getItem("omcp_usuario") || "sistema";
}
export function setUsuario(u) {
  localStorage.setItem("omcp_usuario", u);
}
