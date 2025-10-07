import { createContext, useContext, useEffect, useMemo, useState } from "react";

const SUPPORTED_LOCALES = ["es", "en"];

const MESSAGES = {
  es: {
    "nav.home": "Inicio",
    "nav.products": "Productos y Servicios",
    "nav.products.memberships": "Membresías",
    "nav.products.training": "Entrenamiento Personal",
    "nav.products.supplements": "Suplementos",
    "nav.products.merch": "Mercancía",
    "nav.support": "Soporte",
    "nav.logout": "Cerrar sesión",
    "nav.greeting": "Hola",
    "nav.admin.inventory": "Control de Inventario",
    "nav.admin.addProduct": "Añadir Producto/Servicio",
    "nav.logout.confirmTitle": "Confirmar cierre de sesión",
    "nav.logout.confirmBody": "¿Estás seguro de que deseas cerrar sesión?",
    "nav.logout.cancel": "Cancelar",
    "nav.logout.accept": "Confirmar",
    "nav.login.cta": "Inscríbete ya",
    "nav.language": "Idioma",
    "nav.language.switch": "ES / EN",
    "support.title": "Contactar Soporte",
    "support.ticket.title": "Ticket de Soporte",
    "support.ticket.email": "Correo electrónico",
    "support.ticket.desc": "Describe tu problema",
    "support.ticket.submit": "Enviar",
    "login.title": "Ingreso Usuario",
    "login.username.label": "Nombre de usuario",
    "login.username.placeholder": "tu_usuario",
    "login.password.label": "Contraseña",
    "login.password.placeholder": "Contraseña",
    "login.submit": "Iniciar Sesión",
    "login.loading": "Iniciando...",
    "login.required": "Debes ingresar usuario y contraseña",
    "login.error": "No fue posible iniciar sesión",
    "login.credentials.invalid": "Credenciales inválidas.",
    "login.loggedInAs": "Ingreso usuario",
    "login.logout": "Cerrar sesión",
    "login.noAccount": "¿No tienes cuenta?",
    "login.gotoRegister": "Regístrate aquí",
    "register.title": "Crear Cuenta",
    "register.fullname": "Nombre completo",
    "register.username": "Nombre de usuario",
    "register.email": "Correo electrónico",
    "register.password": "Contraseña",
    "register.password.confirm": "Confirmar contraseña",
    "register.submit": "Registrarse",
    "register.loading": "Registrando...",
    "register.haveAccount": "¿Ya tienes una cuenta?",
    "register.gotoLogin": "Inicia sesión aquí",
    "register.error.required": "Nombre, usuario, correo y password son obligatorios",
    "register.error.email": "El correo no es válido",
    "register.error.username": "El usuario debe tener entre 3 y 32 caracteres y solo contener letras, números, guion y guion bajo",
    "register.error.passwordLength": "La contraseña debe tener al menos 6 caracteres",
    "register.error.passwordMismatch": "Las contraseñas no coinciden",
    "register.success": "Registro exitoso, redirigiendo a iniciar sesión...",
  },
  en: {
    "nav.home": "Home",
    "nav.products": "Products & Services",
    "nav.products.memberships": "Memberships",
    "nav.products.training": "Personal Training",
    "nav.products.supplements": "Supplements",
    "nav.products.merch": "Merchandise",
    "nav.support": "Support",
    "nav.logout": "Log out",
    "nav.greeting": "Hello",
    "nav.admin.inventory": "Inventory Control",
    "nav.admin.addProduct": "Add Product/Service",
    "nav.logout.confirmTitle": "Confirm log out",
    "nav.logout.confirmBody": "Are you sure you want to sign out?",
    "nav.logout.cancel": "Cancel",
    "nav.logout.accept": "Confirm",
    "nav.login.cta": "Join now",
    "nav.language": "Language",
    "nav.language.switch": "ES / EN",
    "support.title": "Contact Support",
    "support.ticket.title": "Support ticket",
    "support.ticket.email": "Email address",
    "support.ticket.desc": "Describe your issue",
    "support.ticket.submit": "Submit",
    "login.title": "User Login",
    "login.username.label": "Username",
    "login.username.placeholder": "your_username",
    "login.password.label": "Password",
    "login.password.placeholder": "Password",
    "login.submit": "Log In",
    "login.loading": "Signing in...",
    "login.required": "Username and password are required",
    "login.error": "Unable to sign in",
    "login.credentials.invalid": "Invalid credentials.",
    "login.loggedInAs": "Signed in as",
    "login.logout": "Sign out",
    "login.noAccount": "Don't have an account?",
    "login.gotoRegister": "Sign up here",
    "register.title": "Create Account",
    "register.fullname": "Full name",
    "register.username": "Username",
    "register.email": "Email",
    "register.password": "Password",
    "register.password.confirm": "Confirm password",
    "register.submit": "Register",
    "register.loading": "Registering...",
    "register.haveAccount": "Already have an account?",
    "register.gotoLogin": "Log in here",
    "register.error.required": "Name, username, email and password are required",
    "register.error.email": "Email is not valid",
    "register.error.username": "Username must be 3-32 characters and only include letters, numbers, dash or underscore",
    "register.error.passwordLength": "Password must be at least 6 characters long",
    "register.error.passwordMismatch": "Passwords do not match",
    "register.success": "Registration successful, redirecting to login...",
  },
};

const LocaleContext = createContext(null);

const detectInitialLocale = () => {
    if (typeof window === "undefined") {
      return "es";
    }
    const stored = window.localStorage.getItem("app_locale");
    if (stored && SUPPORTED_LOCALES.includes(stored)) {
      return stored;
    }
    const nav = window.navigator?.language || "es";
    const normalized = nav.slice(0, 2).toLowerCase();
    return SUPPORTED_LOCALES.includes(normalized) ? normalized : "es";
};

export function LocaleProvider({ children }) {
  const [locale, setLocale] = useState(detectInitialLocale);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("app_locale", locale);
    }
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
    }
  }, [locale]);

  const value = useMemo(() => {
    const fallback = MESSAGES.es;
    const bundle = MESSAGES[locale] ?? fallback;
    return {
      locale,
      setLocale,
      t: (key) => bundle[key] ?? fallback[key] ?? key,
      messages: bundle,
    };
  }, [locale]);

  return <LocaleContext.Provider value={value}>{children}</LocaleContext.Provider>;
}

export function useLocale() {
  const ctx = useContext(LocaleContext);
  if (!ctx) {
    throw new Error("useLocale must be used within a LocaleProvider");
  }
  return ctx;
}

export { SUPPORTED_LOCALES };
