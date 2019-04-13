package samples

import org.scalatest.FreeSpec
import org.scalatest.prop.TableDrivenPropertyChecks

import scala.annotation.tailrec

class Ex11_Compose_Spec extends FreeSpec {

  def compose[A, B, C](g: B => C, f: A => B): A => C = (x: A) => g(f(x))

  "compose works for two functions with the same type" in {
    val f = (x: Int) => x * 2
    val g = (x: Int) => x - 1

    assert(compose(f, g)(3) == f(g(3)))
    assert(compose(f, g)(3) == 4)
    assert(compose(g, f)(3) == g(f(3)))
    assert(compose(g, f)(3) == 5)
  }

  "compose works for two functions with different types" in {
    val f = (x: Double) => x.toInt
    val g = (x: Int) => "*" * x

    assert(compose(g, f)(3) == g(f(3)))
    assert(compose(g, f)(3) == "***")
  }
}
