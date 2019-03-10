/*
A Pythagorean triplet is a set of three natural numbers, a < b < c, for which,

        a^2 + b^2 = c^2

For example, 3^2 + 4^2 = 9 + 16 = 25 = 5^2.

There exists exactly one Pythagorean triplet for which a + b + c = 1000.

Find the product abc.
*/

import org.scalatest.FreeSpec

class p009_SpecialPythagoreanTriplet_Spec extends FreeSpec {

  def isPyhagoreanTriplet(a: Int, b: Int, c: Int) = {
    a < b && b < c && (Math.pow(a, 2) + Math.pow(b, 2)) == Math.pow(c, 2)
  }

  "The solution is correct" in {
    val S = 1000
    val triplets = for (
      a <- 1 to 999;
      b <- a + 1 to 999;
      if isPyhagoreanTriplet(a, b, S - a - b)
    ) yield (a, b, S - a - b)
    assert(triplets.length == 1)
    val (a, b, c) = triplets.head
    val ans = a * b * c
    assert(ans == 31875000)
  }
}
