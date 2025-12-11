#!/usr/bin/env python3
"""
Calculadora de TMB (Tasa Metabólica Basal) y Calorías de Mantenimiento
Usa la fórmula de Harris-Benedict revisada

Uso:
    python scripts/calculate_tmb.py --peso 75 --altura 175 --edad 25 --sexo hombre --actividad moderado
"""
import argparse

def calcular_tmb(peso_kg: float, altura_cm: float, edad: int, sexo: str) -> float:
    """
    Calcula TMB usando Harris-Benedict
    
    Hombres: TMB = 88.362 + (13.397 × peso) + (4.799 × altura) - (5.677 × edad)
    Mujeres: TMB = 447.593 + (9.247 × peso) + (3.098 × altura) - (4.330 × edad)
    """
    if sexo.lower() in ['hombre', 'masculino', 'm', 'male']:
        tmb = 88.362 + (13.397 * peso_kg) + (4.799 * altura_cm) - (5.677 * edad)
    elif sexo.lower() in ['mujer', 'femenino', 'f', 'female']:
        tmb = 447.593 + (9.247 * peso_kg) + (3.098 * altura_cm) - (4.330 * edad)
    else:
        raise ValueError(f"Sexo '{sexo}' no válido. Use 'hombre' o 'mujer'.")
    
    return round(tmb, 2)


def calcular_mantenimiento(tmb: float, nivel_actividad: str) -> float:
    """
    Calcula calorías de mantenimiento según nivel de actividad
    
    Factores:
    - sedentario: 1.2 (poco o ningún ejercicio)
    - ligero: 1.375 (ejercicio 1-3 días/semana)
    - moderado: 1.55 (ejercicio 3-5 días/semana)
    - activo: 1.725 (ejercicio 6-7 días/semana)
    - muy_activo: 1.9 (ejercicio intenso diario)
    """
    factores = {
        'sedentario': 1.2,
        'ligero': 1.375,
        'moderado': 1.55,
        'activo': 1.725,
        'muy_activo': 1.9
    }
    
    factor = factores.get(nivel_actividad.lower())
    if not factor:
        raise ValueError(f"Nivel de actividad '{nivel_actividad}' no válido. Opciones: {list(factores.keys())}")
    
    return round(tmb * factor, 2)


def calcular_objetivos(mantenimiento: float) -> dict:
    """
    Calcula calorías para diferentes objetivos
    """
    return {
        'bajar_grasa': round(mantenimiento - 500, 2),
        'bajar_grasa_moderado': round(mantenimiento - 300, 2),
        'mantenimiento': mantenimiento,
        'hipertrofia_ligero': round(mantenimiento + 200, 2),
        'hipertrofia': round(mantenimiento + 400, 2)
    }


def main():
    parser = argparse.ArgumentParser(description='Calculadora de TMB y calorías de mantenimiento')
    parser.add_argument('--peso', type=float, required=True, help='Peso en kg')
    parser.add_argument('--altura', type=float, required=True, help='Altura en cm')
    parser.add_argument('--edad', type=int, required=True, help='Edad en años')
    parser.add_argument('--sexo', type=str, required=True, choices=['hombre', 'mujer', 'm', 'f'], 
                        help='Sexo biológico')
    parser.add_argument('--actividad', type=str, required=True, 
                        choices=['sedentario', 'ligero', 'moderado', 'activo', 'muy_activo'],
                        help='Nivel de actividad física')
    
    args = parser.parse_args()
    
    # Calcular TMB
    tmb = calcular_tmb(args.peso, args.altura, args.edad, args.sexo)
    
    # Calcular mantenimiento
    mantenimiento = calcular_mantenimiento(tmb, args.actividad)
    
    # Calcular objetivos
    objetivos = calcular_objetivos(mantenimiento)
    
    # Mostrar resultados
    print("\n" + "="*60)
    print("📊 RESULTADOS - CALORÍAS DIARIAS")
    print("="*60)
    print(f"\n🔹 Datos de entrada:")
    print(f"   Peso: {args.peso} kg")
    print(f"   Altura: {args.altura} cm")
    print(f"   Edad: {args.edad} años")
    print(f"   Sexo: {args.sexo}")
    print(f"   Actividad: {args.actividad}")
    
    print(f"\n🔹 TMB (Tasa Metabólica Basal):")
    print(f"   {tmb:.0f} kcal/día")
    
    print(f"\n🔹 Calorías de Mantenimiento:")
    print(f"   {mantenimiento:.0f} kcal/día")
    
    print(f"\n🔹 Objetivos recomendados:")
    print(f"   🔻 Bajar grasa (déficit 500 kcal):     {objetivos['bajar_grasa']:.0f} kcal/día")
    print(f"   🔻 Bajar grasa moderado (déficit 300): {objetivos['bajar_grasa_moderado']:.0f} kcal/día")
    print(f"   ⚖️  Mantenimiento:                      {objetivos['mantenimiento']:.0f} kcal/día")
    print(f"   🔺 Hipertrofia ligero (superávit 200): {objetivos['hipertrofia_ligero']:.0f} kcal/día")
    print(f"   🔺 Hipertrofia (superávit 400):        {objetivos['hipertrofia']:.0f} kcal/día")
    
    print("\n" + "="*60)
    print("💡 Tip: Usa estos valores para generar tu dieta con el chatbot")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
