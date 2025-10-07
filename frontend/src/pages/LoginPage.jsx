import { useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { API } from '../services/apijs';
import { useLocale } from '../contexts/LocaleContext';
import '../styles/legacy/login/style_login.css';

const normalize = (value) => (value || '').trim();

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { t } = useLocale();
  const [me, setMe] = useState({ auth: false });
  const [username, setUsername] = useState('');
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
    const normalizedUsername = normalize(username).toLowerCase();
    const normalizedPassword = normalize(password);
    if (!normalizedUsername || !normalizedPassword) {
      setMessage(t('login.required'));
      return;
    }
    try {
      setLoading(true);
      const response = await API.auth.login(normalizedUsername, normalizedPassword);
      if (response?.user) {
        setMe({ auth: true, user: response.user });
        setUsername('');
        setPassword('');
        const next = params.get('next');
        if (next) {
          navigate(next, { replace: true });
        } else {
          navigate('/admin/productos', { replace: true });
        }
      } else {
        setMessage(t('login.error'));
      }
    } catch (error) {
      setMessage(error?.message || t('login.credentials.invalid'));
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
          <h2 className='text-center m-4'>{t('login.title')}</h2>

          {me.auth ? (
            <div className='text-center'>
              <p>
                {t('login.loggedInAs')}: <strong>{me.user?.full_name || me.user?.username || 'Usuario'}</strong>
              </p>
              <button className='btn btn-light' onClick={logout}>
                {t('login.logout')}
              </button>
            </div>
          ) : (
            <form className='w-50 mx-auto' onSubmit={submit}>
              <div className='form-group mb-3'>
                <label htmlFor='loginUsername'>{t('login.username.label')}</label>
                <input
                  id='loginUsername'
                  className='form-control'
                  value={username}
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder={t('login.username.placeholder')}
                  autoComplete='username'
                  required
                />
              </div>
              <div className='form-group mb-3'>
                <label htmlFor='loginPassword'>{t('login.password.label')}</label>
                <input
                  type='password'
                  id='loginPassword'
                  className='form-control'
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={t('login.password.placeholder')}
                  autoComplete='current-password'
                  required
                />
              </div>
              <div className='text-center mb-2'>
                <span>{t('login.noAccount')} </span>
                <Link to='/registro'>{t('login.gotoRegister')}</Link>
              </div>
              {message && <div className='alert alert-danger mt-2'>{message}</div>}
              <div className='d-flex justify-content-center m-3'>
                <button
                  type='submit'
                  className='btn'
                  style={{ backgroundColor: 'black', color: 'white', borderColor: 'rgba(255,255,255,.568)' }}
                  disabled={loading}
                >
                  {loading ? t('login.loading') : t('login.submit')}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </main>
  );
}

