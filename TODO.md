# TODO: Implement Simulated Card Payment in Shopping Cart

## Backend Changes
- [x] Refactor routes.py: Extract `validar_y_deducir()` function for stock validation and deduction without clearing cart.
- [x] Modify `/validar` endpoint to use `validar_y_deducir()` then clear cart.
- [x] Add `/pagar` endpoint: Validate simulated payment data, call `validar_y_deducir()`, return success.
- [x] Modify `/boleta` and `/boleta_json` to clear cart after generating receipt.

## Frontend API
- [x] Update apijs.js: Add `pagar` method to API.carrito.

## Frontend Components
- [x] Create PagoPage.jsx: Payment form with card number, expiration, CVV, name. Include client-side validation (Luhn, expiration, CVV).
- [x] Update CarritoPage.jsx: Change `buy()` to redirect to `/pago` instead of calling `validar`.

## Routing
- [x] Update App.js: Add route for `/pago` to PagoPage.

## Additional
- [x] Implement Luhn algorithm in JavaScript for card number validation.
- [x] Test the complete flow: cart → payment → boleta.
- [x] Ensure no card data is stored or logged.
