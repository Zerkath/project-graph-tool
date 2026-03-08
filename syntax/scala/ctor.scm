; Plain:    new Foo()
(instance_expression
    (type_identifier) @ctor.name)

; Generic:  new Foo[T]()
(instance_expression
    (generic_type (type_identifier) @ctor.name))

; Apply:    Foo()  (resolved against known class names in pass 2)
(call_expression
    (identifier) @ctor.name)
