; import x.y / import x.y as z
(import_statement (dotted_name) @import.module)
(import_statement (aliased_import (dotted_name) @import.module))

; from x.y import ...
(import_from_statement module_name: (dotted_name) @import.module)

; from . import ... / from ..pkg import ...
(import_from_statement module_name: (relative_import) @import.relative)
