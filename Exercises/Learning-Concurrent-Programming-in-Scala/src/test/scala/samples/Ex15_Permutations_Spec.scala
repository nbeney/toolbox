package samples

import org.scalatest.FreeSpec

class Ex15_Permutations_Spec extends FreeSpec {

  def permutations(s: String): Seq[String] = {
    def loop(xs: List[Char]): List[List[Char]] = {
      xs.length match {
        case 1 => List(xs)
        case _ => {
          (for {
            idx <- 0.until(xs.length);
            tmp <- loop(xs.slice(0, idx) ::: xs.slice(idx + 1, xs.length))
          } yield (xs(idx) :: tmp)).toList
        }
      }
    }

    if (s == "") Seq("") else loop(s.toList).map(_.mkString)
  }

  "permutations works for an empty String" in {
    assert(permutations("") == Seq(""))
  }

  "permutations works for a 1-char String" in {
    assert(permutations("a") == Seq("a"))
  }

  "permutations works for a 2-char String" in {
    assert(permutations("ab") == Seq("ab", "ba"))
  }

  "permutations works for a 3-char String" in {
    assert(permutations("abc") == Seq("abc", "acb", "bac", "bca", "cab", "cba"))
  }
}
