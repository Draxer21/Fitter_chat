import { NavLink, useNavigate } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import Logo from '../components/Logo';
import { API } from '../services/apijs';

const closeBootstrapModal = (ref) => {
  const Modal = window.bootstrap && window.bootstrap.Modal;
  if (!Modal || !ref || !ref.current) {
    return;
  }
  let instance = Modal.getInstance(ref.current);
  if (!instance) {
    instance = new Modal(ref.current);
  }
  instance.hide();
};

export default function Navbar() {
  const [me, setMe] = useState({ auth: false, is_admin: false, user: '' });
  const [supportEmail, setSupportEmail] = useState('');
  const [supportDesc, setSupportDesc] = useState('');
  const navigate = useNavigate();
  const supportModalRef = useRef(null);
  const logoutModalRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    API.auth
      .me()
      .then((r) => {
        if (mounted && r) {
          setMe(r);
        }
      })
      .catch(() => {});
    return () => {
      mounted = false;
    };
  }, []);

  const handleSupportSubmit = (event) => {
    event.preventDefault();
    console.info('Support request', { email: supportEmail, desc: supportDesc });
    setSupportEmail('');
    setSupportDesc('');
    closeBootstrapModal(supportModalRef);
  };

  const handleLogout = async () => {
    try {
      await API.auth.logout();
    } catch (e) {
      // ignore network errors, proceed with client side logout
    }
    setMe({ auth: false, is_admin: false, user: '' });
    navigate('/');
  };

  const confirmLogout = async () => {
    closeBootstrapModal(logoutModalRef);
    await handleLogout();
  };

  return (
    <>
      <nav className='navbar navbar-expand-lg navbar-dark custom-navbar p-3 fixed-top shadow-sm'>
        <NavLink className='navbar-brand' to='/'>
          <Logo src='/fitter_logo.png' alt='Fitter' width={120} height={80} className='d-inline-block align-text-top' />
        </NavLink>

        <button
          className='navbar-toggler'
          type='button'
          data-bs-toggle='collapse'
          data-bs-target='#navbarNavDropdown'
          aria-controls='navbarNavDropdown'
          aria-expanded='false'
          aria-label='Toggle navigation'
        >
          <span className='navbar-toggler-icon' />
        </button>

        <div className='collapse navbar-collapse' id='navbarNavDropdown'>
          <ul className='navbar-nav'>
            <li className='nav-item'>
              <NavLink className='nav-link' to='/'>Inicio</NavLink>
            </li>

            <li className='nav-item dropdown'>
              <a className='nav-link dropdown-toggle' href='#!' id='navbarDropdownMenuLink' role='button' data-bs-toggle='dropdown' aria-expanded='false'>
                Productos y Servicios
              </a>
              <div className='dropdown-menu' aria-labelledby='navbarDropdownMenuLink'>
                <NavLink className='dropdown-item' to='/?categoria=Membership'>Membresias</NavLink>
                <NavLink className='dropdown-item' to='/?categoria=Personal%20Training'>Entrenamiento Personal</NavLink>
                <NavLink className='dropdown-item' to='/?categoria=Supplements'>Suplementos</NavLink>
                <NavLink className='dropdown-item' to='/?categoria=Merchandise'>Mercancia</NavLink>
              </div>
            </li>

            {me?.is_admin && (
              <>
                <li className='nav-item'>
                  <NavLink className='nav-link' to='/admin/productos'>Control de Inventario</NavLink>
                </li>
                <li className='nav-item'>
                  <NavLink className='nav-link' to='/admin/productos/nuevo'>Anadir Producto/Servicio</NavLink>
                </li>
              </>
            )}

            <li className='nav-item'>
              <a className='nav-link' href='#!' data-bs-toggle='modal' data-bs-target='#supportModal'>
                Soporte
              </a>
            </li>

            {!me?.auth ? (
              <li className='nav-item'>
                <NavLink className='nav-link' to='/login'>Acceso de Administrador</NavLink>
              </li>
            ) : (
              <li className='nav-item dropdown'>
                <a className='nav-link dropdown-toggle' href='#!' id='userMenuLink' role='button' data-bs-toggle='dropdown' aria-expanded='false'>
                  Hola, {me.user || 'Usuario'}
                </a>
                <ul className='dropdown-menu dropdown-menu-end' aria-labelledby='userMenuLink'>
                  <li>
                    <button className='dropdown-item' type='button' data-bs-toggle='modal' data-bs-target='#logoutModal'>
                      Cerrar sesion
                    </button>
                  </li>
                </ul>
              </li>
            )}
          </ul>

          <ul className='navbar-nav ms-auto'>
            <li className='nav-item'>
              <NavLink className='nav-link d-flex align-items-center' to='/carrito' aria-label='Carrito de Compras'>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  width='28'
                  height='28'
                  viewBox='0 0 24 24'
                  fill='none'
                  stroke='#ffffff'
                  strokeWidth='1.5'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  aria-hidden='false'
                  role='img'
                >
                  <title>Carrito de compras</title>
                  <circle cx='9' cy='21' r='1' fill='#ffffff' />
                  <circle cx='20' cy='21' r='1' fill='#ffffff' />
                  <path d='M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6' />
                </svg>
              </NavLink>
            </li>
          </ul>
        </div>
      </nav>

      <div className='modal fade' id='logoutModal' tabIndex={-1} aria-labelledby='logoutModalLabel' aria-hidden='true' ref={logoutModalRef}>
        <div className='modal-dialog modal-sm modal-dialog-centered'>
          <div className='modal-content'>
            <div className='modal-header'>
              <h5 className='modal-title' id='logoutModalLabel'>Confirmar cierre de sesion</h5>
              <button type='button' className='btn-close' data-bs-dismiss='modal' aria-label='Close' />
            </div>
            <div className='modal-body'>Esta seguro de que desea cerrar sesion?</div>
            <div className='modal-footer'>
              <button type='button' className='btn btn-secondary' data-bs-dismiss='modal'>Cancelar</button>
              <button type='button' className='btn btn-danger' onClick={confirmLogout}>Confirmar</button>
            </div>
          </div>
        </div>
      </div>

      <div className='modal fade' id='supportModal' tabIndex={-1} aria-labelledby='supportModalLabel' aria-hidden='true' ref={supportModalRef}>
        <div className='modal-dialog'>
          <div className='modal-content'>
            <div className='modal-header' style={{ backgroundColor: 'black' }}>
              <h1 className='modal-title fs-5' id='supportModalLabel' style={{ color: '#ffffff' }}>
                Contactar Soporte
              </h1>
              <button type='button' className='btn-close' data-bs-dismiss='modal' aria-label='Close' style={{ backgroundColor: '#ffffff' }} />
            </div>
            <div className='modal-body'>
              <strong>
                <a href='https://api.whatsapp.com/send/?phone=945747265&text&type=phone_number&app_absent=0' style={{ textDecoration: 'none' }}>
                  <i className='fa-brands fa-whatsapp' /> +1 (555) 123-4567
                </a>
              </strong>
              <br />
              <br />
              <strong>
                <a href='tel:+15551234567' style={{ textDecoration: 'none' }}>
                  <i className='fa-solid fa-phone' /> +1 (555) 123-4567 24/7
                </a>
              </strong>
              <br />
              <br />
              <strong>
                <a href='mailto:support@fittergym.com' style={{ textDecoration: 'none' }}>
                  <i className='fa-solid fa-envelope' /> support@fittergym.com
                </a>
              </strong>
              <br />
              <br />
              <br />
              <h4>Ticket de Soporte</h4>
              <form onSubmit={handleSupportSubmit}>
                <div className='form-group'>
                  <label htmlFor='ticketEmail'>Correo Electronico</label>
                  <input
                    className='form-control'
                    id='ticketEmail'
                    value={supportEmail}
                    onChange={(event) => setSupportEmail(event.target.value)}
                    placeholder='Introduce tu correo'
                  />
                </div>
                <div className='form-group'>
                  <label htmlFor='ticketDesc'>Describe tu problema</label>
                  <textarea
                    className='form-control'
                    id='ticketDesc'
                    rows={3}
                    value={supportDesc}
                    onChange={(event) => setSupportDesc(event.target.value)}
                  />
                </div>
                <button type='submit' className='btn btn-primary' style={{ marginTop: 8 }}>
                  Enviar
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
