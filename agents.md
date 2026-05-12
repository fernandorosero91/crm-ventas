
### Requisitos del aplicativo

Desarrollar una aplicación web completa utilizando el framework Django, aplicando los principios fundamentales del desarrollo de software, la arquitectura MVT (Modelo-Vista-template)	y	las	buenas	prácticas	de	programación. El proyecto deberá incluir una temática específica de aplicación (biblioteca, reservas, inventario, gestión académica, etc.), con un flujo de autenticación de usuarios, operaciones CRUD (crear, leer, actualizar y eliminar) y un panel de administración con reportes gráficos con su respectivo despliegue.

###Objetivo general
Diseñar, implementar y desplegar una aplicación web funcional que integre los componentes esenciales del desarrollo con Django: gestión de usuarios, manipulación de datos desde una base relacional, y visualización de información mediante interfaces web y gráficos interactivos.

Requisitos funcionales comunes a todos los proyectos
1.	Autenticación y autorización de usuarios
o	Debe existir un sistema de inicio de sesión, registro y cierre de sesión.
o	Implementar diferentes roles (por ejemplo: administrador, usuario, cliente, operador).
2.	Modelado de datos
o	Crear al menos 4 modelos principales relacionados mediante llaves foráneas.
o	Definir los campos con tipos de datos adecuados (CharField, IntegerField, DateField, etc.).
3.	Operaciones CRUD completas
o	Permitir crear, consultar, actualizar y eliminar registros desde la interfaz web.
o	Implementar formularios validados (Django Forms o ModelForms).
4.	Panel de administración (Dashboard)
o	Mostrar estadísticas y gráficos (Chart.js, Plotly o D3.js).
o	Ejemplo: número de registros, elementos más usados, actividades recientes.
5.	Reportes y exportación de datos
 
o	Generar reportes descargables en PDF o Excel (con reportlab o pandas).
o	Incluir filtros de búsqueda y segmentación por fechas o categorías.
6.	Interfaz de usuario (Frontend)
o	Desarrollar una interfaz limpia y responsiva (Bootstrap o TailwindCSS).
o	Incluir menús de navegación y alertas de confirmación.
7.	Validaciones y control de errores
o	Manejar correctamente excepciones y validaciones en formularios y vistas.
o	Evitar duplicados o datos inconsistentes.
8.	Despliegue del sistema
o	Subir la aplicación a una plataforma gratuita (Render, Railway o PythonAnywhere).
o	Conectar a una base de datos PostgreSQL o SQLite según disponibilidad.
9.	Documentación técnica
o	Incluir archivo README.md con descripción del proyecto, requerimientos e instrucciones de instalación.
o	Documentar modelos y rutas principales del sistema.
10.	Gráficos e indicadores (Charts)
•	Incluir mínimo dos gráficos estadísticos en el dashboard (por ejemplo: top 5 productos vendidos, usuarios activos, reservas por mes, etc.).
•	Deben alimentarse dinámicamente desde los datos reales del sistema.


Entregables
•	Código fuente completo del proyecto.
•	Documento técnico o informe final (descripción del sistema, modelos, flujos, capturas).
•	URL pública de despliegue funcional.

### APLICTIVO A DESARROLLAR
Sistema de Gestión de Ventas y Clientes (CRM básico)
Descripción: Herramienta para seguimiento de clientes y control de ventas.
Características:
1.	Inicio de sesión con roles.
2.	CRUD de clientes y oportunidades de venta.
3.	Registro de seguimientos y contactos.
4.	Estadísticas por cliente o vendedor.
5.	Recordatorios automáticos.
6.	Gráficos: ventas por mes, clientes activos/inactivos.
7.	Exportación de reportes.
8.	Dashboard de KPIs.
9.	Integración con correos automáticos.
10.	Buscador inteligente por nombre o ID.


### RESTRICCIONES DEL PROYECTO
1. Organización del equipo

El sistema debe planearse para un equipo de 4 desarrolladores, distribuyendo responsabilidades por módulos y funcionalidades.

Cada desarrollador debe trabajar en una aplicación independiente del proyecto siguiendo una arquitectura modular.

2. Arquitectura del sistema

El proyecto debe desarrollarse usando:

Backend: Django
Frontend: HTML + Tailwind CSS + JavaScript
Base de datos: PostgreSQL
Arquitectura MVT modular
Variables de entorno para configuraciones sensibles
Patrón MVC/MVT y separación de responsabilidades

El sistema debe dividirse en las siguientes aplicaciones:

core
users/authentication
clients
sales
dashboard
notifications
reports
3. Estándares de programación

Todo el código fuente debe escribirse en inglés:

nombres de variables
funciones
clases
modelos
endpoints
comentarios técnicos

La interfaz visual dirigida al usuario debe estar completamente en español.

Se deben aplicar:

Clean Code
SOLID principles
DRY
buenas prácticas REST
tipado y validaciones
manejo correcto de excepciones
4. Seguridad

El sistema debe implementar prácticas de seguridad profesionales:

Protección contra SQL Injection usando ORM
Protección CSRF
Protección XSS
Validación backend y frontend
Sanitización de entradas
Autenticación segura
Control de acceso basado en roles
Protección de variables sensibles mediante .env
Restricción de vistas según permisos

Roles mínimos:

Administrador
Vendedor
Supervisor
5. Interfaz y experiencia visual

La interfaz debe desarrollarse usando:

Tailwind CSS

Restricciones visuales:

No usar colores morados
Diseño moderno y profesional
Responsive design
Dashboard interactivo
Componentes reutilizables
Animaciones suaves
Formularios modernos
Tablas avanzadas
Sidebar adaptable
Compatibilidad móvil y escritorio

Paleta recomendada:

Azul oscuro
Azul petróleo
Gris grafito
Blanco
Verde esmeralda para indicadores positivos
6. Funcionalidades técnicas obligatorias

El sistema debe incluir:

Autenticación con roles
CRUD completo
Buscador inteligente
Dashboard KPI
Gráficos dinámicos
Exportación PDF/Excel/CSV
Recordatorios automáticos
Correos automáticos
Paginación
Filtros avanzados
Logs básicos del sistema
7. DevOps y despliegue

El proyecto debe ser desplegable mediante contenedores Docker.

Debe incluir:

Dockerfile
docker-compose.yml
configuración para Dockploy
archivo .env.example
configuración de producción
configuración de static/media
configuración segura para producción
Gunicorn/Nginx
documentación de despliegue

8. Control de versiones

El equipo debe trabajar usando:

GitHub
ramas por funcionalidad
Pull Requests
commits descriptivos
documentación técnica mínima

Convención recomendada:

feature/
fix/
hotfix/
release/
9. Calidad del software

El sistema debe garantizar:

Código reutilizable
Escalabilidad
Mantenibilidad
Separación de responsabilidades
Bajo acoplamiento
Alta cohesión

10. no incluyas test por tareas, solo se hara un test final 




