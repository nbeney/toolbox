/*
A palindromic number reads the same both ways. The largest palindrome made from the product of two 2-digit numbers is 9009 = 91 × 99.

Find the largest palindrome made from the product of two 3-digit numbers.
 */

import org.scalatest.FreeSpec

class p004_LargestPalindromeProduct_Spec extends FreeSpec {

  "The solution is correct" in {
    def isPalindromic(n: Int): Boolean = n.toString == n.toString.reverse
    val products = for (
      p <- 100 to 999;
      q <- 100 to 999
    ) yield p * q
    val ans = products.filter(isPalindromic).max
    assert(ans == 906609)
  }
}
