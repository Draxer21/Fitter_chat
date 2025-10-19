import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { API } from "../services/apijs";

const CartContext = createContext(null);

const emptyCart = {
  itemsMap: {},
  items: [],
  total: 0,
  count: 0,
};

const normalizeCartPayload = (payload) => {
  const source = payload?.carrito || payload?.cart || payload;
  if (!source || typeof source !== "object") {
    return { ...emptyCart };
  }

  const rawItems = source.items;
  let itemsMap = {};
  let itemsList = [];
  if (Array.isArray(rawItems)) {
    itemsList = rawItems.filter(Boolean);
    itemsMap = itemsList.reduce((acc, item) => {
      const key = item?.producto_id ?? item?.id ?? item?.slug ?? item?.nombre;
      if (key !== undefined && key !== null) {
        acc[key] = item;
      }
      return acc;
    }, {});
  } else if (rawItems && typeof rawItems === "object") {
    itemsMap = rawItems;
    itemsList = Object.values(rawItems);
  }

  const total = Number(source.total) || 0;
  const count = itemsList.reduce((acc, item) => acc + (Number(item?.cantidad) || 0), 0);

  return {
    itemsMap,
    items: itemsList,
    total,
    count,
  };
};

export function CartProvider({ children }) {
  const [cartState, setCartState] = useState({ ...emptyCart });
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState(null);
  const [initialized, setInitialized] = useState(false);
  const initRef = useRef(false);

  const applyCart = useCallback((payload) => {
    const normalized = normalizeCartPayload(payload);
    setCartState(normalized);
    return normalized;
  }, []);

  const refresh = useCallback(async () => {
    setStatus("loading");
    try {
      const data = await API.carrito.estado();
      const normalized = applyCart(data);
      setError(null);
      return normalized;
    } catch (err) {
      applyCart(null);
      setError(err);
      throw err;
    } finally {
      setInitialized(true);
      setStatus("ready");
    }
  }, [applyCart]);

  const mutate = useCallback(
    async (action, { silent = false } = {}) => {
      if (!silent) {
        setStatus("updating");
      }
      try {
        const data = await action();
        const normalized = applyCart(data);
        setError(null);
        return normalized;
      } catch (err) {
        setError(err);
        throw err;
      } finally {
        if (!silent) {
          setStatus("ready");
        }
        setInitialized(true);
      }
    },
    [applyCart]
  );

  const addItem = useCallback((id) => mutate(() => API.carrito.add(id)), [mutate]);
  const decrementItem = useCallback((id) => mutate(() => API.carrito.dec(id)), [mutate]);
  const removeItem = useCallback((id) => mutate(() => API.carrito.remove(id)), [mutate]);
  const clearCart = useCallback(() => mutate(() => API.carrito.clear()), [mutate]);

  useEffect(() => {
    if (initRef.current) {
      return;
    }
    initRef.current = true;
    refresh().catch(() => {
      /* allow silent failure on first load */
    });
  }, [refresh]);

  const value = useMemo(
    () => ({
      cart: cartState,
      items: cartState.items,
      itemsMap: cartState.itemsMap,
      total: cartState.total,
      itemCount: cartState.count,
      status,
      loading: status === "loading" && !initialized,
      updating: status === "updating",
      initialized,
      error,
      refresh,
      addItem,
      decrementItem,
      removeItem,
      clearCart,
    }),
    [cartState, status, initialized, error, refresh, addItem, decrementItem, removeItem, clearCart]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return ctx;
}
