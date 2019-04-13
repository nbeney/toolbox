package samples

import org.scalatest.FreeSpec

class Ex24_Uncurry_Spec extends FreeSpec {

  def uncurry[A, B, C](f: A => B => C): (A, B) => C = (a: A, b: B) => f(a)(b)

  "uncurry works" in {
    val fc = (n: Int) => (s: String) => s * n
    assert(fc(3)("x") == "xxx")

    val f2 = uncurry(fc)
    assert(f2(3, "x") == "xxx")
    assert(f2(3, "x") == fc(3)("x"))
  }
}
