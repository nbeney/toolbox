/*
The following iterative sequence is defined for the set of positive integers:

        n → n/2 (n is even)
        n → 3n + 1 (n is odd)

Using the rule above and starting with 13, we generate the following sequence:

        13 → 40 → 20 → 10 → 5 → 16 → 8 → 4 → 2 → 1

It can be seen that this sequence (starting at 13 and finishing at 1) contains 10 terms. Although it has not been proved
yet (Collatz Problem), it is thought that all starting numbers finish at 1.

Which starting number, under one million, produces the longest chain?

NOTE: Once the chain starts the terms are allowed to go above one million.
*/

import org.scalatest.FreeSpec

import scala.annotation.tailrec
import scala.collection.concurrent.TrieMap
import scala.collection.mutable

class p014_LongestCollatzSequence_Spec extends FreeSpec {
  val cache = new TrieMap[Int, List[Int]]

  def collatzSeq(n: Int): List[Int] = {
    def loop(n: Int): List[Int] = {
      val x = cache.get(n)
      x match {
        case Some(y) =>
          y
        case None =>
          val v: List[Int] = if (n == 1)
            1 :: Nil
          else if (n % 2 == 0)
            loop(n / 2) ::: (n :: Nil)
          else
            loop(3 * n + 1) ::: (n :: Nil)

          cache.update(n, v)
          v
      }
    }

    cache.getOrElseUpdate(n, loop(n))
  }

  "The solution is correct" in {
    val res = (999000 until 999050).map(n => collatzSeq(n)).maxBy(_.length)
    assert(res == 999904)
    //    (1 to 25).foreach { n => println(n, collatzSeq(n)) }
  }
}
