# jag_kb_last_modified_order

Módulo para Knowledge (`document.page`) que ajusta el orden en las vistas de páginas.

## Objetivo

Mejorar la navegación en Knowledge con un orden útil por defecto:

- Carpetas (`type = category`): orden alfabético por nombre.
- Documentos (`type = content`): orden por última revisión, de más reciente a más antigua.

Además, en la vista de lista de Páginas se fuerza el orden por:

- `content_date desc`
- `id desc`

para evitar resultados inconsistentes cuando la vista no aplica el `_order` global del modelo.

## Dependencias

- `document_page`

## Datos cargados

- `views/document_page_views.xml`

## Notas técnicas

- Se añaden campos auxiliares de orden para categorías.
- El orden de documentos usa `history_head desc`, que representa la última revisión de contenido.
- Incluye tests del módulo para validar:
  - Orden de categorías por nombre.
  - Orden de documentos por última modificación.

## Licencia

LGPL-3.
