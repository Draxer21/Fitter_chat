"""
Script de prueba para verificar la conexión con MercadoPago
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_mercadopago_connection():
    """Probar la conexión con MercadoPago"""
    print("=" * 60)
    print("PRUEBA DE CONEXIÓN CON MERCADOPAGO")
    print("=" * 60)
    
    # Verificar credenciales
    access_token = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
    public_key = os.getenv('MERCADOPAGO_PUBLIC_KEY')
    
    print("\n1. Verificando credenciales...")
    assert access_token and access_token != 'your_access_token_here', "MERCADOPAGO_ACCESS_TOKEN no está configurado"
    else:
        # Mostrar solo los primeros y últimos caracteres
        masked_token = access_token[:10] + "..." + access_token[-10:] if len(access_token) > 20 else "***"
        print(f"   ✓ Access Token: {masked_token}")
    
    assert public_key and public_key != 'your_public_key_here', "MERCADOPAGO_PUBLIC_KEY no está configurado"
    else:
        masked_key = public_key[:10] + "..." + public_key[-10:] if len(public_key) > 20 else "***"
        print(f"   ✓ Public Key: {masked_key}")
    
    # Probar SDK
    print("\n2. Probando SDK de MercadoPago...")
    try:
        import mercadopago
        sdk = mercadopago.SDK(access_token)
        print("   ✓ SDK inicializado correctamente")
        
        # Probar una llamada a la API (obtener métodos de pago)
        print("\n3. Probando conexión con la API...")
        payment_methods = sdk.payment_methods().list_all()
        
        assert payment_methods["status"] == 200, f"Error al conectar: Status {payment_methods['status']}"
        if payment_methods["status"] == 200:
            methods_count = len(payment_methods.get("response", []))
            print(f"   ✓ Conexión exitosa - {methods_count} métodos de pago disponibles")
            
            # Mostrar algunos métodos de pago
            if methods_count > 0:
                print("\n   Métodos de pago disponibles:")
                for method in payment_methods["response"][:5]:
                    print(f"   - {method['id']}: {method['name']}")
                if methods_count > 5:
                    print(f"   ... y {methods_count - 5} más")
            
            return
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        assert False

if __name__ == "__main__":
    success = test_mercadopago_connection()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ TODAS LAS PRUEBAS PASARON")
        print("\nPuedes usar la integración de MercadoPago!")
        print("\nPróximos pasos:")
        print("1. Configura el webhook en: https://www.mercadopago.cl/developers/panel/webhooks")
        print("2. Usa las tarjetas de prueba para testing")
        print("3. Revisa la documentación en docs/MERCADOPAGO.md")
    else:
        print("❌ ALGUNAS PRUEBAS FALLARON")
        print("\nVerifica:")
        print("1. Que las credenciales sean correctas")
        print("2. Que estés usando credenciales de Sandbox para testing")
        print("3. Tu conexión a internet")
    print("=" * 60)
