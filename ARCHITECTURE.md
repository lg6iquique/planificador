
 
## Convenciones del proyecto

- Cada módulo es una app Django independiente.
- Todas las vistas renderizan templates (no HttpResponse directo).
- Todos los templates heredan de base.html.
- El menú de navegación vive solo en base.html.
- URLs de cada módulo están bajo su prefijo (/personas/, /usuarios/).
- CRUD completo por módulo.
- SQLite para desarrollo, MySQL en producción.
- No se usan librerías externas innecesarias.
