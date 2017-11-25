from __future__ import print_function

from pyDatalog import pyDatalog as pdl

pdl.load('''
    + male(daniel)
    + male(nicolas)
    + male(alain)
    + male(luigi)
    + male(johnny)
    + male(sacha)
    + male(ernest)
    + male(robert)
    + male(gilbert)

    + female(suzanne)
    + female(christine)
    + female(keiko)
    + female(rose_marie)
    + female(sylvie)
    + female(muriel)
    + female(magali)
    + female(maya)
    + female(nana)
    + female(suzanne_madeleine)
    + female(violette)
    + female(jacqueline)

    + husband(nicolas, keiko)
    + husband(johnny, luigi)
    + husband(maurice, jacqueline)
    + husband(gilbert, rose_marie)

    + father(gilbert, muriel)
    + father(gilbert, sylvie)
    + mother(rose_marie, muriel)
    + mother(rose_marie, sylvie)

    + father(ernest, suzanne)
    + father(ernest, jacqueline)
    + mother(suzanne_madeleine, suzanne)
    + mother(suzanne_madeleine, jacqueline)

    + father(robert, daniel)
    + father(robert, gilbert)
    + mother(violette, daniel)
    + mother(violette, gilbert)

    + father(daniel, nicolas)
    + father(daniel, alain)
    + father(daniel, christine)
    + mother(suzanne, nicolas)
    + mother(suzanne, alain)
    + mother(suzanne, christine)

    + father(johnny, luigi)
    + father(johnny, magali)
    + mother(christine, luigi)
    + mother(christine, magali)

    + father(nicolas, sacha)
    + father(nicolas, maya)
    + father(nicolas, nana)
    + mother(keiko, sacha)
    + mother(keiko, maya)
    + mother(keiko, nana)

    parent(X, Y) <= (father(X, Y))
    parent(X, Y) <= (mother(X, Y))

    print(parent(Parent, Child) & (Child == nicolas))
    print()

    grand_parent(X, Y) <= (parent(X, Z) & parent(Z, Y))
    grand_father(X, Y) <= (grand_parent(X, Y) & male(X))
    grand_mother(X, Y) <= (grand_parent(X, Y) & female(X))

    print(grand_parent(GrandParent, GrandChild) & (GrandChild == nicolas))
    print()
    print(grand_father(GrandFather, GrandChild) & (GrandChild == nicolas))
    print()
    print(grand_mother(GrandMother, GrandChild) & (GrandChild == nicolas))
    print()

    sibling(X, Y) <= (parent(Z, X) & parent(Z, Y) & (X != Y))
    brother(X, Y) <= (male(X) & sibling(X, Y))
    sister(X, Y) <= (female(X) & sibling(X, Y))

    print(sibling(Sibling, X) & (X == nicolas))
    print()
    print(brother(Brother, X) & (X == nicolas))
    print()
    print(sister(Sister, X) & (X == nicolas))
    print()

    uncle(X, Y) <= (parent(Z, Y) & brother(X, Z))
    uncle(X, Y) <= (parent(Z, Y) & sibling(A, Z) & husband(X, A))
    aunt(X, Y) <= (parent(Z, Y) & sister(X, Z))
    aunt(X, Y) <= (parent(Z, Y) & sibling(A, Z) & husband(A, X))

    print(uncle(Uncle, X) & (X == nicolas))
    print()
    print(aunt(Aunt, X) & (X == nicolas))
    print()

    ancestor(X, Y) <= (parent(X, Y))
    ancestor(X, Y) <= (parent(X, Z) & ancestor(Z, Y))

    print(ancestor(MaleAncestor, X) & (X == nicolas) & male(MaleAncestor))
    print()

    descendant(X, Y) <= (ancestor(Y, X))

    print(descendant(FemaleDescendant, X) & (X == daniel) & female(FemaleDescendant))
    print()
''')
