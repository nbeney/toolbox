import scala.annotation.tailrec

object Util {

  def isPrime(n: Long): Boolean = {
    if (n == 2)
      true
    else if (n < 2 || n % 2 == 0)
      false
    else {
      val root = Math.sqrt(n).toLong
      !(3L to root by 2L).exists(f => n % f == 0)
    }
  }

  def isDivisible(n: Int, ps: List[Int]): Boolean = {
    ps.exists(n % _ == 0)
  }

  def primes(n: Long): List[Long] = 2L :: (3L to n by 2L).filter(isPrime(_)).toList

  def nthPrime(n: Int): Int = {
    @tailrec
    def loop(ps: List[Int], i: Int): Int = {
      if (ps.length == n)
        ps.head
      else if (!isDivisible(i, ps)) {
        loop(i :: ps, i + 2)
      } else {
        loop(ps, i + 2)
      }
    }

    loop(List(2), 3)
  }

  def factors(n: Long): List[Long] = {
    (1L to n).filter(n % _ == 0).toList
  }
}
