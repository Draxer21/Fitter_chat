# 🤖 Fitter – Chatbot con Rasa

Proyecto de Título – Ingeniería en Informática (INACAP)  
Autores: Bryan Carreño / Diego Guzman  
Docente Guía: Iván Riquelme Nuñez

---

## 📌 Descripción
Fitter es un **chatbot en español** diseñado con **Rasa** para el contexto de gimnasios y centros deportivos.
Permite a los usuarios:
- Consultar rutinas personalizadas de entrenamiento.
- Obtener información de servicios.
- Registrar reservas de clases.
- Resolver dudas frecuentes.

El sistema se integra con un **backend en Flask/Django** y una interfaz web básica en **HTML/JS**, cumpliendo con la normativa chilena (Ley 21.719) sobre protección de datos.

---

## 🛠️ Tecnologías utilizadas
- **Python 3.10** (entorno base)
- **Rasa 3.6** (NLP / NLU)
- **Flask** (servidor backend para integración web)
- **HTML + JS** (interfaz de usuario simple)
- **GitHub** (versionamiento)

---

## 🧱 Pipeline local de aprendizaje a partir de videos y documentos
Como el proyecto está en desarrollo y se ejecuta en entornos locales, se recomienda el siguiente flujo para preparar la base de conocimientos antes de conectar el chatbot a producción:

1. **Ingesta de datos**  
   - Documentos: usar OCR o extractores locales (p. ej. `langchain`, `unstructured`, `pdfminer`, `python-docx`).  
   - Videos: generar transcripciones mediante modelos ASR como [Whisper](https://github.com/openai/whisper) o [Vosk](https://alphacephei.com/vosk/).  
   - Imágenes o presentaciones: aplicar OCR con `pytesseract` o `easyocr` cuando sea necesario.

2. **Limpieza y segmentación**  
   - Normalizar caracteres, eliminar ruido y dividir el texto en *chunks* semánticos (500–1 500 tokens).  
   - Guardar metadatos útiles (fuente, tema, autor, marca de tiempo) en archivos JSON/YAML para mantener trazabilidad local.

3. **Vectorización (embeddings)**  
   - Transformar cada fragmento en vectores con modelos locales como `text-embedding-3-large` (vía API) o alternativas open-source (`bge-large`, `intfloat/multilingual-e5-large`).  
   - Almacenar los vectores en una base como [ChromaDB](https://www.trychroma.com/), [FAISS](https://github.com/facebookresearch/faiss) o `qdrant` desplegada localmente mediante contenedores Docker.

4. **RAG (Retrieval-Augmented Generation)**  
   - Convertir la consulta del usuario en vector y recuperar los fragmentos más cercanos.  
   - Pasar contexto + pregunta al modelo generativo (Rasa Action Server puede orquestar esta llamada).  
   - Registrar logs de preguntas/respuestas para retroalimentar el dataset.

5. **Evaluación**  
   - Definir *ground truth* local y medir exactitud, F1, BLEU/ROUGE o evaluaciones humanas.  
   - Ajustar la segmentación y los umbrales de similitud hasta acercarse al 90 % de acierto en el dominio.

Este pipeline es compatible con un despliegue exclusivamente local y puede migrarse a servicios gestionados (Azure, Google Cloud, AWS) cuando el proyecto lo requiera.

---

## ✅ Próximos pasos sugeridos
- Automatizar la ingesta periódica de nuevos documentos mediante scripts en `backend/`.
- Documentar ejemplos de *chunks* y su metadata dentro del repositorio para facilitar pruebas.
- Preparar pruebas con usuarios internos que verifiquen la calidad de las respuestas antes de considerar un despliegue en la nube.

