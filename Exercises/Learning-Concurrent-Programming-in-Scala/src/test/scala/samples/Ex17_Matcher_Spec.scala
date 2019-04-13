package samples

import org.scalatest.FreeSpec

import scala.util.matching.Regex

class Ex17_Matcher_Spec extends FreeSpec {

  def matcher(regex: String): PartialFunction[String, List[String]] = {
    val re = new Regex(regex)
    new PartialFunction[String, List[String]] {
      def apply(s: String): List[String] = re.findAllMatchIn(s).map(_.group(0).toString).toList

      def isDefinedAt(s: String): Boolean = re.findAllMatchIn(s).nonEmpty
    }
  }

  "matcher works when there are matches" in {
    val pf = matcher("a+")
    val matches = List("a", "a", "aa")
    val input = matches.mkString("x", "y", "z")
    assert(pf.isDefinedAt(input))
    assert(pf(input) == matches)
  }

  "matcher works when there are no matches" in {
    val pf = matcher("a+")
    val matches = List()
    val input = matches.mkString("x", "y", "z")
    assert(!pf.isDefinedAt(input))
  }
}
