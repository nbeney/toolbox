import org.scalatest.FreeSpec

class Util_Spec extends FreeSpec {

  "The Util.isPrime function works" in {
    assert(Util.isPrime(2))
    assert(Util.isPrime(3))
    assert(Util.isPrime(5))
    assert(Util.isPrime(7))

    assert(!Util.isPrime(1))
    assert(!Util.isPrime(4))
    assert(!Util.isPrime(6))
    assert(!Util.isPrime(8))
    assert(!Util.isPrime(9))
  }

  "The Util.primes function works" in {
    assert(Util.primes(20) == List(2, 3, 5, 7, 11, 13, 17, 19))
  }

  "The Util.nthPrime function works" in {
    assert(Util.nthPrime(1) == 2)
    assert(Util.nthPrime(2) == 3)
    assert(Util.nthPrime(3) == 5)
    assert(Util.nthPrime(4) == 7)
    assert(Util.nthPrime(5) == 11)
  }

  "The Util.factors function works" in {
    assert(Util.factors(1) == List(1))
    assert(Util.factors(2) == List(1, 2))
    assert(Util.factors(3) == List(1, 3))
    assert(Util.factors(4) == List(1, 2, 4))
    assert(Util.factors(5) == List(1, 5))
    assert(Util.factors(6) == List(1, 2, 3, 6))
  }
}
