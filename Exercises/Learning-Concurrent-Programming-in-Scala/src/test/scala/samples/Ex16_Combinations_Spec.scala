package samples

import org.scalatest.FreeSpec

class Ex16_Combinations_Spec extends FreeSpec {

  // TODO: Use Iterator
  def combinations[T](n: Int, xs: List[T]): List[List[T]] = {
    n match {
      case 0 => List(List())
      case _ =>
        (for (
          idx <- 0 until xs.length;
          cmb <- combinations(n - 1, xs.slice(idx + 1, xs.length))
        ) yield xs(idx) :: cmb).toList
    }
  }

  "combinations works" in {
    val input = List(1, 2, 3, 4)
    for (i <- 0 to input.length) assert(combinations(i, input) == input.combinations(i).toList)
  }
}
