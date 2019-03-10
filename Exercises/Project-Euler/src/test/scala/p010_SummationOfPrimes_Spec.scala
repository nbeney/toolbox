/*
The sum of the primes below 10 is 2 + 3 + 5 + 7 = 17.

Find the sum of all the primes below two million.
*/

import org.scalatest.FreeSpec

class p010_SummationOfPrimes_Spec extends FreeSpec {

  "The solution is correct" in {
    val ps = Util.primes(2000000)
    val ans = ps.map(_.toLong).sum
    assert(ans == 142913828922L)
  }
}
