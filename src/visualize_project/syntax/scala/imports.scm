; tree-sitter-scala emits import_declaration as a flat sequence of identifiers
; separated by dots, optionally followed by namespace_selectors or namespace_wildcard.
; Capture the whole node and parse the dotted path in Python.
(import_declaration) @import.scala_raw
