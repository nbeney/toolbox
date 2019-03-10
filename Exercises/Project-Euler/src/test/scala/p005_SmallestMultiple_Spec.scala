/*
2520 is the smallest number that can be divided by each of the numbers from 1 to 10 without any remainder.

What is the smallest positive number that is evenly divisible by all of the numbers from 1 to 20?
 */

import org.scalatest.FreeSpec

class p005_SmallestMultiple_Spec extends FreeSpec {

  "The solution is correct" in {
    val N = 20
    val primes = Util.primes(N)
    val exps = primes.map(p => Math.floor(Math.log(N) / Math.log(p)))
    val ans = (primes zip exps).map { case (p, e) => Math.pow(p, e) }.product
    assert(ans == 232792560)
  }
}
