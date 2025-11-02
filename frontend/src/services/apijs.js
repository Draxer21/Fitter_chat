// src/services/apijs.js
const BASE = process.env.NODE_ENV === "development" ? "" : ""; // con proxy activo basta cadena vacia
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
    const error = new Error(message || `HTTP ${resp.status}`);
    error.status = resp.status;
    if (body && typeof body === 'object') {
      error.payload = body;
    }
    throw error;
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
    pagar:   (paymentData) => fetch(`${BASE}/carrito/pagar`, { method:"POST", headers: { "Content-Type": "application/json" }, credentials:"include", body: JSON.stringify(paymentData) }).then(j),
    boleta:  (orderId) => {
      const url = orderId ? `${BASE}/carrito/boleta_json?order=${orderId}` : `${BASE}/carrito/boleta_json`;
      return fetch(url, { credentials:"include" }).then(j);
    },
  },
  auth: {
    me:    () => fetch(`${BASE}/auth/me`, { credentials:"include" }).then(j),
    login: (u,p,opts={})=> fetch(`${BASE}/auth/login`, {
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      credentials:"include",
      body: JSON.stringify({
        username:u,
        user:u,
        password:p,
        pwd:p,
        ...(opts && opts.totp ? { totp: opts.totp, code: opts.totp } : {}),
        ...(opts && opts.token ? { token: opts.token } : {}),
        ...(opts && opts.backupCode ? { backup_code: opts.backupCode, recovery_code: opts.backupCode } : {})
      })
    }).then(j),
    logout:() => fetch(`${BASE}/auth/logout`, { method:"POST", credentials:"include" }).then(j),
    register: (payload) => fetch(`${BASE}/auth/register`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify(payload) }).then(j),
    mfa: {
      status: () => fetch(`${BASE}/auth/mfa/status`, { credentials:"include" }).then(j),
      setup:  () => fetch(`${BASE}/auth/mfa/setup`, { method:"POST", credentials:"include" }).then(j),
      confirm: ({ code }) => fetch(`${BASE}/auth/mfa/confirm`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        credentials:"include",
        body: JSON.stringify({ code })
      }).then(j),
      disable: ({ code, backupCode } = {}) => fetch(`${BASE}/auth/mfa/disable`, {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        credentials:"include",
        body: JSON.stringify({
          ...(code ? { code, totp: code } : {}),
          ...(backupCode ? { backup_code: backupCode, recovery_code: backupCode } : {})
        })
      }).then(j),
    },
  },
  profile: {
    me: () => fetch(`${BASE}/profile/me`, { credentials:"include" }).then(j),
    update: (payload) => fetch(`${BASE}/profile/me`, {
      method:"PUT",
      headers:{ "Content-Type":"application/json" },
      credentials:"include",
      body: JSON.stringify(payload)
    }).then(j),
  },
  orders: {
    get: (id) => fetch(`${BASE}/orders/${id}`, { credentials:"include" }).then(j),
    summary: (params="") => fetch(`${BASE}/admin/orders/summary${params ? `?${params}` : ""}`, { credentials:"include" }).then(j),
    list: (params="") => fetch(`${BASE}/admin/orders${params ? `?${params}` : ""}`, { credentials:"include" }).then(j),
    receiptPdf: (id) => fetch(`${BASE}/orders/${id}/receipt.pdf`, { credentials:"include" }),
  },
  chat: {
    send:  (sender,message)=> fetch(`${BASE}/chat/send`, { method:"POST", headers:{ "Content-Type":"application/json" }, credentials:"include", body: JSON.stringify({ sender, message }) }).then(j),
  }
};



