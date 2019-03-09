package samples

import org.scalatest.FreeSpec

import scala.annotation.tailrec

class Ex22_IsSorted_Spec extends FreeSpec {

  def isSorted[T](as: Array[T], ordered: (T, T) => Boolean): Boolean = {
    @tailrec
    def loop(i: Int): Boolean = if (i > as.length - 2) true else ordered(as(i), as(i + 1)) && loop(i + 1)

    loop(0)
  }

  def cmp(a: Int, b: Int): Boolean = b - a >= 0

  def assertPositive(as: Array[Int]) = {
    println(s"Testing ${as.mkString("(", ",", ")")}")
    assert(isSorted(as, cmp))
  }

  def assertNegative(as: Array[Int]) = {
    println(s"Testing ${as.mkString("(", ",", ")")}")
    assert(!isSorted(as, cmp))
  }

  "cmp works" in {
    assert(cmp(1, 1))
    assert(cmp(1, 2))
    assert(!cmp(2, 1))
  }

  "isSorted works for empty Arrays" in {
    assertPositive(Array())
  }

  "isSorted works for sorted Arrays" in {
    for (n <- 1 to 5) {
      val as = (1 to n).toArray
      assertPositive(as)
    }
  }

  "isSorted works for unsorted Arrays" in {
    for (n <- 2 to 5) {
      val as = (1 to n).toArray
      for (x <- as.permutations if !(x sameElements as)) {
        assertNegative(x)
      }
    }
  }
}
