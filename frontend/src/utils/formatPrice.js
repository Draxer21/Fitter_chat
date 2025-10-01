const pesoFormatter = new Intl.NumberFormat("es-CL", {
  style: "currency",
  currency: "CLP",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export const formatearPrecio = (valor) => {
  if (valor === null || valor === undefined) {
    return pesoFormatter.format(0);
  }

  const numero = typeof valor === "number" ? valor : Number.parseFloat(valor);
  if (!Number.isFinite(numero)) {
    return pesoFormatter.format(0);
  }

  const normalizado = Math.round(numero);
  return pesoFormatter.format(normalizado);
};

export const formatPrice = formatearPrecio;
