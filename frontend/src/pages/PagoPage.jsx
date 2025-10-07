import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API } from "../services/apijs";

function luhnCheck(cardNumber) {
  let sum = 0;
  let shouldDouble = false;
  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber.charAt(i));
    if (shouldDouble) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }
    sum += digit;
    shouldDouble = !shouldDouble;
  }
  return sum % 10 === 0;
}

export default function PagoPage() {
  const [form, setForm] = useState({ card_num: "", exp: "", cvv: "", name: "" });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const validate = () => {
    const errs = {};
    const cardNum = form.card_num.replace(/\s/g, "");
    if (!cardNum || !/^\d{13,19}$/.test(cardNum) || !luhnCheck(cardNum)) {
      errs.card_num = "Número de tarjeta inválido.";
    }
    if (!form.exp || !/^\d{2}\/\d{2}$/.test(form.exp)) {
      errs.exp = "Fecha de expiración inválida (MM/YY).";
    } else {
      const [mm, yy] = form.exp.split("/");
      const expDate = new Date(2000 + parseInt(yy), parseInt(mm) - 1);
      if (expDate < new Date()) {
        errs.exp = "Tarjeta expirada.";
      }
    }
    if (!form.cvv || !/^\d{3}$/.test(form.cvv)) {
      errs.cvv = "CVV inválido.";
    }
    if (!form.name.trim()) {
      errs.name = "Nombre del titular requerido.";
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      await API.carrito.pagar(form);
      navigate("/boleta");
    } catch (err) {
      setErrors({ general: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 20, maxWidth: 400, margin: "auto" }}>
      <h2>Información de Pago</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label>Número de Tarjeta:</label>
          <input
            type="text"
            name="card_num"
            value={form.card_num}
            onChange={handleChange}
            placeholder="1234 5678 9012 3456"
            required
          />
          {errors.card_num && <div style={{ color: "red" }}>{errors.card_num}</div>}
        </div>
        <div>
          <label>Fecha de Expiración (MM/YY):</label>
          <input
            type="text"
            name="exp"
            value={form.exp}
            onChange={handleChange}
            placeholder="12/25"
            required
          />
          {errors.exp && <div style={{ color: "red" }}>{errors.exp}</div>}
        </div>
        <div>
          <label>CVV:</label>
          <input
            type="text"
            name="cvv"
            value={form.cvv}
            onChange={handleChange}
            placeholder="123"
            required
          />
          {errors.cvv && <div style={{ color: "red" }}>{errors.cvv}</div>}
        </div>
        <div>
          <label>Nombre del Titular:</label>
          <input
            type="text"
            name="name"
            value={form.name}
            onChange={handleChange}
            placeholder="Juan Pérez"
            required
          />
          {errors.name && <div style={{ color: "red" }}>{errors.name}</div>}
        </div>
        {errors.general && <div style={{ color: "red" }}>{errors.general}</div>}
        <button type="submit" disabled={loading}>
          {loading ? "Procesando..." : "Pagar"}
        </button>
      </form>
    </div>
  );
}
