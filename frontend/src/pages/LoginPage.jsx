import { useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { API } from '../services/apijs';
import '../styles/legacy/login/style_login.css';

const normalize = (value) => (value || '').trim();

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [me, setMe] = useState({ auth: false });
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let mounted = true;
    API.auth
      .me()
      .then((data) => {
        if (mounted && data?.auth) {
          setMe(data);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (me?.auth) {
      const next = params.get('next');
      if (next) {
        navigate(next, { replace: true });
      }
    }
  }, [me, navigate, params]);

  const submit = async (event) => {
    event.preventDefault();
    setMessage('');
    const normalizedEmail = normalize(email).toLowerCase();
    const normalizedPassword = normalize(password);
    if (!normalizedEmail || !normalizedPassword) {
      setMessage('Debes ingresar correo y password');
      return;
    }
    try {
      setLoading(true);
      const response = await API.auth.login(normalizedEmail, normalizedPassword);
      if (response?.user) {
        setMe({ auth: true, user: response.user });
        setEmail('');
        setPassword('');
        const next = params.get('next');
        if (next) {
          navigate(next, { replace: true });
        } else {
          navigate('/admin/productos', { replace: true });
        }
      } else {
        setMessage('No fue posible iniciar sesion');
      }
    } catch (error) {
      setMessage(error?.message || 'Credenciales invalidas.');
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await API.auth.logout();
    } catch (error) {
      // ignore logout failures
    }
    setMe({ auth: false });
  };

  return (
    <main>
      <div className='d-flex justify-content-center align-items-center' style={{ height: '67.5vh' }}>
        <div className='container mt-5 border mx-auto' style={{ backgroundColor: 'rgba(0,0,0,.904)', width: 500, borderRadius: 13, color: 'white' }}>
          <h2 className='text-center m-4'>Acceso de Administrador Fitter Gym Chain</h2>

          {me.auth ? (
            <div className='text-center'>
              <p>
                Sesion iniciada como <strong>{me.user?.full_name || me.user?.email || 'Usuario'}</strong>
              </p>
              <button className='btn btn-light' onClick={logout}>
                Cerrar Sesion
              </button>
            </div>
          ) : (
            <form className='w-50 mx-auto' onSubmit={submit}>
              <div className='form-group mb-3'>
                <label htmlFor='loginEmail'>Correo electronico</label>
                <input
                  id='loginEmail'
                  type='email'
                  className='form-control'
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder='correo@dominio.com'
                  autoComplete='email'
                  required
                />
              </div>
              <div className='form-group mb-3'>
                <label htmlFor='loginPassword'>Password</label>
                <input
                  type='password'
                  id='loginPassword'
                  className='form-control'
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder='Password'
                  autoComplete='current-password'
                  required
                />
              </div>
              <div className='text-center mb-2'>
                <span>No tienes cuenta? </span>
                <Link to='/registro'>Registrate aqui</Link>
              </div>
              {message && <div className='alert alert-danger mt-2'>{message}</div>}
              <div className='d-flex justify-content-center m-3'>
                <button
                  type='submit'
                  className='btn'
                  style={{ backgroundColor: 'black', color: 'white', borderColor: 'rgba(255,255,255,.568)' }}
                  disabled={loading}
                >
                  {loading ? 'Iniciando...' : 'Iniciar Sesion'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}
