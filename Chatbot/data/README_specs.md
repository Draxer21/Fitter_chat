# Generador de datos NLU

Este directorio reúne especificaciones (`data/specs/*.yml`) para generar cientos o miles de ejemplos por intent usando plantillas y listas de sinónimos.

## Cómo funciona

1. Cada archivo en `data/specs/` describe **un intent** con:
   - `intent`: nombre exacto del intent en `domain.yml`.
   - `templates`: frases con marcadores `{slot}` que se expanden con los valores listados.
   - `slots`: diccionario de listas de valores para cada marcador.
   - `static_examples` (opcional): frases fijas que siempre se incluyen.

   Ejemplo resumido:

   ```yaml
   intent: solicitar_rutina
   templates:
     - "Necesito una rutina {modality} para {goal} considerando {condition}"
   slots:
     modality: [completa, de fuerza, …]
     goal: [bajar grasa, ganar masa muscular, …]
     condition: [tengo hipertensión, …]
   static_examples:
     - "¿Puedes armarme una rutina personalizada?"
   ```

2. El script `python tools/generate_nlu.py` combina plantillas y valores, deduplica y toma hasta `--per-intent` ejemplos por intent. Puedes ajustar la semilla con `--seed`.

## Pasos para generar 2 000 ejemplos por intent

```bash
cd Chatbot
python tools/generate_nlu.py \
    --spec-dir data/specs \
    --output data/generated/nlu_generated.yml \
    --per-intent 2000
```

El archivo resultante usa formato Rasa 3.x (`version` + bloque `nlu`). Puedes:

- Reemplazar `data/nlu.yml` por el archivo generado.
- O bien **fusionar** los ejemplos generados con tus datos existentes.

## Buenas prácticas

- Revisa el archivo generado con `rasa data validate`.
- Mezcla frases sintéticas con ejemplos reales etiquetados.
- Amplía y ajusta las listas de `slots` cuando detectes confusiones (ver `results/intent_errors.json` tras `rasa test nlu`).
- Divide los specs por tema para facilitar revisiones (rutinas, reservas, soporte, small talk, etc.).

Con este flujo puedes mantener un dataset amplio y homogéneo para todos los intents, no solo los relacionados con rutinas.
