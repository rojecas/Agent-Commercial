# 📘 DOCUMENTACIÓN COMPLETA - INASC

**Proyecto:** Instruments & Applied Science INASC S.A.S.  
**Versión:** 2.0  
**Última actualización:** Octubre 2025  
**Framework:** PHP Vanilla (Sin framework)  

---

## 📋 ÍNDICE

1. [Descripción General](#descripción-general)
2. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
3. [Estructura de Archivos](#estructura-de-archivos)
4. [Tecnologías Utilizadas](#tecnologías-utilizadas)
5. [Sistema de Routing](#sistema-de-routing)
6. [Características Implementadas](#características-implementadas)
7. [Sistema de Responsive Design](#sistema-de-responsive-design)
8. [Optimizaciones de Rendimiento](#optimizaciones-de-rendimiento)
9. [Seguridad](#seguridad)
10. [Guía de Desarrollo](#guía-de-desarrollo)

---

## 🎯 DESCRIPCIÓN GENERAL

INASC es un sitio web corporativo especializado en la comercialización de instrumentos y equipos científicos para laboratorios en Colombia. El sitio incluye:

- **Catálogo de productos** con sistema de categorías
- **Cotizador en línea** con carrito persistente
- **Laboratorio de Metrología** acreditado
- **Servicio Técnico** especializado
- **Sistema de búsqueda** de productos y columnas HPLC
- **Panel de administración** completo (directorio `/zoom/`)
- **Conversión automática** de imágenes a WebP
- **SEO avanzado** con meta tags dinámicos y Schema.org

---

## 🏗️ ARQUITECTURA DEL PROYECTO

### **Patrón de Diseño**
- **MVC Simplificado** sin framework formal
- **Front Controller:** `index.php` → `views/index.php`
- **Routing:** Sistema de parámetros GET (`?getion=`)
- **Template System:** Inclusión de archivos PHP

### **Stack Tecnológico**
```
├── Frontend
│   ├── HTML5 + CSS3
│   ├── JavaScript (ES6)
│   ├── Bootstrap 4.1.3
│   ├── jQuery 3.3.1
│   ├── Font Awesome (iconos)
│   └── Slick Carousel
│
├── Backend
│   ├── PHP 8.x
│   ├── MySQL (PDO)
│   ├── Clase ZOOM (ORM custom)
│   └── Apache (mod_rewrite)
│
└── Herramientas
    ├── GD Library (procesamiento imágenes)
    ├── PHPMailer (emails)
    └── NiceScroll (UI)
```

---

## 📁 ESTRUCTURA DE ARCHIVOS

```
inasc/
│
├── 📄 index.php                    # Entry point principal
├── 📄 sitemap.php                  # Sitemap XML dinámico
├── 📄 test-sitemap.php             # Validador de sitemap
├── 📄 robots.txt                   # Configuración para crawlers
├── 📄 .htaccess                    # Configuración Apache
├── 📄 Documentation.md             # Esta documentación
├── 📄 SEO-DOCUMENTATION.md         # Documentación de SEO
├── 🖼️ favicon.ico                  # Icono del sitio
│
├── 📂 cods/                        # Código CSS y JavaScript
│   ├── css/
│   │   ├── cssion.css             # Estilos generales
│   │   ├── fixion-4.css           # Estilos de layout
│   │   ├── fontion-2.css          # Utilidades de fuentes/tamaños
│   │   └── responsion-2.css       # Media queries y responsive
│   └── js/
│       ├── jquerion.js            # Inicialización jQuery
│       ├── mainion.js             # Funcionalidades generales
│       └── quoter.tool.js         # Sistema de cotizador
│
├── 📂 includes/                    # Scripts de procesamiento
│   ├── config/
│   │   ├── email_class.php        # Clase de email
│   │   └── email_config.php       # Configuración SMTP
│   ├── contact_mail.php           # Envío formulario contacto
│   ├── quote_actions.php          # Acciones del cotizador
│   ├── quote_items.php            # Listado items cotizador
│   ├── quote_mail.php             # Envío cotización por email
│   └── quote_summary.php          # Resumen de cotización
│
├── 📂 resources/                   # Recursos multimedia
│   ├── img/                       # Imágenes generales
│   │   ├── general/               # Imágenes del sitio
│   │   ├── clientes/              # Logos de clientes
│   │   └── important/             # Imágenes críticas
│   ├── fonts/                     # Fuentes web
│   │   ├── fa/                    # Font Awesome
│   │   ├── rrss/                  # Iconos redes sociales
│   │   ├── special/               # Fuentes especiales
│   │   └── webfonts/              # Web fonts
│   ├── plugins/                   # Librerías JavaScript
│   │   ├── bootstrap-4.1.3-dist/
│   │   ├── fancybox-3.0/         # Lightbox de imágenes
│   │   ├── jquery-3.3.1/
│   │   ├── nicescroll/           # Scrollbar personalizado
│   │   ├── PHPMailer/            # Envío de correos
│   │   └── slick/                # Carrusel de imágenes
│   ├── pdf/                      # Documentos PDF
│   └── complements/              # Componentes adicionales
│       ├── wowInasc/             # Efectos animación
│       └── wowProducto/          # Animaciones productos
│
├── 📂 static/                     # Contenido estático
│   ├── webp.php                  # Conversor JPG/PNG → WebP
│   ├── analytes/                 # Documentos analitos (PDF)
│   ├── brochures/                # Catálogos productos
│   │   └── ACE/                  # Brochures ACE
│   ├── categories/               # Imágenes de categorías
│   ├── columns/                  # Imágenes de columnas HPLC
│   ├── documents/                # Documentación técnica
│   ├── products/                 # Imágenes de productos
│   │   ├── m/                    # Tamaño medio
│   │   ├── s/                    # Tamaño pequeño
│   │   └── l/                    # Tamaño grande
│   └── zones/                    # Imágenes por zonas
│
├── 📂 views/                      # Vistas y templates
│   ├── 📄 index.php              # Configuración y enrutamiento
│   ├── 📄 views.php              # Router de vistas
│   │
│   ├── components/               # Componentes reutilizables
│   │   └── producto.php         # Card de producto
│   │
│   ├── general/                  # Templates generales
│   │   ├── head.php             # <head> del sitio
│   │   ├── header.php           # Navegación principal
│   │   ├── footer.php           # Pie de página
│   │   ├── end.php              # Scripts finales
│   │   ├── metas.php            # Meta tags dinámicos (SEO)
│   │   ├── modal.php            # Modales globales
│   │   ├── lista_piezas.php    # Listado de productos
│   │   └── preview/             # Vistas previas
│   │
│   └── paginas/                 # Páginas del sitio
│       ├── home.php             # Página de inicio
│       ├── productos.php        # Catálogo de productos
│       ├── categoria.php        # Productos por categoría
│       ├── producto.php         # Detalle de producto
│       ├── columna.php          # Detalle columna HPLC
│       ├── filtro_columnas.php # Filtro de columnas
│       ├── busqueda.php        # Resultados de búsqueda
│       ├── ccmt.php            # Laboratorio de Metrología
│       ├── servicio-tecnico.php # Servicio técnico
│       ├── nosotros.php        # Sobre la empresa
│       ├── contacto.php        # Formulario de contacto
│       └── cotizacion.php      # Carrito de cotización
│
└── 📂 zoom/                      # Panel de administración
    ├── 📄 index.php             # Entry point admin
    ├── 📄 .htaccess             # Protección directorio
    │
    ├── cods/                    # CSS/JS del admin
    ├── default/                 # Templates admin
    ├── resources/               # Recursos admin
    ├── views/                   # Vistas admin
    │
    └── zoom/                    # Core del sistema
        ├── class/              # Clases PHP
        │   ├── classZoom.php  # ORM custom
        │   ├── class.inputfilter.php
        │   ├── resize-class.php
        │   └── connect/       # Conexión BD
        │
        └── process/           # Procesadores AJAX
            ├── general/
            ├── configuraciones/
            └── inasc/
```

---

## 🛠️ TECNOLOGÍAS UTILIZADAS

### **Frontend**

| Tecnología | Versión | Uso |
|------------|---------|-----|
| Bootstrap | 4.1.3 | Grid system, componentes UI |
| jQuery | 3.3.1 | Manipulación DOM, AJAX |
| Font Awesome | 5.x | Iconografía |
| Slick | 1.8.1 | Carruseles de imágenes |
| Fancybox | 3.0 | Lightbox de imágenes |
| NiceScroll | 3.x | Scrollbar personalizado |

### **Backend**

| Tecnología | Uso |
|------------|-----|
| PHP | 8.x (compatible con 7.4+) |
| MySQL | Base de datos relacional |
| PDO | Acceso a base de datos |
| GD Library | Procesamiento de imágenes |
| PHPMailer | Envío de correos SMTP |

---

## 🔀 SISTEMA DE ROUTING

### **Funcionamiento**
```php
# URL: http://inasc.local/productos
# Apache (.htaccess) convierte a: index.php?getion=productos

# views/index.php carga la configuración
# views/views.php enruta a la vista correspondiente
```

### **Rutas Principales**

```php
/                       → home.php
/productos              → productos.php
/categoria/{url}        → categoria.php
/producto/{sku}/{nombre}→ producto.php
/columna/{sku}/{nombre} → columna.php
/filtro-columnas        → filtro_columnas.php
/busqueda               → busqueda.php
/ccmt                   → ccmt.php
/servicio-tecnico       → servicio-tecnico.php
/nosotros               → nosotros.php
/contacto               → contacto.php
/cotizacion             → cotizacion.php
```

### **Parámetros URL**
```php
$geton = explode("/", $_GET['getion']);

// Ejemplo: producto/ACE-001/columna-hplc
$geton[0] = "producto"     // Tipo de página
$geton[1] = "ACE-001"      // SKU del producto
$geton[2] = "columna-hplc" // Slug SEO (opcional)
```

---

## ✨ CARACTERÍSTICAS IMPLEMENTADAS

### **1. Sistema Responsive Completo** ✅

#### **Logo Adaptativo**
```css
/* cssion.css */
.logo-svg {
    width: 300px;  /* Default: PC grande */
    transition: width 0.3s ease;
}

@media (max-width: 1440px) { width: 250px; }
@media (max-width: 1280px) { width: 240px; }
@media (max-width: 768px)  { width: 180px; }
@media (max-width: 480px)  { width: 150px; }
```

#### **Menú Móvil Mejorado**
- 🎨 Diseño moderno con animaciones
- 🍔 Hamburger icon CSS puro (3 barras → X)
- 🎬 Animación slide-down con efecto fade
- 👆 Cierre al hacer clic fuera del menú
- 📱 Optimizado para touch devices
- ✨ Efecto de presionado en página activa

#### **Sistema de Clases Responsive**
```css
/* Sufijos para responsive */
._oS    → Solo en móvil/tablet (max-width: 991px)
._oPC   → Solo en PC (min-width: 992px)

/* Ejemplos */
.dN_oS      → display: none en móvil
.pAA60_oS   → padding: 60px en móvil
.w100_oS    → width: 100% en móvil
.h80_oS     → height: 80px en móvil
.mb20_oS    → margin-bottom: 20px en móvil
```

### **2. Botón de WhatsApp** ✅
```html
<!-- header.php -->
<a href="https://wa.me/573502490204?text=Hola%2C%20me%20gustar%C3%ADa%20recibir%20informaci%C3%B3n%20sobre%20sus%20productos%20y%20servicios" 
   class="lkWhats">
    <i class="fab fa-whatsapp"></i>
    <span class="dN_oS">&nbsp;Contáctanos</span>
</a>
```

**Características:**
- 📞 Enlace directo a WhatsApp Business
- 💬 Mensaje predefinido personalizado
- 🎨 Diseño sutil con hover effect
- 📱 Adaptado para web y móvil

### **3. Sistema de Cotizador** ✅

**Archivos involucrados:**
- `cods/js/quoter.tool.js` - Lógica del carrito
- `includes/quote_actions.php` - Agregar/eliminar items
- `includes/quote_items.php` - Listar items
- `includes/quote_summary.php` - Resumen y totales
- `includes/quote_mail.php` - Envío por email
- `views/paginas/cotizacion.php` - Página del carrito

**Funcionalidades:**
- ➕ Agregar productos desde cualquier página
- 🔢 Contador de items en badge
- 📋 Persistencia en sesión PHP
- ✉️ Envío de cotización por email
- 📄 Generación de PDF (opcional)

### **4. Búsqueda Inteligente** ✅

**Búsqueda por:**
- Nombre de producto
- Número de catálogo / SKU
- Marca
- Categoría
- Palabras clave

**Resultados:**
- Productos regulares
- Columnas HPLC
- Categorías relacionadas

### **5. Imágenes WebP** ✅

**Archivo:** `static/webp.php`

**Características:**
- 🔄 Conversión automática JPG/PNG → WebP
- 📊 Ahorro de 60-80% en peso
- 🛡️ Protección contra sobrecarga
- 📈 Estadísticas detalladas
- 🎛️ Configuración personalizable

**Configuración `.htaccess`:**
```apache
### WEBP SUPPORT
RewriteCond %{HTTP_ACCEPT} image/webp
RewriteCond %{REQUEST_URI} \.(jpe?g|png)$ [NC]
RewriteCond %{DOCUMENT_ROOT}%{REQUEST_URI}.webp -f
RewriteRule ^(.*)\.(jpe?g|png)$ $1.$2.webp [T=image/webp,E=accept:1,L]
```

**Flujo:**
```
1. Navegador solicita: imagen.jpg
2. .htaccess verifica: ¿existe imagen.jpg.webp?
3. Si existe y navegador soporta WebP → sirve WebP
4. Si no → sirve JPG original
```

### **6. SEO Avanzado** ✅

Ver [SEO-DOCUMENTATION.md](SEO-DOCUMENTATION.md) para detalles completos.

**Resumen:**
- 🏷️ Meta tags dinámicos por página
- 📱 Open Graph (Facebook/WhatsApp)
- 🐦 Twitter Cards
- 📊 Schema.org / JSON-LD
- 🗺️ Sitemap XML dinámico
- 🤖 robots.txt optimizado
- 🔗 URLs canónicas
- 🌍 Geolocalización (Cali, Colombia)

---

## 📐 SISTEMA DE RESPONSIVE DESIGN

### **Breakpoints**

| Dispositivo | Ancho | Media Query |
|------------|-------|-------------|
| Móvil pequeño | < 480px | `@media (max-width: 480px)` |
| Móvil | 481px - 767px | `@media (max-width: 767px)` |
| Tablet | 768px - 991px | `@media (max-width: 991px)` |
| Desktop | 992px - 1199px | `@media (min-width: 992px)` |
| Desktop grande | 1200px - 1919px | `@media (min-width: 1200px)` |
| 4K/UHD | > 1920px | Default |

### **Clases Responsive Personalizadas**

Definidas en `cods/css/responsion-2.css`:

```css
/* Utilidades de display */
.dN_oS      /* display: none en móvil */
.dN_oPC     /* display: none en PC */
.dB_oS      /* display: block en móvil */
.dIB_oPC    /* display: inline-block en PC */

/* Dimensiones */
.w100_oS    /* width: 100% en móvil */
.h80_oS     /* height: 80px en móvil */
.hAUTO_oS   /* height: auto en móvil */
.max100_oS  /* max-width: 100% en móvil */

/* Padding */
.pAA60_oS   /* padding: 60px en móvil */
.p30_oS     /* padding: 30px en móvil */
.pLR20_oS   /* padding-left/right: 20px en móvil */

/* Margin */
.mb20_oS    /* margin-bottom: 20px en móvil */
.m0_oS      /* margin: 0 en móvil */

/* Textos */
.t14_oS     /* font-size: 14px en móvil */
.taC_oS     /* text-align: center en móvil */
.taL_oS     /* text-align: left en móvil */

/* Tablas */
.tab100_oS  /* table width: 100% en móvil */

/* Márgenes especiales (por página) */
.mEs1 → .mEs8  /* Ajustes específicos */
```

### **Bootstrap Grid**

```html
<!-- Responsive grid -->
<div class="row">
    <div class="col-lg-6 col-md-12 col-12">
        <!-- 50% en desktop, 100% en móvil -->
    </div>
</div>
```

---

## ⚡ OPTIMIZACIONES DE RENDIMIENTO

### **1. Compresión GZIP** ✅
```apache
# .htaccess
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/css text/javascript
    AddOutputFilterByType DEFLATE application/javascript
    # Ahorro: ~70% en tamaño de archivos
</IfModule>
```

### **2. Caché del Navegador** ✅
```apache
# .htaccess - Cachear recursos estáticos
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType image/jpg "access plus 1 year"
    ExpiresByType image/webp "access plus 1 year"
    ExpiresByType text/css "access plus 1 month"
    ExpiresByType application/javascript "access plus 1 month"
</IfModule>
```

### **3. Imágenes WebP** ✅
- Conversión automática
- Fallback a JPG/PNG
- Ahorro 60-80% en peso

### **4. Lazy Loading** (Recomendado)
```html
<!-- Agregar a imágenes -->
<img src="producto.jpg" loading="lazy" alt="...">
```

### **5. Minificación** (Pendiente)
- Minificar CSS
- Minificar JavaScript
- Combinar archivos

---

## 🔒 SEGURIDAD

### **Implementaciones Actuales**

#### **1. Headers de Seguridad** ✅
```apache
# .htaccess
Header set X-Content-Type-Options "nosniff"
Header set X-Frame-Options "SAMEORIGIN"
Header set X-XSS-Protection "1; mode=block"
Header set Referrer-Policy "strict-origin-when-cross-origin"
```

#### **2. Protección de Archivos** ✅
```apache
# Bloquear acceso a archivos sensibles
<FilesMatch "\.(htaccess|htpasswd|ini|log|env|md)$">
    Require all denied
</FilesMatch>
```

#### **3. InputFilter** ✅
```php
// zoom/class/class.inputfilter.php
// Limpieza de inputs XSS
```

#### **4. Prevención Directory Listing** ✅
```apache
Options -Indexes
```

### **⚠️ PENDIENTES DE SEGURIDAD**

#### **🔴 CRÍTICO:**
1. **HTTPS/SSL**
   - Obtener certificado SSL (Let's Encrypt gratuito)
   - Forzar redirección HTTP → HTTPS
   - Actualizar configuración de dominio

2. **Prepared Statements**
   - Migrar todas las consultas SQL a PDO Prepared Statements
   - Evitar SQL Injection

3. **Validación de Inputs**
   - Validar todos los formularios server-side
   - Sanitizar datos de usuario

4. **CSRF Protection**
   - Implementar tokens CSRF en formularios

5. **Rate Limiting**
   - Limitar intentos de login
   - Proteger formularios de spam

---

## 🧑‍💻 GUÍA DE DESARROLLO

### **Configuración del Entorno**

#### **Requisitos:**
- PHP 8.x (compatible con 7.4+)
- MySQL 5.7+
- Apache con mod_rewrite
- Extensión GD habilitada
- Extensión PDO habilitada

#### **Configuración Local:**

1. **Archivo hosts** (Windows):
```
# C:\Windows\System32\drivers\etc\hosts
127.0.0.1 inasc.local
```

2. **VirtualHost Apache**:
```apache
<VirtualHost *:80>
    ServerName inasc.local
    DocumentRoot "W:/XAMPP/xampp8-2-12/htdocs/inasc"
    <Directory "W:/XAMPP/xampp8-2-12/htdocs/inasc">
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

3. **Configuración BD**:
```php
// views/index.php
if ($isLocal) {
    $dominion = "http://inasc.local/";
    $path = "W:/XAMPP/xampp8-2-12/htdocs/inasc/";
}
```

### **Agregar una Nueva Página**

1. **Crear vista** en `views/paginas/nueva-pagina.php`
2. **Agregar ruta** en `views/views.php`:
```php
if($geton[0] == "nueva-pagina" || $geton[0] == "nueva-pagina/"){
    include $roution."views/paginas/nueva-pagina.php";
}
```
3. **Agregar meta tags** en `views/general/metas.php`
4. **Agregar al sitemap** en `sitemap.php`

### **Modificar Estilos**

```css
/* cssion.css - Estilos generales */
.mi-clase {
    color: #333;
}

/* responsion-2.css - Versión móvil */
@media screen and (max-width: 991px) {
    .mi-clase {
        color: #666;
    }
}
```

### **Agregar JavaScript**

```javascript
// mainion.js
$(document).ready(function() {
    // Tu código aquí
});
```

---

## 📊 CLASE ZOOM (ORM Custom)

### **Ubicación:** `zoom/zoom/class/classZoom.php`

### **Métodos Principales:**

```php
// Obtener datos
$_ZOOM->get_data($table, $condition, $multiple);

// Ejemplo:
$productos = $_ZOOM->get_data(
    "i3_productos", 
    " AND inactivo = 0 AND eliminado = 0 ", 
    1  // 1 = múltiples, 0 = uno solo
);

// Otros métodos útiles
$_ZOOM->url_seo($string);           // Genera URL SEO-friendly
$_ZOOM->upload_file($file);         // Sube archivos
$_ZOOM->resize_image($image, $w, $h); // Redimensiona imágenes
```

---

## 🗄️ ESTRUCTURA DE BASE DE DATOS

### **Tablas Principales:**

```sql
i3_productos           # Productos del catálogo
i3_productos_imagenes  # Imágenes de productos
i3_categorias          # Categorías
i3_marcas              # Marcas
in_columnas            # Columnas HPLC
in_clasificacion       # Clasificación de columnas
in_fases              # Fases cromatográficas
in_diametros          # Diámetros de columna
```

---

## 🔧 HERRAMIENTAS ÚTILES

### **Desarrollo:**
- [XAMPP](https://www.apachefriends.org/) - Servidor local
- [HeidiSQL](https://www.heidisql.com/) - Cliente MySQL
- [Visual Studio Code](https://code.visualstudio.com/) - Editor

### **Validación:**
- [W3C HTML Validator](https://validator.w3.org/)
- [CSS Validator](https://jigsaw.w3.org/css-validator/)
- [GTmetrix](https://gtmetrix.com/) - Performance

### **SEO:**
- [Google Search Console](https://search.google.com/search-console)
- [Google PageSpeed Insights](https://pagespeed.web.dev/)
- [Schema Validator](https://validator.schema.org/)

---

## 📝 CHANGELOG RECIENTE

### **Octubre 2025**
- ✅ Logo responsive con 11 breakpoints
- ✅ Menú móvil rediseñado con animaciones
- ✅ Botón WhatsApp implementado
- ✅ Sistema responsive completo para todas las páginas
- ✅ SEO avanzado con meta tags dinámicos
- ✅ Sitemap XML corregido y funcional
- ✅ Sistema WebP optimizado
- ✅ Documentación completa actualizada

---

## 📞 CONTACTO

**Sitio Web:** https://inasc.com.co  
**Email:** info@inasc.com.co  
**WhatsApp:** +57 350 249 0204  
**Ubicación:** Cali, Colombia  

---

## 📄 LICENCIA

© 2025 Instruments & Applied Science INASC S.A.S.  
Todos los derechos reservados.

---

**Última actualización:** 4 de Octubre de 2025  
**Versión del documento:** 2.0  
**Mantenedor:** Equipo de Desarrollo INASC
