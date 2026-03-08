(class_definition
    name: (identifier) @class.name
    (template_body
        (function_definition name: (identifier) @method.name))) @class.def

(object_definition
    name: (identifier) @class.name
    (template_body
        (function_definition name: (identifier) @method.name))) @class.def

(trait_definition
    name: (identifier) @class.name
    (template_body
        (function_definition name: (identifier) @method.name))) @class.def
