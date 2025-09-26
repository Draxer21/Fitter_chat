import { useEffect, useState } from "react";
import { API } from "../services/apijs";
import "../styles/legacy/carrito/style_carrito.css";

export default function CarritoPage() {
  const [state, setState] = useState({ items:{}, total:0 });
  const load = () => API.carrito.estado().then(setState);
  useEffect(()=>{ load(); }, []);

  const inc  = (id) => API.carrito.add(id).then(load);
  const dec  = (id) => API.carrito.dec(id).then(load);
  const del  = (id) => API.carrito.remove(id).then(load);
  const cls  = ()    => API.carrito.clear().then(load);
  const buy  = async () => {
    const r = await API.carrito.validar();
    if (r?.errores) alert(r.errores.join("\n"));
    else if (r?.error) alert(r.error);
    else window.location.href = "/boleta";
  };

  const rows = Object.values(state.items || {});
  return (
    <div className="container" style={{maxWidth: 1200, margin: "0 auto"}}>
      <div className="alert" role="alert" style={{backgroundColor: "rgba(0,0,0,0.904)"}}>
        <div className="table-responsive">
          <table className="table table-bordered">
            <thead>
              <tr><th scope="row" colSpan={5} className="text-center">CARRITO</th></tr>
              <tr>
                <th>NOMBRE</th><th>CANTIDAD</th><th>PRECIO UNITARIO</th>
                <th>PRECIO TOTAL DEL PRODUCTO</th><th>ELIMINAR/AGREGAR</th>
              </tr>
            </thead>
            <tbody>
              {rows.length>0 ? rows.map(v=>(
                <tr key={v.producto_id}>
                  <td>{v.nombre}</td>
                  <td>{v.cantidad}</td>
                  <td>${v.precio_unitario.toFixed(2)}</td>
                  <td>${v.acumulado.toFixed(2)}</td>
                  <td>
                    <button onClick={()=>dec(v.producto_id)} className="badge btn btn-dark badge-dark">-</button>{" "}
                    <button onClick={()=>inc(v.producto_id)} className="badge btn btn-dark badge-dark">+</button>{" "}
                    <button onClick={()=>del(v.producto_id)} className="badge btn btn-danger">x</button>
                  </td>
                </tr>
              )) : (
                <tr><td colSpan={5}><div className="alert alert-danger text-center">Sin Productos</div></td></tr>
              )}
              <tr>
                <th scope="row">Total:</th>
                <td colSpan={4}>${Number(state.total||0).toFixed(2)}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <hr />
      </div>

      <div className="row text-center">
        <div className="col-6"><button onClick={cls} className="btn btn-danger">Limpiar</button></div>
        <div className="col-6"><button onClick={buy} className="btn btn-success">Hacer Compra</button></div>
      </div>
    </div>
  );
}
