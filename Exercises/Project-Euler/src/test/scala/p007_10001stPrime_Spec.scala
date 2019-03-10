/*
By listing the first six prime numbers: 2, 3, 5, 7, 11, and 13, we can see that the 6th prime is 13.

What is the 10001st prime number?
*/

import org.scalatest.FreeSpec

class p007_10001stPrime_Spec extends FreeSpec {

  "The solution is correct" in {
    val ans = Util.nthPrime(10001)
    assert(ans == 25164150L)
  }
}
