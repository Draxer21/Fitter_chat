import { NavLink, useNavigate } from 'react-router-dom';
import { useRef, useState } from 'react';
import Logo from '../components/Logo';
import { useLocale } from '../contexts/LocaleContext';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import { useFontSize } from '../contexts/FontSizeContext';

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
  const { t, locale, setLocale } = useLocale();
  const { user, isAdmin, isAuthenticated, logout: logoutUser } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { increase, decrease, reset, scale } = useFontSize();
  const [supportEmail, setSupportEmail] = useState('');
  const [supportDesc, setSupportDesc] = useState('');
  const navigate = useNavigate();
  const supportModalRef = useRef(null);
  const logoutModalRef = useRef(null);
  const collapseRef = useRef(null);

  const handleSupportSubmit = (event) => {
    event.preventDefault();
    console.info('Support request', { email: supportEmail, desc: supportDesc });
    setSupportEmail('');
    setSupportDesc('');
    closeBootstrapModal(supportModalRef);
  };

  const handleLogout = async () => {
    await logoutUser();
    navigate('/');
  };

  const confirmLogout = async () => {
    closeBootstrapModal(logoutModalRef);
    await handleLogout();
  };


  const closeNavbarCollapse = () => {
    const Collapse = window.bootstrap && window.bootstrap.Collapse;
    if (!Collapse || !collapseRef.current) return;
    let instance = Collapse.getInstance(collapseRef.current);
    if (!instance) {
      instance = new Collapse(collapseRef.current, { toggle: false });
    }
    instance.hide();
  };

  const handleCategoryNavigate = (category) => {
    const query = category ? `?categoria=${encodeURIComponent(category)}` : '';
    navigate(`/catalogo${query}`);
    closeNavbarCollapse();
  };

  const toggleLocale = () => {
    setLocale(locale === 'es' ? 'en' : 'es');
  };

  const handleToggleTheme = () => {
    toggleTheme();
    closeNavbarCollapse();
  };

  const currentUserLabel = user?.username || user?.full_name || user?.email || 'Usuario';

  return (
    <>
      <nav className='navbar navbar-expand-lg custom-navbar p-3 fixed-top shadow-sm'>
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
          aria-label='Alternar navegación'
        >
          <span className='navbar-toggler-icon' />
        </button>

        <div className='collapse navbar-collapse' id='navbarNavDropdown' ref={collapseRef}>
          <ul className='navbar-nav'>
            <li className='nav-item'>
              <NavLink className='nav-link' to='/'>{t('nav.home')}</NavLink>
            </li>

            <li className='nav-item dropdown'>
              <button className='nav-link dropdown-toggle' id='navbarDropdownMenuLink' type="button" data-bs-toggle='dropdown' aria-expanded='false'>
                {t('nav.products')}
              </button>
              <div className='dropdown-menu' aria-labelledby='navbarDropdownMenuLink'>
                <NavLink className='dropdown-item' to='/catalogo' onClick={closeNavbarCollapse}>
                  Catálogo completo
                </NavLink>
                <button type='button' className='dropdown-item' onClick={() => handleCategoryNavigate('Membership')}>
                  {t('nav.products.memberships')}
                </button>
                <button type='button' className='dropdown-item' onClick={() => handleCategoryNavigate('Personal Training')}>
                  {t('nav.products.training')}
                </button>
                <button type='button' className='dropdown-item' onClick={() => handleCategoryNavigate('Supplements')}>
                  {t('nav.products.supplements')}
                </button>
                <button type='button' className='dropdown-item' onClick={() => handleCategoryNavigate('Merchandise')}>
                  {t('nav.products.merch')}
                </button>
              </div>
            </li>

            {isAdmin && (
              <>
                <li className='nav-item'>
                  <NavLink className='nav-link' to='/admin/productos'>{t('nav.admin.inventory')}</NavLink>
                </li>
                <li className='nav-item'>
                  <NavLink className='nav-link' to='/admin/productos/nuevo'>{t('nav.admin.addProduct')}</NavLink>
                </li>
                <li className='nav-item'>
                  <NavLink className='nav-link' to='/admin/ventas'>Panel de ventas</NavLink>
                </li>
              </>
            )}

            <li className='nav-item'>
              <button className='nav-link btn btn-link p-0 text-start' type="button" data-bs-toggle='modal' data-bs-target='#supportModal'>
                {t('nav.support')}
              </button>
            </li>

            {isAuthenticated && (
              <li className='nav-item dropdown'>
                <button className='nav-link dropdown-toggle' id='userMenuLink' type="button" data-bs-toggle='dropdown' aria-expanded='false'>
                  {t('nav.greeting')}, {currentUserLabel}
                </button>
                <ul className='dropdown-menu dropdown-menu-end' aria-labelledby='userMenuLink'>
                  <li>
                    <NavLink className='dropdown-item' to='/cuenta/perfil' onClick={closeNavbarCollapse}>
                      Mi información
                    </NavLink>
                  </li>
                  <li>
                    <NavLink className='dropdown-item' to='/cuenta/seguridad' onClick={closeNavbarCollapse}>
                      Seguridad (MFA)
                    </NavLink>
                  </li>
                  <li><hr className='dropdown-divider' /></li>
                  <li>
                    <button className='dropdown-item' type='button' data-bs-toggle='modal' data-bs-target='#logoutModal'>
                      {t('nav.logout')}
                    </button>
                  </li>
                </ul>
              </li>
            )}
          </ul>

          <ul className='navbar-nav ms-auto align-items-center gap-2'>
            <li className='nav-item'>
              <button
                type='button'
                className='btn btn-outline-secondary btn-sm'
                onClick={handleToggleTheme}
                aria-pressed={theme === 'dark'}
              >
                {theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
              </button>
            </li>
            <li className='nav-item'>
              <button type='button' className='btn btn-outline-secondary btn-sm' onClick={toggleLocale}>
                {locale === 'es' ? 'EN' : 'ES'}
              </button>
            </li>
            <li className='nav-item d-flex align-items-center gap-1'>
              <button type='button' className='btn btn-outline-secondary btn-sm' onClick={decrease} aria-label='Disminuir tamaño de letra'>
                A-
              </button>
              <button type='button' className='btn btn-outline-secondary btn-sm' onClick={increase} aria-label='Aumentar tamaño de letra'>
                A+
              </button>
              <button type='button' className='btn btn-outline-secondary btn-sm' onClick={reset} aria-label='Restablecer tamaño de letra'>
                {Math.round(scale * 100)}%
              </button>
            </li>
            {!isAuthenticated && (
              <li className='nav-item me-2'>
                <NavLink className='btn btn-warning rounded-pill' to='/login'>{t('nav.login.cta')}</NavLink>
              </li>
            )}
            <li className='nav-item'>
              <NavLink className='nav-link d-flex align-items-center' to='/carrito' aria-label='Carrito de Compras'>
                <svg
                  xmlns='http://www.w3.org/2000/svg'
                  width='28'
                  height='28'
                  viewBox='0 0 24 24'
                  fill='white'
                  stroke='white'
                  strokeWidth='0'
                  strokeLinecap='round'
                  strokeLinejoin='round'
                  aria-hidden='true'
                  role='img'
                >
                  <title>Carrito de compras</title>
                  <circle cx='9' cy='21' r='1' />
                  <circle cx='20' cy='21' r='1' />
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
              <h5 className='modal-title' id='logoutModalLabel'>{t('nav.logout.confirmTitle')}</h5>
              <button type='button' className='btn-close' data-bs-dismiss='modal' aria-label='Close' />
            </div>
            <div className='modal-body'>{t('nav.logout.confirmBody')}</div>
            <div className='modal-footer'>
              <button type='button' className='btn btn-secondary' data-bs-dismiss='modal'>{t('nav.logout.cancel')}</button>
              <button type='button' className='btn btn-danger' onClick={confirmLogout}>{t('nav.logout.accept')}</button>
            </div>
          </div>
        </div>
      </div>

      <div className='modal fade' id='supportModal' tabIndex={-1} aria-labelledby='supportModalLabel' aria-hidden='true' ref={supportModalRef}>
        <div className='modal-dialog'>
          <div className='modal-content'>
            <div className='modal-header' style={{ backgroundColor: 'black' }}>
              <h1 className='modal-title fs-5' id='supportModalLabel' style={{ color: '#ffffff' }}>
                {t('support.title')}
              </h1>
              <button type='button' className='btn-close' data-bs-dismiss='modal' aria-label='Close' style={{ backgroundColor: '#ffffff' }} />
            </div>
            <div className='modal-body'>
              <strong>
                <a href='https://api.whatsapp.com/send/?phone=56950117527&text&type=phone_number&app_absent=0' style={{ textDecoration: 'none' }}>
                  <i className='fa-brands fa-whatsapp' /> +56 9 5011-7527 (WhatsApp)
                </a>
              </strong>
              <br />
              <br />
              <strong>
                <a href='tel:+56972791541' style={{ textDecoration: 'none' }}>
                  <i className='fa-solid fa-phone' /> +56 9 7279 1541 24/7
                </a>
              </strong>
              <br />
              <br />
              <strong>
                <a href='mailto:supporfitter@gmail.com' style={{ textDecoration: 'none' }}>
                  <i className='fa-solid fa-envelope' /> supporfitter@gmail.com
                </a>
              </strong>
              <br />
              <br />
              <br />
              <h4>{t('support.ticket.title')}</h4>
              <form onSubmit={handleSupportSubmit}>
                <div className='form-group'>
                  <label htmlFor='ticketEmail'>{t('support.ticket.email')}</label>
                  <input
                    className='form-control'
                    id='ticketEmail'
                    value={supportEmail}
                    onChange={(event) => setSupportEmail(event.target.value)}
                    placeholder='name@example.com'
                  />
                </div>
                <div className='form-group'>
                  <label htmlFor='ticketDesc'>{t('support.ticket.desc')}</label>
                  <textarea
                    className='form-control'
                    id='ticketDesc'
                    rows={3}
                    value={supportDesc}
                    onChange={(event) => setSupportDesc(event.target.value)}
                  />
                </div>
                <button type='submit' className='btn btn-primary' style={{ marginTop: 8 }}>
                  {t('support.ticket.submit')}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
