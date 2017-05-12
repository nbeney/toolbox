from __future__ import print_function

from pprint import pprint

import jsl


class Person(jsl.Document):
    # class Options:
    #     definition_id = 'PERSON'
    #     title = 'Person'
    #     description = 'A person'

    fname = jsl.StringField(required=True)
    lname = jsl.StringField(required=True)
    age = jsl.IntField(required=True)


class Employee(Person):
    # class Options:
    #     # definition_id = 'EMPLOYEE'
    #     # title = 'Employee'
    #     # description = 'An employee'
    #     inheritance_mode = jsl.ALL_OF

    department = jsl.StringField(required=True)
    colleagues = jsl.ArrayField(items=jsl.DocumentField(jsl.RECURSIVE_REFERENCE_CONSTANT))


p = Person()
e = Employee()

pprint(e.get_schema(ordered=False))
pprint('-----------------')
pprint(p.is_recursive())
pprint(e.is_recursive())
pprint('-----------------')
pprint(p.get_definition_id())
pprint(e.get_definition_id())
pprint('-----------------')
pprint(p.resolve_field('fname'))
pprint(e.resolve_field('age'))
pprint('-----------------')
for _ in e.resolve_and_iter_fields():
    pprint(_)
pprint('-----------------')
for _ in e.resolve_and_walk():
    pprint(_)
pprint('-----------------')
pprint(p.get_definitions_and_schema())
pprint('')
pprint(e.get_definitions_and_schema())

print()
print()
print()

point_class = type(
    'Point',
    (jsl.Document,),
    {
        'x': jsl.NumberField(required=True),
        'y': jsl.NumberField(required=True),
        'z': jsl.NumberField(required=True),
    }
)

pt = point_class()
pprint(pt.get_schema())

print()
print()
print()

list_class = type(
    'List',
    (jsl.Document,),
    {
        'list': jsl.ArrayField(items=jsl.DocumentField(point_class)),
    }
)

l = list_class()
pprint(l.get_schema())
