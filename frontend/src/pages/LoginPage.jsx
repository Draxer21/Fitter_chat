import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/login/style_login.css";

export default function LoginPage() {
  const [me, setMe] = useState({auth:false});
  const [usuario, setUsuario] = useState("");
  const [contrasena, setContrasena] = useState("");
  const [msg, setMsg] = useState("");

  useEffect(()=>{ API.auth.me().then(setMe).catch(()=>{}); }, []);

  const submit = async (e) => {
    e.preventDefault(); setMsg("");
    try{
      const r = await API.auth.login(usuario, contrasena);
      setMe({auth:true, user:r.user});
    }catch{ setMsg("Credenciales inválidas."); }
  };
  const logout = async ()=>{ await API.auth.logout(); setMe({auth:false}); };

  return (
    <main>
      <div className="d-flex justify-content-center align-items-center" style={{height:"67.5vh"}}>
        <div className="container mt-5 border mx-auto" style={{backgroundColor:"rgba(0,0,0,.904)", width:500, borderRadius:13, color:"white"}}>
          <h2 className="text-center m-4">Acceso de Administrador <br/>Fitter Gym Chain</h2>

          {me.auth ? (
            <div className="text-center">
              <p>Sesión iniciada como <strong>{me.user}</strong></p>
              <button className="btn btn-light" onClick={logout}>Cerrar Sesión</button>
            </div>
          ) : (
            <form className="w-50 mx-auto" onSubmit={submit}>
              <div className="form-group mb-3">
                <label htmlFor="usuario">Nombre de Usuario</label>
                <input id="usuario" className="form-control" value={usuario} onChange={e=>setUsuario(e.target.value)} placeholder="Introduce tu Nombre de Usuario" />
              </div>
              <div className="form-group mb-3">
                <label htmlFor="contrasena">Contraseña</label>
                <input type="password" id="contrasena" className="form-control" value={contrasena} onChange={e=>setContrasena(e.target.value)} placeholder="Contraseña" />
              </div>
              <div className="text-center">
                <p>¿No tienes cuenta? <a href="/registro">Regístrate aquí</a></p>
              </div>
              {msg && <div className="alert alert-danger mt-2">{msg}</div>}
              <div className="d-flex justify-content-center m-3">
                <button type="submit" className="btn" style={{backgroundColor:"black", color:"white", borderColor:"rgba(255,255,255,.568)"}}>
                  Iniciar Sesión
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
