import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import Alert from '../components/Alert';
import { API } from '../services/apijs';

import '../assets/css/style_login.css';
import '../assets/css/registro_usuario.css';

const normalize = (value) => (value || '').trim();

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [password2, setPassword2] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const showMessage = (type, text) => setMessages([{ type, text }]);

  const validate = () => {
    const name = normalize(fullName);
    const mail = normalize(email).toLowerCase();
    const pass = normalize(password);
    const passConfirm = normalize(password2);

    if (!name || !mail || !pass || !passConfirm) {
      showMessage('danger', 'Nombre, correo y password son obligatorios');
      return null;
    }
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) {
      showMessage('danger', 'Correo no es valido');
      return null;
    }
    if (pass.length < 6) {
      showMessage('danger', 'Password debe tener al menos 6 caracteres');
      return null;
    }
    if (pass !== passConfirm) {
      showMessage('danger', 'Las contrasenas no coinciden');
      return null;
    }
    return { full_name: name, email: mail, password: pass };
  };

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
      showMessage('success', 'Registro exitoso, redirigiendo a iniciar sesion...');
      setTimeout(() => navigate('/login', { replace: true }), 1500);
    } catch (error) {
      showMessage('danger', error?.message || 'No fue posible registrar la cuenta');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='registro-bg d-flex flex-column min-vh-100'>
      <Navbar />

      <main className='container mt-4 mb-5 flex-grow-1 d-flex justify-content-center align-items-center'>
        <div className='card p-5' style={{ maxWidth: 500, width: '100%' }}>
          <h2 className='mb-4 text-center text-dark fw-bold'>Crear Cuenta</h2>
          <form id='formulario' onSubmit={handleSubmit} noValidate>
            {messages.map((msg, index) => (
              <Alert key={index} type={msg.type} message={msg.text} />
            ))}

            <div className='mb-3'>
              <label htmlFor='registerName' className='form-label'>Nombre completo</label>
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
              <label htmlFor='registerEmail' className='form-label'>Correo electronico</label>
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
              <label htmlFor='registerPassword' className='form-label'>Password</label>
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
              <label htmlFor='registerPassword2' className='form-label'>Confirmar password</label>
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
              {loading ? 'Registrando...' : 'Registrarse'}
            </button>
          </form>

          <div className='text-center mt-4'>
            <p className='text-dark mb-0'>Ya tienes una cuenta?</p>
            <Link to='/login' className='text-primary text-decoration-none fw-medium'>Inicia sesion aqui</Link>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
