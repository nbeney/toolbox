package samples

import org.scalatest.FreeSpec

class Ex25_Compose_Spec extends FreeSpec {

  def compose[A, B, C](g: B => C, f: A => B): A => C = (a: A) => g(f(a))

  "compose works" in {
    val f = (n: Int) => "1" * n
    val g = (s: String) => s.toDouble
    assert(compose(g, f)(2) == 11.0)
    assert(compose(g, f)(2) == (g compose f)(2))
    assert(compose(g, f)(2) == (f andThen g)(2))
  }
}
