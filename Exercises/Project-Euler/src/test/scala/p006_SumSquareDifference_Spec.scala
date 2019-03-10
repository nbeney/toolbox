/*
The sum of the squares of the first ten natural numbers is,

        1^2 + 2^2 + ... + 10^2 = 385

The square of the sum of the first ten natural numbers is,

        (1 + 2 + ... + 10)^2 = 55^2 = 3025

Hence the difference between the sum of the squares of the first ten natural numbers and the square of the sum is 3025 − 385 = 2640.

Find the difference between the sum of the squares of the first one hundred natural numbers and the square of the sum.
*/

import org.scalatest.FreeSpec

class p006_SumSquareDifference_Spec extends FreeSpec {

  "The solution is correct" in {
    val N = 100L
    val sum = (1L to N).sum
    val squareSum = Math.pow(sum, 2).toLong
    val sumSquare = (1L to N).map(Math.pow(_, 2).toLong).sum
    val ans = squareSum - sumSquare
    assert(ans == 25164150L)
  }
}
