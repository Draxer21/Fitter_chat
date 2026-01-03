import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import Alert from '../components/Alert';
import { API } from '../services/apijs';
import { useLocale } from '../contexts/LocaleContext';
import { useAuth } from '../contexts/AuthContext';
import GoogleAuthButton from '../components/GoogleAuthButton';
import NicknamePrompt from '../components/NicknamePrompt';

import '../assets/css/style_login.css';
import '../assets/css/registro_usuario.css';

const normalize = (value) => (value || '').trim();

const usernamePattern = /^[a-zA-Z0-9_-]{3,32}$/;

export default function RegisterPage() {
  const { t } = useLocale();
  const { loginWithGoogle, user, isAuthenticated } = useAuth();
  const [fullName, setFullName] = useState('');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNicknamePrompt, setShowNicknamePrompt] = useState(false);
  const [pendingRedirect, setPendingRedirect] = useState(null);
  const navigate = useNavigate();

  const showMessage = (type, text) => setMessages([{ type, text }]);

  const validate = () => {
    const name = normalize(fullName);
    const user = normalize(username).toLowerCase();
    const mail = normalize(email).toLowerCase();
    const pass = normalize(password);
    const passConfirm = normalize(password2);

    if (!name || !user || !mail || !pass || !passConfirm) {
      showMessage('danger', t('register.error.required'));
      return null;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) {
      showMessage('danger', t('register.error.email'));
      return null;
    }
    if (!usernamePattern.test(user)) {
      showMessage('danger', t('register.error.username'));
      return null;
    }
    if (pass.length < 6) {
      showMessage('danger', t('register.error.passwordLength'));
      return null;
    }
    if (pass !== passConfirm) {
      showMessage('danger', t('register.error.passwordMismatch'));
      return null;
    }
    return { full_name: name, username: user, email: mail, password: pass };
  };

  useEffect(() => {
    if (isAuthenticated && user?.needs_username) {
      setShowNicknamePrompt(true);
    }
  }, [isAuthenticated, user]);

  const resolveRedirect = useCallback(() => pendingRedirect || '/admin/productos', [pendingRedirect]);

  const handleNicknameComplete = useCallback(() => {
    const destination = resolveRedirect();
    setPendingRedirect(null);
    setShowNicknamePrompt(false);
    navigate(destination, { replace: true });
  }, [navigate, resolveRedirect]);

  const handleGoogleCredential = useCallback(
    async (credential) => {
      if (!credential) {
        showMessage('danger', t('login.error'));
        return;
      }
      try {
        setLoading(true);
        const result = await loginWithGoogle(credential);
        setMessages([]);
        if (result?.user?.needs_username) {
          setShowNicknamePrompt(true);
          setPendingRedirect('/admin/productos');
          return;
        }
        navigate('/admin/productos', { replace: true });
      } catch (error) {
        showMessage('danger', error?.message || t('login.error'));
      } finally {
        setLoading(false);
      }
    },
    [loginWithGoogle, navigate, showMessage, t]
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessages([]);
    const payload = validate();
    if (!payload) {
      return;
    }

    try {
      setLoading(true);
      await API.auth.register(payload);
      showMessage('success', t('register.success'));
      setTimeout(() => navigate('/login', { replace: true }), 1500);
    } catch (error) {
      showMessage('danger', error?.message || t('register.error.required'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='registro-bg d-flex flex-column min-vh-100'>
      <Navbar />

      <main className='container mt-4 mb-5 flex-grow-1 d-flex justify-content-center align-items-center'>
        <div className='card p-5' style={{ maxWidth: 500, width: '100%' }}>
          <h2 className='mb-4 text-center text-dark fw-bold'>{t('register.title')}</h2>
          <form id='formulario' onSubmit={handleSubmit} noValidate>
            {messages.map((msg, index) => (
              <Alert key={index} type={msg.type} message={msg.text} />
            ))}

            <div className='mb-3'>
              <label htmlFor='registerName' className='form-label'>{t('register.fullname')}</label>
              <input
                id='registerName'
                className='form-control'
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                placeholder='Tu nombre y apellido'
                required
              />
            </div>

            <div className='mb-3'>
              <label htmlFor='registerUsername' className='form-label'>{t('register.username')}</label>
              <input
                id='registerUsername'
                className='form-control'
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder='tu_usuario'
                required
              />
            </div>

            <div className='mb-3'>
              <label htmlFor='registerEmail' className='form-label'>{t('register.email')}</label>
              <input
                id='registerEmail'
                type='email'
                className='form-control'
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder='correo@dominio.com'
                required
              />
            </div>

            <div className='mb-3'>
              <label htmlFor='registerPassword' className='form-label'>{t('register.password')}</label>
              <input
                id='registerPassword'
                type='password'
                className='form-control'
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder='Password segura'
                required
              />
            </div>

            <div className='mb-4'>
              <label htmlFor='registerPassword2' className='form-label'>{t('register.password.confirm')}</label>
              <input
                id='registerPassword2'
                type='password'
                className='form-control'
                value={password2}
                onChange={(event) => setPassword2(event.target.value)}
                placeholder='Repite tu password'
                required
              />
            </div>

            <button type='submit' className='btn btn-primary w-100 py-2 fw-bold' disabled={loading}>
              {loading ? t('register.loading') : t('register.submit')}
            </button>
          </form>

          <div className='mt-4'>
            <p className='text-center text-uppercase text-muted small mb-2'>{t('login.or')}</p>
            <GoogleAuthButton onCredential={handleGoogleCredential} mode='signup' className='d-flex flex-column align-items-center' />
            <p className='text-center small text-muted mt-2 mb-0'>{t('login.googleCta')}</p>
          </div>

          <div className='text-center mt-4'>
            <p className='text-dark mb-0'>{t('register.haveAccount')}</p>
            <Link to='/login' className='text-primary text-decoration-none fw-medium'>{t('register.gotoLogin')}</Link>
          </div>

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
      </main>

      <Footer />
    </div>
  );
}
