/*
The prime factors of 13195 are 5, 7, 13 and 29.

What is the largest prime factor of the number 600851475143 ?
 */

import org.scalatest.FreeSpec

class p003_LargestPrimeFactor_Spec extends FreeSpec {

  "The solution is correct" in {
    val N = 600851475143L
    val root = Math.sqrt(N).toLong
    val ans = (3L to root by 2L).filter(N % _ == 0).filter(Util.isPrime).max
    assert(ans == 6857)
  }
}
