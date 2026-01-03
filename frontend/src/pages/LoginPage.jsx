import { useCallback, useEffect, useState } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLocale } from '../contexts/LocaleContext';
import '../styles/legacy/login/style_login.css';
import GoogleAuthButton from '../components/GoogleAuthButton';
import NicknamePrompt from '../components/NicknamePrompt';

const normalize = (value) => (value || '').trim();

export default function LoginPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { t } = useLocale();
  const { user, isAuthenticated, login: loginUser, loginWithGoogle, logout: logoutUser, initialized, authenticating } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [totp, setTotp] = useState('');
  const [backupCode, setBackupCode] = useState('');
  const [needsMfa, setNeedsMfa] = useState(false);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [showNicknamePrompt, setShowNicknamePrompt] = useState(false);
  const [pendingRedirect, setPendingRedirect] = useState(null);

  useEffect(() => {
    if (!initialized) {
      return;
    }
    if (isAuthenticated) {
      const next = params.get('next');
      if (next) {
        navigate(next, { replace: true });
      }
    }
  }, [initialized, isAuthenticated, navigate, params]);

  useEffect(() => {
    if (isAuthenticated && user?.needs_username) {
      setShowNicknamePrompt(true);
    }
  }, [isAuthenticated, user]);

  const resolveNext = useCallback(() => pendingRedirect || params.get('next') || '/admin/productos', [pendingRedirect, params]);

  const handleNicknameComplete = useCallback(() => {
    const destination = resolveNext();
    setPendingRedirect(null);
    setShowNicknamePrompt(false);
    navigate(destination, { replace: true });
  }, [navigate, resolveNext]);

  const handlePostLogin = useCallback(
    (result) => {
      const destination = params.get('next') || '/admin/productos';
      if (result?.user?.needs_username) {
        setPendingRedirect(destination);
        setShowNicknamePrompt(true);
        return;
      }
      navigate(destination, { replace: true });
    },
    [navigate, params]
  );

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
      const options = {};
      if (totp) options.totp = totp;
      if (backupCode) options.backupCode = backupCode;
      const result = await loginUser(normalizedUsername, normalizedPassword, options);
      setUsername('');
      setPassword('');
      setTotp('');
      setBackupCode('');
      setNeedsMfa(false);
      setMessage('');
      handlePostLogin(result);
    } catch (error) {
      if (error?.payload?.mfa_required) {
        setNeedsMfa(true);
        setMessage('Se requiere un código TOTP o uno de tus códigos de respaldo para completar el ingreso.');
      } else {
        setMessage(error?.message || t('login.credentials.invalid'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleCredential = useCallback(
    async (credential) => {
      if (!credential) {
        setMessage(t('login.error'));
        return;
      }
      try {
        setLoading(true);
        const result = await loginWithGoogle(credential);
        setTotp('');
        setBackupCode('');
        setNeedsMfa(false);
        setMessage('');
        handlePostLogin(result);
      } catch (error) {
        setMessage(error?.message || t('login.error'));
      } finally {
        setLoading(false);
      }
    },
    [handlePostLogin, loginWithGoogle, t]
  );

  const logout = async () => {
    await logoutUser();
  };

  return (
    <main>
      <div className='d-flex justify-content-center align-items-center' style={{ height: '67.5vh' }}>
        <div className='container mt-5 border mx-auto' style={{ backgroundColor: 'rgba(0,0,0,.904)', width: 500, borderRadius: 13, color: 'white' }}>
          <h2 className='text-center m-4'>{t('login.title')}</h2>

          {isAuthenticated ? (
            <div className='text-center'>
              <p>
                {t('login.loggedInAs')}: <strong>{user?.full_name || user?.username || 'Usuario'}</strong>
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
                  aria-invalid={Boolean(message)}
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
                  aria-invalid={Boolean(message)}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  placeholder={t('login.password.placeholder')}
                  autoComplete='current-password'
                  required
                />
              </div>
              {(needsMfa || totp || backupCode) && (
                <>
                  <div className='form-group mb-3'>
                    <label htmlFor='loginTotp'>Código TOTP</label>
                    <input
                      id='loginTotp'
                      className='form-control'
                      value={totp}
                      onChange={(event) => setTotp(event.target.value)}
                      placeholder='Ingresa el código de tu app autenticadora'
                      autoComplete='one-time-code'
                    />
                  </div>
                  <div className='form-group mb-3'>
                    <label htmlFor='loginBackup'>Código de respaldo</label>
                    <input
                      id='loginBackup'
                      className='form-control'
                      value={backupCode}
                      onChange={(event) => setBackupCode(event.target.value)}
                      placeholder='Úsalo si no tienes acceso al TOTP'
                      autoComplete='off'
                    />
                    <small className='form-text text-muted'>Puedes dejarlo vacío si usarás el código TOTP.</small>
                  </div>
                </>
              )}
              <div className='text-center mb-2'>
                <span>{t('login.noAccount')} </span>
                <Link to='/registro'>{t('login.gotoRegister')}</Link>
              </div>
              {message && <div className='alert alert-danger mt-2' role='alert' aria-live='assertive'>{message}</div>}
              <div className='d-flex justify-content-center m-3'>
                <button
                  type='submit'
                  className='btn'
                  style={{ backgroundColor: 'black', color: 'white', borderColor: 'rgba(255,255,255,.568)' }}
                  disabled={loading || authenticating}
                >
                  {loading || authenticating ? t('login.loading') : t('login.submit')}
                </button>
              </div>
              <div className='mt-3'>
                <p className='text-center text-uppercase text-muted small mb-2'>{t('login.or')}</p>
                <GoogleAuthButton
                  onCredential={handleGoogleCredential}
                  mode='signin'
                  className='d-flex flex-column align-items-center'
                />
                <p className='text-center small text-muted mt-2 mb-0'>{t('login.googleCta')}</p>
              </div>
            </form>
          )}

          <NicknamePrompt
            visible={showNicknamePrompt}
            title={t('login.nickname.title')}
            description={t('login.nickname.description')}
            placeholder={t('login.nickname.placeholder')}
            submitLabel={t('login.nickname.submit')}
            skipLabel={t('login.nickname.skip')}
            validationMessage={t('login.nickname.error')}
            errorMessage={t('login.nickname.error')}
            onSuccess={handleNicknameComplete}
            onSkip={handleNicknameComplete}
          />
        </div>
      </div>
    </main>
  );
}
