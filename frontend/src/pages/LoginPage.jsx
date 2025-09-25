import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/login/style_login.css";

export default function LoginPage() {
  const [me, setMe] = useState({ auth: false, user: null });
  const [user, setUser] = useState("");
  const [pwd, setPwd] = useState("");
  const [err, setErr] = useState("");

  useEffect(() => {
    API.auth.me().then(setMe).catch(() => {});
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    try {
      const r = await API.auth.login(user, pwd);
      setMe({ auth: true, user: r.user });
    } catch {
      setErr("Credenciales inválidas.");
    }
  };

  const out = async () => {
    await API.auth.logout();
    setMe({ auth: false, user: null });
  };

  return (
    <div className="legacy-scope" style={{ padding: 16 }}>
      <h2>Login</h2>
      {me.auth ? (
        <>
          <p>Autenticado como <strong>{me.user}</strong></p>
          <button onClick={out}>Salir</button>
        </>
      ) : (
        <form onSubmit={submit} className="login-form">
          <input
            value={user}
            onChange={(e) => setUser(e.target.value)}
            placeholder="usuario"
            autoComplete="username"
            required
          />
          <input
            type="password"
            value={pwd}
            onChange={(e) => setPwd(e.target.value)}
            placeholder="clave"
            autoComplete="current-password"
            required
          />
          {err && <div style={{ color: "#b91c1c", marginTop: 8 }}>{err}</div>}
          <button type="submit">Entrar</button>
        </form>
      )}
    </div>
  );
}
