package samples

import org.scalatest.FreeSpec

import scala.annotation.tailrec

class Ex23_Curry_Spec extends FreeSpec {

  def curry[A, B, C](f: (A, B) => C): A => (B => C) = (a: A) => (b: B) => f(a, b)

  "curry works" in {
    val f2 = (n: Int, s: String) => s * n
    assert(f2(3, "x") == "xxx")

    val fc = curry(f2)
    assert(fc(3)("x") == "xxx")
    assert(fc(3)("x") == f2(3, "x"))
  }
}
