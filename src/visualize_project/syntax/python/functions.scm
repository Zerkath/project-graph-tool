; Top-level function definitions (direct children of the module)
(module
    (function_definition name: (identifier) @function.name))

; Decorated top-level: @decorator def foo(): ...
(module
    (decorated_definition
        (function_definition name: (identifier) @function.name)))
