package samples

import org.scalatest.FreeSpec

class Ex12_Fuse_Spec extends FreeSpec {

  def fuse[A, B](a: Option[A], b: Option[B]): Option[(A, B)] =
    for (x <- a; y <- b) yield (x, y)

  "fuse works" in {
    val a = 1
    val someA = Some(a)
    val b = "hi"
    val someB = Some(b)

    assert(fuse(someA, someB) == Some((a, b)))
    assert(fuse(someA, None) == None)
    assert(fuse(None, someB) == None)
    assert(fuse(None, None) == None)
  }
}
