import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar'; // Asume que tienes un componente Navbar
import Footer from '../components/Footer'; // Asume que tienes un componente Footer
import Alert from '../components/Alert';   // Componente simple para mostrar mensajes

// Importa tus estilos CSS
import '../assets/css/style_login.css';
import '../assets/css/registro_usuario.css';

const RegisterPage = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [password2, setPassword2] = useState('');
    const [messages, setMessages] = useState([]); // Para mensajes de éxito/error
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessages([]); // Limpiar mensajes anteriores
        setLoading(true);

        // Frontend validation (basic)
        if (!username || !email || !password || !password2) {
            setMessages([{ type: 'danger', text: 'Todos los campos son obligatorios.' }]);
            setLoading(false);
            return;
        }
        if (password !== password2) {
            setMessages([{ type: 'danger', text: 'Las contraseñas no coinciden.' }]);
            setLoading(false);
            return;
        }
        if (password.length < 6) { // Ejemplo de validación de longitud
            setMessages([{ type: 'danger', text: 'La contraseña debe tener al menos 6 caracteres.' }]);
            setLoading(false);
            return;
        }
        // Basic email regex
        if (!/\S+@\S+\.\S+/.test(email)) {
            setMessages([{ type: 'danger', text: 'El formato del correo electrónico no es válido.' }]);
            setLoading(false);
            return;
        }

        try {
            // Ajusta esta URL a tu endpoint de registro en el backend Flask
            const response = await fetch('http://localhost:5000/auth/register', { // Asume que tu backend Flask corre en 5000
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ username, email, password, password2 }),
            });

            const data = await response.json();

            if (response.ok) {
                setMessages([{ type: 'success', text: '¡Registro exitoso! Redirigiendo a iniciar sesión...' }]);
                setTimeout(() => {
                    navigate('/login'); // Redirige a la página de login
                }, 2000);
            } else {
                // Manejar errores específicos del backend
                const errorText = data.error || 'Error en el registro. Inténtalo de nuevo.';
                setMessages([{ type: 'danger', text: errorText }]);
            }
        } catch (error) {
            console.error('Error al registrar:', error);
            setMessages([{ type: 'danger', text: 'Error de conexión. Por favor, inténtalo más tarde.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="registro-bg d-flex flex-column min-vh-100">
            <Navbar /> {/* Asume que tu Navbar no necesita props específicas para esta página */}

            <main className="container mt-4 mb-5 flex-grow-1 d-flex justify-content-center align-items-center">
                <div className="card p-5" style={{ maxWidth: '500px', width: '100%' }}>
                    <h2 className="mb-4 text-center text-dark fw-bold">Crear Cuenta</h2>
                    <form id="formulario" onSubmit={handleSubmit} noValidate>
                        {messages.map((msg, index) => (
                            <Alert key={index} type={msg.type} message={msg.text} />
                        ))}

                        <div className="mb-3">
                            <label htmlFor="username" className="form-label">Nombre de usuario</label>
                            <input
                                type="text"
                                className="form-control"
                                id="username"
                                name="username"
                                placeholder="Introduce tu nombre de usuario"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                required
                            />
                            {/* Aquí podrías añadir mensajes de error específicos para cada campo si tu backend los devuelve */}
                        </div>
                        <div className="mb-3">
                            <label htmlFor="email" className="form-label">Correo electrónico</label>
                            <input
                                type="email"
                                className="form-control"
                                id="email"
                                name="email"
                                placeholder="Introduce tu correo electrónico"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                            />
                        </div>
                        <div className="mb-3">
                            <label htmlFor="password" className="form-label">Contraseña</label>
                            <input
                                type="password"
                                className="form-control"
                                id="password"
                                name="password"
                                placeholder="Contraseña"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                required
                            />
                        </div>
                        <div className="mb-4">
                            <label htmlFor="password2" className="form-label">Confirmar contraseña</label>
                            <input
                                type="password"
                                className="form-control"
                                id="password2"
                                name="password2"
                                placeholder="Confirmar contraseña"
                                value={password2}
                                onChange={(e) => setPassword2(e.target.value)}
                                required
                            />
                        </div>
                        <button
                            type="submit"
                            className="btn btn-primary w-100 py-2 fw-bold"
                            disabled={loading}
                        >
                            {loading ? 'Registrando...' : 'Registrarse'}
                        </button>
                    </form>
                    <div className="text-center mt-4">
                        <p className="text-dark mb-0">¿Ya tienes una cuenta?</p>
                        <Link to="/login" className="text-primary text-decoration-none fw-medium">Inicia sesión aquí</Link>
                    </div>
                </div>
            </main>

            <Footer /> {/* Asume que tu Footer no necesita props específicas */}
        </div>
    );
};

export default RegisterPage;

