# Bitácora técnica – Ajuste FAQ (Retrieval + DIET)

## Objetivo
Asegurar que preguntas de horarios y pagos sean clasificadas como intent base `faq` (DIET),
mientras `ResponseSelector` resuelve el sub-intent (`faq/horarios`, `faq/pagos`) con alta precisión.

## Cambios realizados
- Ampliación semántica de NLU en:
  - `faq/horarios`: +10 ejemplos (hora, abren/cierran, fin de semana).
  - `faq/pagos`: +10 ejemplos (métodos, transferencia, cuotas, tarjeta/débito).
- Desambiguación de `soporte_general`:
  - Reescritura de ejemplos para que “pago” implique fallo explícito (rechazo/error/cobro doble/no se registró).
  - Micro-ajuste final: reforzado “falló mi último pago” para evitar confusión con “métodos de pago”.
  - Añadidos ejemplos directos de “tarjeta de débito” en `faq/pagos`.

## Evidencia (logs)
- validate_after_faq_clean.txt / train_after_faq_clean.txt / nlu_probe_after_faq_clean.txt
- validate_after_faq_micro.txt / train_after_faq_micro.txt / nlu_probe_after_faq_micro.txt

## Resultado (sonda final)
- “¿Puedo pagar con débito?” → `faq` (0.847) ✅
- “¿Cómo pago?” → `faq` (0.604) ✅
- “¿Aceptan transferencia?” → `faq` (0.852) ✅

## Estado
CERRADO / APROBADO.
