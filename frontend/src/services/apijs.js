// src/services/apijs.js
const BASE = process.env.NODE_ENV === "development" ? "" : ""; // con proxy activo basta cadena vacía
const parseBody = async (resp) => {
  const raw = await resp.text();
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch (err) {
    return raw;
  }
};

const j = async (resp) => {
  const body = await parseBody(resp);
  if (!resp.ok) {
    const message = body && typeof body === 'object'
      ? body.error || (Array.isArray(body.errores) ? body.errores.join('\n') : body.message)
      : null;
    throw new Error(message || `HTTP ${resp.status}`);
  }
  return body;
};

export const API = {
  productos: {
    list: (q="") => fetch(`${BASE}/producto/${q}`, { credentials:"include" }).then(j),
    get:  (id) => fetch(`${BASE}/producto/${id}`, { credentials:"include" }).then(j),
    create:(d)=> {
      if (d instanceof FormData) {
        return fetch(`${BASE}/producto/`, { method:"POST", credentials:"include", body: d }).then(j);
      }
      return fetch(`${BASE}/producto/`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify(d) }).then(j);
    },
    update:(id,d)=> {
      if (d instanceof FormData) {
        return fetch(`${BASE}/producto/${id}`, { method:"PUT", credentials:"include", body: d }).then(j);
      }
      return fetch(`${BASE}/producto/${id}`, { method:"PUT", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify(d) }).then(j);
    },
    del:  (id) => fetch(`${BASE}/producto/${id}`, { method:"DELETE", credentials:"include" }).then(j),
  },
  carrito: {
    estado:  () => fetch(`${BASE}/carrito/estado`, { credentials:"include" }).then(j),
    add:     (id)=> fetch(`${BASE}/carrito/agregar/${id}`, { method:"POST", credentials:"include" }).then(j),
    dec:     (id)=> fetch(`${BASE}/carrito/restar/${id}`,  { method:"POST", credentials:"include" }).then(j),
    remove:  (id)=> fetch(`${BASE}/carrito/eliminar/${id}`,{ method:"POST", credentials:"include" }).then(j),
    clear:   () => fetch(`${BASE}/carrito/limpiar`,       { method:"POST", credentials:"include" }).then(j),
    validar: () => fetch(`${BASE}/carrito/validar`,       { method:"POST", credentials:"include" }).then(j),
    boleta:  () => fetch(`${BASE}/carrito/boleta_json`,   { credentials:"include" }).then(j),
  },
  auth: {
    me:    () => fetch(`${BASE}/auth/me`, { credentials:"include" }).then(j),
    login: (u,p)=> fetch(`${BASE}/auth/login`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify({ email:u, user:u, password:p, pwd:p }) }).then(j),
    logout:() => fetch(`${BASE}/auth/logout`, { method:"POST", credentials:"include" }).then(j),
    register: (payload) => fetch(`${BASE}/auth/register`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify(payload) }).then(j),
  },
  chat: {
    send:  (sender,message)=> fetch(`${BASE}/chat/send`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify({ sender, message }) }).then(j),
  }
};
