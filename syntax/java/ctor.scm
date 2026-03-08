; Plain:    new Foo()
(object_creation_expression
    type: (type_identifier) @ctor.name)

; Generic:  new Foo<T>()
(object_creation_expression
    type: (generic_type (type_identifier) @ctor.name))
