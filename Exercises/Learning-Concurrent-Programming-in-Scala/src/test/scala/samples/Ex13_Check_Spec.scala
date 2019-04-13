package samples

import org.scalatest.FreeSpec

class Ex13_Check_Spec extends FreeSpec {

  def check[T](xs: Seq[T])(pred: T => Boolean) = xs.forall(pred)

  "check works" in {
    assert(check(1 to 10)(_ > 0))
    assert(!check(1 to 10)(_ % 2 == 1))
  }
}
