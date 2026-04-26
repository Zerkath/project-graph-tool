(class_declaration
    name: (identifier) @class.name
    body: (class_body
        (method_declaration name: (identifier) @method.name))) @class.def

(interface_declaration name: (identifier) @class.name)
(enum_declaration      name: (identifier) @class.name)
