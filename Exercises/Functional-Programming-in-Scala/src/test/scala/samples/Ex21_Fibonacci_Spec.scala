package samples

import org.scalatest.FreeSpec
import org.scalatest.prop.TableDrivenPropertyChecks

import scala.annotation.tailrec

class Ex21_Fibonacci_Spec extends FreeSpec with TableDrivenPropertyChecks {

  def fibIter(n: Int): Int = {
    n match {
      case 1 => 0
      case 2 => 1
      case _ =>
        var p = 0
        var q = 1
        for (x <- 3 to n) {
          val tmp: Int = p + q
          p = q
          q = tmp
        }
        q
    }
  }

  def fibNaiveRec(n: Int): Int = {
    n match {
      case 1 => 0
      case 2 => 1
      case _ => fibNaiveRec(n - 2) + fibNaiveRec(n - 1)
    }
  }

  // TODO: Add another version that uses double recursion but with memoization.
  def fibMemoRec(n: Int): Int = ???

  def fibTailRec(n: Int): Int = {
    @tailrec
    def loop(i: Int, p: Int, q: Int): Int = if (i == n) q else loop(i + 1, q, p + q)

    n match {
      case 1 => 0
      case 2 => 1
      case _ => loop(3, 1, 0 + 1)
    }
  }

  lazy val fibs: Stream[Int] = 0 #:: 1 #:: fibs.zip(fibs.tail).map { case (p, q) => p + q }

  def fibStream(n: Int): Int = fibs(n - 1)

  def test(f: Int => Int) = {
    val data =
      Table(
        ("input", "output"),
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 2),
        (5, 3),
        (6, 5),
        (7, 8),
        (8, 13),
        (9, 21),
        (10, 34),
      )

    forAll(data) { (inp: Int, out: Int) =>
      assert(f(inp) == out)
    }
  }

  "The iterative version is working" in {
    test(fibIter)
  }

  "The naive recursive version is working" in {
    test(fibNaiveRec)
  }

  "The memoized recursive version is working" in {
    test(fibMemoRec)
  }

  "The tail recursive version is working" in {
    test(fibTailRec)
  }

  "The stream version is working" in {
    test(fibStream)
  }

  "The tail recursive version is faster than the naive recursive version" in {
    // TODO: Is there a standard library function to do this?
    def timed(block: => Unit): Long = {
      val startTime = System.currentTimeMillis()
      block
      val endTime = System.currentTimeMillis()
      endTime - startTime
    }

    val N = 40
    val durTail = timed {
      fibTailRec(N)
    }
    val durNaive = timed {
      fibNaiveRec(N)
    }
    val durStream = timed {
      fibStream(N)
    }
    println(s"The tail recursive version took ${durTail} ms")
    println(s"The naive recursive version took ${durNaive} ms")
    println(s"The stream version took ${durStream} ms")
    assert(durTail < durNaive)
    assert(durStream < durNaive)
    assert(durTail <= durStream)
  }
}
