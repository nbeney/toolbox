package samples

import org.scalatest.FreeSpec

class Ex14_Pair_Spec extends FreeSpec {

  class Pair1[A, B](val a: A, val b: B)

  object Pair1 {
    def apply[A, B](a: A, b: B): Pair1[A, B] = new Pair1(a, b)
    def unapply[A, B](p: Pair1[A, B]): Option[(A, B)] = Some(p.a, p.b)
  }

  "Pair1 can be matched" in {
    val A = 1
    val B = "hi"
    val p = new Pair1(A, B)
    p match {
      case Pair1(A, B) =>
    }
  }

  case class Pair2[A, B](val a: A, val b: B)

  "Pair2 can be matched" in {
    val A = 1
    val B = "hi"
    val p = new Pair2(A, B)
    p match {
      case Pair2(A, B) =>
    }
  }
}
