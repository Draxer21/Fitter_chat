"""
Script para probar el flujo completo de pago con MercadoPago
"""
from backend.app import create_app

app = create_app()

with app.app_context():
    print("=" * 60)
    print("VERIFICACIÓN DE INTEGRACIÓN MERCADOPAGO")
    print("=" * 60)
    
    # Verificar que el blueprint de pagos esté registrado
    print("\n1. Verificando blueprints registrados...")
    blueprints = [bp.name for bp in app.blueprints.values()]
    
    if 'payments' in blueprints:
        print("   ✓ Blueprint 'payments' registrado")
    else:
        print("   ❌ Blueprint 'payments' NO registrado")
    
    if 'carrito' in blueprints:
        print("   ✓ Blueprint 'carrito' registrado")
    else:
        print("   ❌ Blueprint 'carrito' NO registrado")
    
    # Verificar rutas
    print("\n2. Verificando rutas importantes...")
    routes = {}
    for rule in app.url_map.iter_rules():
        routes[rule.endpoint] = str(rule)
    
    rutas_importantes = [
        ('carrito.procesar_pago', '/carrito/pagar'),
        ('carrito.payment_success', '/carrito/payment/success'),
        ('carrito.payment_failure', '/carrito/payment/failure'),
        ('carrito.payment_pending', '/carrito/payment/pending'),
        ('payments.create_preference', '/api/payments/create-preference'),
        ('payments.webhook', '/api/payments/webhook'),
    ]
    
    for endpoint, expected_path in rutas_importantes:
        if endpoint in routes:
            print(f"   ✓ {endpoint}: {routes[endpoint]}")
        else:
            print(f"   ❌ {endpoint} NO encontrado (esperado: {expected_path})")
    
    # Verificar configuración
    print("\n3. Verificando configuración de MercadoPago...")
    access_token = app.config.get('MERCADOPAGO_ACCESS_TOKEN')
    public_key = app.config.get('MERCADOPAGO_PUBLIC_KEY')
    frontend_url = app.config.get('FRONTEND_URL')
    
    if access_token and access_token != 'your_access_token_here':
        print(f"   ✓ MERCADOPAGO_ACCESS_TOKEN configurado")
    else:
        print(f"   ❌ MERCADOPAGO_ACCESS_TOKEN no configurado")
    
    if public_key and public_key != 'your_public_key_here':
        print(f"   ✓ MERCADOPAGO_PUBLIC_KEY configurado")
    else:
        print(f"   ❌ MERCADOPAGO_PUBLIC_KEY no configurado")
    
    print(f"   ✓ FRONTEND_URL: {frontend_url}")
    
    print("\n" + "=" * 60)
    print("✓ VERIFICACIÓN COMPLETA")
    print("=" * 60)
    print("\nURLs de retorno configuradas:")
    print(f"  Success: {frontend_url}/carrito/payment/success")
    print(f"  Failure: {frontend_url}/carrito/payment/failure")
    print(f"  Pending: {frontend_url}/carrito/payment/pending")
    print("\nAhora puedes:")
    print("1. Iniciar el servidor con: python backend/app.py")
    print("2. Ir a http://localhost:5000/carrito/tienda")
    print("3. Agregar productos al carrito")
    print("4. Hacer clic en 'Hacer Compra'")
    print("5. Serás redirigido a MercadoPago")
    print("=" * 60)
