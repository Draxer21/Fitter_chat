// src/services/apijs.js
const j = async (r) => {
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
};

export const API = {
  productos: {
    list:  () => fetch("/producto/",         { credentials: "include" }).then(j),
    get:   (id) => fetch(`/producto/${id}`,  { credentials: "include" }).then(j),
    create:(data)=> fetch("/producto/", {
      method:"POST", headers:{ "Content-Type":"application/json" },
      credentials:"include", body: JSON.stringify(data)
    }).then(j),
    update:(id,data)=> fetch(`/producto/${id}`, {
      method:"PUT", headers:{ "Content-Type":"application/json" },
      credentials:"include", body: JSON.stringify(data)
    }).then(j),
    del:   (id)=> fetch(`/producto/${id}`,   { method:"DELETE", credentials:"include" }).then(j),
  },
  carrito: {
    estado:  () => fetch("/carrito/estado",             { credentials:"include" }).then(j),
    add:     (id)=> fetch(`/carrito/agregar/${id}`,      { method:"POST", credentials:"include" }).then(j),
    dec:     (id)=> fetch(`/carrito/restar/${id}`,       { method:"POST", credentials:"include" }).then(j),
    remove:  (id)=> fetch(`/carrito/eliminar/${id}`,     { method:"POST", credentials:"include" }).then(j),
    clear:   () => fetch("/carrito/limpiar",             { method:"POST", credentials:"include" }).then(j),
    validar: () => fetch("/carrito/validar",             { method:"POST", credentials:"include" }).then(j),
    boleta:  () => fetch("/carrito/boleta_json",         { credentials:"include" }).then(j),
  },
  auth: {
    me:     () => fetch("/auth/me",    { credentials:"include" }).then(j),
    login:  (u,p)=> fetch("/auth/login", {
      method:"POST", headers:{ "Content-Type":"application/json" },
      credentials:"include", body: JSON.stringify({ user:u, pwd:p })
    }).then(j),
    logout: () => fetch("/auth/logout", { method:"POST", credentials:"include" }).then(j),
  },
  chat: {
    send:(sender,message)=> fetch("/chat/send", {
      method:"POST", headers:{ "Content-Type":"application/json" },
      credentials:"include", body: JSON.stringify({ sender, message })
    }).then(j),
  }
};
