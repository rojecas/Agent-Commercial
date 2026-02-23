# Decisiones de Arquitectura de Base de Datos
**Proyecto:** Agente Conversacional Multicanal
**Propósito:** Resumir las conclusiones y el diseño de la base de datos (DB) del Agente, y cómo interactúa con los datos existentes de la empresa.
**Fecha:** Febrero 2026

---

## 1. El Concepto de "Mixin"
En Programación Orientada a Objetos (OOP), un **Mixin** es una clase que contiene métodos o atributos diseñados para ser utilizados por otras clases, sin ser la clase padre de esas otras clases. El nombre viene de "Mix in" (mezclar adentro). 

A diferencia de la herencia tradicional (donde un `Gato` hereda de `Animal`), un Mixin es como un paquete de habilidades adicionales que le "pegas" a una clase. 
Por ejemplo: Creamos la tabla `User`. Luego le "mezclamos" el `AuditableMixin` (que le da `created_at` y `updated_at`) y el `SoftDeleteMixin` (que le da `is_deleted`). Así evitamos repetir ese mismo código en las tablas `Conversation`, `Message`, `Lead`, etc.

---

## 2. El Valor del Agente: Asesoría vs. Formulario
El agente **no debe ser un formulario glorificado**. Su valor real radica en la **Venta Consultiva (Asesoría Técnica)**.
Si el cliente dice: *"Necesito leer pH en muestras de agua cruda de pozo"*, el agente debe responder: *"Para agua cruda con alta turbidez, le recomiendo nuestro Medidor de pH Serie X con electrodo de unión de teflón, ya que evita obstrucciones. ¿Le gustaría que le envíe la ficha técnica de este equipo y de la Serie Y como alternativa?"*

Para lograr esto, el Agente necesita leer los productos que vende INASC.

---

## 3. Integración con la Base de Datos de Productos (App Web vs. Agente)
Tenemos dos bases de datos conviviendo:
1.  **BD de la App Web (PHP/MySQL):** Contiene el catálogo real de productos, categorías, fichas técnicas, precios, etc. Esta es la *fuente de la verdad*.
2.  **BD del Agente (MySQL/PostgreSQL):** La que estamos diseñando para guardar conversaciones, leads, logs y telemetría.

### ¿Cómo gestionamos las solicitudes entre ambas?
**Regla de Oro:** El Agente NO debe modificar el catálogo de productos jamás. Solo debe **leerlo**.
Tenemos varias opciones de integración, cada una con distintos impactos en la arquitectura:

#### Opción A (API REST Proxy)
La aplicación PHP expone un endpoint seguro (ej. `inasc.com.co/api/productos/buscar?q=medidor+ph+agua+cruda`). El Agente de Python tiene una herramienta/skill que hace una petición HTTP a esta URL, lee el JSON devuelto y el LLM formula la respuesta.
*   **Impacto:** Bajo acoplamiento. Si alguna vez cambias la base de datos de PHP por otra tecnología, el Agente no se entera ni se rompe mientras la API siga respondiendo igual.
*   **Contras:** Dependidez de que el desarrollador de PHP cree y mantenga ese endpoint. Latencia de red extra.

#### Opción B (Acceso Directo de Lectura SQL)
En nuestro archivo `.env`, configuramos una segunda conexión de base de datos (`DB_CATALOG_HOST`, `DB_CATALOG_USER`). El Agente de Python se conecta directamente a la MySQL de PHP con un usuario de **Solo Lectura** y hace consultas crudas (`SELECT * FROM productos WHERE descripcion LIKE '%pH%'`).
*   **Impacto:** Altísimo rendimiento y cero dependencias del equipo web. El Bot es autosuficiente para explorar el catálogo.
*   **Sobre tu preocupación (Colisiones):** Tienes toda la razón en que los motores de bases de datos relacionales (MySQL/PostgreSQL) están diseñados para manejar miles de lecturas simultáneas (Concurrencia). Una consulta `SELECT` no bloquea la tabla. No hay riesgo de colisión ni de tumbar la página web a menos que escribas una consulta SQL terriblemente ineficiente que consuma el 100% de la CPU. El verdadero riesgo aquí es el "Fuerte Acoplamiento": si alguien cambia el nombre de la columna `precio` a `valor` en el PHP, el Agente se rompe de inmediato.

#### Opción C (RAG / Retrieval-Augmented Generation / Vector Database)
*(Esta es la arquitectura "State of the Art" recomendada masivamente por OpenAI y Meta para Asesores Comerciales IA)*

Los LLMs (ChatGPT) no entienden bien las palabras exactas, entienden **"Conceptos Matemáticos"** (Semántica). Si un cliente escribe *"Busco un equipo para medir acidez en efluentes"*, una base de datos MySQL tradicional (Opciones A y B) fallará miserablemente porque las palabras "acidez" y "efluentes" podrían no existir en la fila del producto (donde quizás dice "pH" y "aguas residuales").

**¿Cómo funciona RAG?**
1.  **Ingesta (Una vez al día/semana):** Un pequeño script de Python se conecta a tu MySQL de PHP, lee todos los productos (Nombre, Ficha Técnica, Uso) y los envía a un modelo de IA especializado (ej. `text-embedding-3`). Este modelo convierte todo el texto de la ficha técnica en un Array de miles de números (un **Vector**).
2.  **Almacenamiento Vectorial:** Guardamos esos números en una Base de Datos especial (ej. *Pinecone*, *ChromaDB*, o *Qdrant*).
3.  **La Pregunta del Cliente:** Cuando el cliente pregunta *"¿Qué me sirve para la acidez de mis efluentes?"*, el Agente convierte silenciosamente ESA frase en otro Vector matemático.
4.  **Búsqueda Geométrica (El truco de Magia):** En lugar de buscar palabras clave (`LIKE %...%`), la Base de Datos Vectorial mide la "Distancia Geométrica" entre el concepto del cliente y los conceptos de todos los productos. Como matemáticamente *Acidez = pH* y *Efluente = Agua Residual*, los vectores estarán muy cerca flotando en el espacio multidimensional.
5.  **El Resultado:** La base de datos vectorial le devuelve al Agente de forma instantánea: *"Los productos más cercanos a esta idea abstracta son el SKU 101 y SKU 204"*.
6.  **La Asesoría:** El LLM toma esa respuesta y dice: *"Entiendo su necesidad con los efluentes. Le recomiendo el Medidor Serie X (SKU 101)..."*

*   **Impacto:** Es la única forma de que el bot "piense" como un ingeniero de ventas real, asociando problemas abstractos con soluciones técnicas.
*   **Contras:** Requiere montar una pieza de infraestructura adicional (La Vector DB) y consume unos centavos de OpenAI cada vez que se indexa el catálogo.

---

## 4. Almacenamiento de Recomendaciones en la BD del Agente
Una vez que el Agente sugiere un equipo (ej. "Medidor de pH Serie X"), ¿dónde guardamos esa información comercialmente valiosa?

**No** se debe guardar como un simple texto en un campo de la tabla `users` o `leads`, ya que un usuario puede recibir 5 recomendaciones distintas. La forma correcta es usar una tabla de **Relación Muchos a Muchos** (Intermedia) o una tabla de **Cotizaciones/Oportunidades**.

### Nuevo Diseño Propuesto (Tablas Adicionales)

1.  **Tabla `leads_opportunities` (Oportunidades de Venta):**
    Representa el interés específico de un usuario en una interacción.
    - `id` (PK)
    - `user_id` (FK a la tabla Users)
    - `status` (Ej: 'qualified', 'needs_expert', 'closed')
    - `problem_statement` (El dolor del cliente: "Necesita medir pH en agua cruda")

2.  **Tabla `opportunity_product_recommendations` (Productos Recomendados):**
    Guarda exactamente qué productos se le ofrecieron para solucionar ese problema.
    - `id` (PK)
    - `opportunity_id` (FK a leads_opportunities)
    - `product_sku` o `product_id` (ID del producto en la Base de Datos de la Web PHP)
    - `product_name` (Nombre del equipo)
    - `justification` (Por qué el bot lo recomendó: "Ideal para alta turbidez")

### Flujo de Datos Actualizado
1. El usuario explica el problema.
2. El Agente usa una herramienta (*Tool*) para buscar en el Catálogo de Productos (vía API o lectura SQL a la BD de PHP).
3. El Agente le explica verbalmente la solución al usuario.
4. Antes de despedirse, el Agente usa otra herramienta (`save_opportunity_recommendation`) que guarda en la tabla `leads_opportunities` el problema del cliente, y en la tabla de recomendaciones inyecta los SKUs de los equipos discutidos.
5. El Comercial humano revisa el Panel (o recibe el Email) y ve: *"A Pedro Pérez le duele X, y la IA ya le recomendó el Equipo A y el Equipo B por estas razones"*. ¡La venta está un 50% cerrada!

---

## 5. Profundizando en RAG y Vector DBs (Independencia del LLM)

### ¿Dónde se definieron los Mixins?
Fueron programados en el archivo `src/database/base.py` (creado en la etapa anterior) y luego heredados por las tablas en `src/database/models.py`.

### ¿Qué es `sentence-transformers` y es de pago?
Es una librería **completamente gratuita y Open Source**. No es un servicio de suscripción. Descarga Modelos de Lenguaje pequeños (Embeddings) desde HuggingFace y los ejecuta **localmente en la CPU/RAM de tu propio servidor (Docker)**. Esto significa que convertir tu catálogo de productos a vectores matemáticos te cuesta **$0 dólares** y no compartes los datos de tus equipos con ninguna empresa externa.

### ¿Hay un modelo para cada LLM? ¿Todos entienden igual una BD Vectorial?
La Base de Datos Vectorial (ChromaDB) y el Modelo Local (`sentence-transformers`) son **100% independientes del Generador LLM** (DeepSeek, ChatGPT, Gemini). El flujo agnóstico funciona así:

1. **El cliente pregunta:** "Necesito medir el pH del agua cruda".
2. **Búsqueda (Local):** `sentence-transformers` convierte esa frase en un vector en milisegundos y hace la búsqueda matemática en `ChromaDB`.
3. **El Resultado:** ChromaDB extrae la información y te devuelve **TEXTO HUMANO PLANO**: *"Producto encontrado: Medidor Serie X - Ideal para agua cruda"*.
4. **La Magia del LLM:** Ese texto plano se inyecta en el Prompt que le enviamos a DeepSeek: *"El sistema encontró este producto: [Texto del Medidor Serie X]. Con base en esto, asesora al cliente"*.

**Conclusión (Portabilidad Absoluta):** Dado que la base de datos vectorial te entrega "texto", cualquier LLM del planeta (Claude, Gemini, ChatGPT) lo entenderá perfectamente. Si el año que viene decides abandonar DeepSeek y pasarte a Google Gemini, tu Base de Datos Vectorial seguirá intacta operando exactamente igual, porque la Búsqueda y la Generación están totalmente particionadas.
