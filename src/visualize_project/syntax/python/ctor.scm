; Plain:    Foo()
(call
    function: (identifier) @ctor.name)

; Qualified: module.Foo() — capture the trailing attribute
(call
    function: (attribute attribute: (identifier) @ctor.name))
