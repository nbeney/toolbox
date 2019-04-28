package samples

import org.scalatest.FreeSpec

import scala.annotation.tailrec

class Chap3_FuncDataStructs_List extends FreeSpec {

  sealed trait List[+A]

  final case object Nil extends List[Nothing]

  final case class Cons[+A](head: A, tail: List[A]) extends List[A]

  def nil[A]() = Nil: List[A]

  val L0 = nil[Int]
  val L1 = List(1)
  val L12 = List(1, 2)
  val L123 = List(1, 2, 3)
  val L1234 = List(1, 2, 3, 4)
  val L12345 = List(1, 2, 3, 4, 5)

  val La = List("a")
  val Lab = List("a", "b")
  val Labc = List("a", "b", "c")
  val Labcd = List("a", "b", "c", "d")
  val Labcde = List("a", "b", "c", "d", "e")

  def List[A](as: A*): List[A] = {
    // Non tailrec version:
    // if (as.length == 0) Nil else Cons(as.head, List(as.tail: _*))

    @tailrec
    def loop(as: Seq[A], acc: List[A]): List[A] =
      if (as.length == 0) acc else loop(as.tail, Cons(as.head, acc))

    loop(as.reverse, Nil)
  }

  def size[A](as: List[A]): Int = {
    // Non tailrec version:
    // as match {
    //   case Nil => 0
    //   case Cons(_, t) => 1 + size(t)
    // }

    @tailrec
    def loop(as: List[A], acc: Int): Int = as match {
      case Nil => acc
      case Cons(h, t) => loop(t, acc + 1)
    }

    loop(as, 0)
  }

  def append[A](as: List[A], a: A): List[A] = {
    // Non tailrec version:
    // as match {
    //   case Nil => Cons(a, Nil)
    //   case Cons(h, t) => Cons(h, append(t, a))
    // }

    @tailrec
    def loop(as: List[A], acc: List[A]): List[A] = as match {
      case Nil => Cons(a, acc)
      case Cons(h, t) => loop(t, Cons(h, acc))
    }

    reverse(loop(as, Nil))
  }

  def appendViaFoldRight[A](as: List[A], x: A): List[A] = {
    foldRight(as, List(x))(Cons(_, _))
  }

  def reverse[A](as: List[A]): List[A] = {
    // Non tailrec version:
    // as match {
    //   case Nil => Nil
    //   case Cons(h, t) => append(reverse(t), h)
    // }

    @tailrec
    def loop(as: List[A], acc: List[A]): List[A] = as match {
      case Nil => acc
      case Cons(h, t) => loop(t, Cons(h, acc))
    }

    loop(as, Nil)
  }

  def sum(is: List[Int]): Int = {
    // Non tailrec version:
    // is match {
    //   case Nil => 0
    //   case Cons(h, t) => h + sum(t)
    // }

    @tailrec
    def loop(is: List[Int], acc: Int): Int = is match {
      case Nil => acc
      case Cons(h, t) => loop(t, acc + h)
    }

    loop(is, 0)
  }

  def product(is: List[Int]): Int = {
    // Non tailrec version:
    // ds match {
    //   case Nil => 1
    //   case Cons(0, t) => 0
    //   case Cons(h, t) => h * product(t)
    // }

    @tailrec
    def loop(is: List[Int], acc: Int): Int = is match {
      case Nil => acc
      case Cons(0, t) => 0
      case Cons(h, t) => loop(t, acc * h)
    }

    loop(is, 1)
  }

  def foldLeft[A, B](as: List[A], z: B)(f: (B, A) => B): B = {
    // Non tailrec version:
    //     def loop(as: List[A], z: B)(f: (B, A) => B): B = {
    //       as match {
    //         case Nil => z
    //         case Cons(h, t) => f(loop(t, z)(f), h)
    //       }
    //     }
    //
    //     loop(reverse(as), z)(f)

    @tailrec
    def loop(as: List[A], acc: B): B = as match {
      case Nil => acc
      case Cons(h, t) => loop(t, f(acc, h))
    }

    loop(as, acc = z)
  }

  def foldRight[A, B](as: List[A], z: B)(f: (A, B) => B): B = {
    // Non tailrec version:
    // as match {
    //   case Nil => z
    //   case Cons(h, t) => f(h, foldRight(t, z)(f))
    // }

    @tailrec
    def loop(as: List[A], acc: B): B = as match {
      case Nil => acc
      case Cons(h, t) => loop(t, f(h, acc))
    }

    loop(reverse(as), z)
  }

  def filter[A](as: List[A])(pred: A => Boolean): List[A] = {
    // Non tailrec version
    // as match {
    //   case Nil => Nil
    //   case Cons(h, t) => if (pred(h)) Cons(h, filter(t)(pred)) else filter(t)(pred)
    // }

    @tailrec
    def loop(as: List[A], acc: List[A]): List[A] = as match {
      case Nil => acc
      case Cons(h, t) if pred(h) => loop(t, Cons(h, acc))
      case Cons(h, t) => loop(t, acc)
    }

    reverse(loop(as, Nil))
  }

  def filterViaFlatMap[A](as: List[A])(pred: A => Boolean): List[A] = {
    flatMap(as)(a => if (pred(a)) List(a) else List())
  }

  def map[A, B](as: List[A])(f: A => B): List[B] = {
    // Non tailrec version:
    // as match {
    //   case Nil => Nil
    //   case Cons(h, t) => Cons(f(h), map(t)(f))
    // }

    @tailrec
    def loop(as: List[A], acc: List[B]): List[B] = as match {
      case Nil => acc
      case Cons(h, t) => loop(t, Cons(f(h), acc))
    }

    reverse(loop(as, Nil))
  }

  def insert[A](as: List[A], others: List[A]): List[A] = {
    others match {
      case Nil => as
      case Cons(h, t) => Cons(h, insert(as, t))
    }
  }

  def flatMap[A, B](as: List[A])(f: A => List[B]): List[B] = {
    val bs = map(as)(f)
    foldRight(bs, nil[B])((a, b) => insert(b, a))
  }

  def fill[A](n: Int, a: A): List[A] = {
    // Non tailrec version:
    // n match {
    //   case 0 => Nil
    //   case n => Cons(a, fill(n - 1, a))
    // }

    @tailrec
    def loop(n: Int, acc: List[A]): List[A] =
      n match {
        case 0 => acc
        case n => loop(n - 1, Cons(a, acc))
      }

    loop(n, Nil)
  }

  def zipWith[A, B, C](as: List[A], bs: List[B])(f: (A, B) => C): List[C] = {
    (as, bs) match {
      case (Nil, Nil) => Nil
      case (Cons(ha, ta), Cons(hb, tb)) => Cons(f(ha, hb), zipWith(ta, tb)(f))
    }
  }

  "Basics" - {
    "construction" in {
      assert(L0 == Nil)
      assert(L1 == Cons(1, Nil))
      assert(L123 == Cons(1, Cons(2, Cons(3, Nil))))
    }

    "size" in {
      assert(size(L0) == 0)
      assert(size(L1) == 1)
      assert(size(L123) == 3)
    }

    "append" in {
      assert(append(L0, 10) == List(10))
      assert(append(L1, 10) == List(1, 10))
      assert(append(L123, 10) == List(1, 2, 3, 10))
    }

    "reverse" in {
      assert(reverse(L0) == L0)
      assert(reverse(L1) == L1)
      assert(reverse(L12) == List(2, 1))
      assert(reverse(L123) == List(3, 2, 1))
      assert(reverse(L12345) == List(5, 4, 3, 2, 1))
    }

    "sum" in {
      assert(sum(L0) == 0)
      assert(sum(L1) == 1)
      assert(sum(L12345) == 15)
    }

    "product" in {
      assert(product(L0) == 1)
      assert(product(L1) == 1)
      assert(product(L12345) == 120)
    }

    "foldLeft" in {
      def op(b: String, a: String): String = s"op(${b}, ${a})"

      assert(foldLeft(nil[String], "1")(op) == "1")
      assert(foldLeft(La, "1")(op) == "op(1, a)")
      assert(foldLeft(Lab, "1")(op) == "op(op(1, a), b)")
      assert(foldLeft(Labc, "1")(op) == "op(op(op(1, a), b), c)")
    }

    "foldRight" in {
      def op(a: String, b: String): String = s"op(${a}, ${b})"

      assert(foldRight(List(), "0")(op) == "0")
      assert(foldRight(La, "1")(op) == "op(a, 1)")
      assert(foldRight(Lab, "1")(op) == "op(a, op(b, 1))")
      assert(foldRight(Labc, "1")(op) == "op(a, op(b, op(c, 1)))")
    }

    "foldRight-sum" in {
      def sumFR(is: List[Int]) = foldRight(is, 0)(_ + _)

      assert(sumFR(L0) == 0)
      assert(sumFR(L1) == 1)
      assert(sumFR(L12345) == 15)
    }

    "foldRight-product" in {
      def productFR(ds: List[Int]) = foldRight(ds, 1)(_ * _)

      assert(productFR(L0) == 1)
      assert(productFR(L1) == 1)
      assert(productFR(L12345) == 120)
    }

    "map" in {
      val l = Cons(1, Cons(2, Cons(3, Nil)))
      val d = Cons(2, Cons(4, Cons(6, Nil)))
      assert(map(l)(_ * 2) == d)
    }

    "fill" in {
      assert(fill(0, 1) == Nil)
      assert(fill(1, 1) == L1)
      assert(fill(5, 1) == List(1, 1, 1, 1, 1))
      fill(10000, 0) // test for StackOverflowError
    }
  }

  def tail[A](as: List[A]) = as match {
    case Nil => Nil
    case Cons(h, t) => t
  }

  def setHead[A](as: List[A], v: A) = as match {
    case Nil => Nil
    case Cons(h, t) => Cons(v, t)
  }

  @tailrec
  final def drop[A](as: List[A], n: Int): List[A] =
    if (n == 0)
      as
    else
      as match {
        case Nil => Nil
        case Cons(h, t) => drop(t, n - 1)
      }

  @tailrec
  final def dropWhile[A](as: List[A])(pred: A => Boolean): List[A] =
    as match {
      case Nil => Nil
      case Cons(h, t) if pred(h) => dropWhile(t)(pred)
      case _ => as
    }

  def init[A](as: List[A]): List[A] = {
    // Non tailtrec version:
    // as match {
    //   case Nil => Nil
    //   case Cons(h, Nil) => Nil
    //  c ase Cons(h, t) => Cons(h, init(t))
    // }

    @tailrec
    def loop(as: List[A], acc: List[A]): List[A] = as match {
      case Nil => acc
      case Cons(h, Nil) => acc
      case Cons(h, t) => loop(t, Cons(h, acc))
    }

    reverse(loop(as, Nil))
  }

  "Exercises" - {
    "Ex3-1_match" in {
      val x = L12345 match {
        case Cons(x, Cons(2, Cons(4, _))) => x
        case Nil => 42
        case Cons(x, Cons(y, Cons(3, Cons(4, _)))) => x + y
        case Cons(h, t) => h + sum(t)
        case _ => 101
      }
      assert(x == 3)
    }

    "Ex3-2_tail" in {
      assert(tail(L12345) == List(2, 3, 4, 5))
      assert(tail(L12) == List(2))
      assert(tail(L1) == Nil)
      assert(tail(Nil) == Nil)
    }

    "Ex3-3_setHead" in {
      assert(setHead(L12345, 11) == List(11, 2, 3, 4, 5))
    }

    "Ex3-4_drop" in {
      val x = L12345
      assert(drop(x, 0) == x)
      assert(drop(x, 1) == tail(x))
      assert(drop(x, 2) == tail(tail(x)))
      assert(drop(x, 3) == tail(tail(tail(x))))
      assert(drop(x, 5) == Nil)
      assert(drop(x, 10) == Nil)
      assert(drop(Nil, 0) == Nil)
      assert(drop(Nil, 1) == Nil)
    }

    "Ex3-5_dropWhile2" in {
      val x = L12345
      assert(dropWhile(x)(_ < 1) == x)
      assert(dropWhile(x)(_ < 4) == List(4, 5))
      assert(dropWhile(x)(_ < 10) == Nil)
      assert(dropWhile(Nil)((x: Int) => x < 3) == Nil)
    }

    "Ex3-6_init" in {
      val x = L12345
      assert(init(Nil) == Nil)
      assert(init(L1) == Nil)
      assert(init(x) == L1234)
    }

    //    "Ex3-7_product_with_foldRight_and_short_circuit" in {
    //      ???
    //    }

    "Ex3-8_foldRight_with_Nil_and_Cons" in {
      val res = foldRight(L123, nil[Int])(Cons(_, _))
      assert(res == L123)
    }

    "Ex3-9_length_using_foldRight" in {
      def len[A](as: List[A]): Int = foldRight(as, 0)((a, b) => b + 1)

      assert(len(L0) == 0)
      assert(len(L1) == 1)
      assert(len(L12) == 2)
      assert(len(L12345) == 5)
    }

    "Ex3-10_foldLeft_stack_safe" in {
      val n = 100000
      val x = fill(n, 1)
      val sum = foldLeft(x, 0)(_ + _)
      assert(sum == n)
    }

    "Ex3-11_use_foldLeft" in {
      def sum(as: List[Int]): Int = foldLeft(as, 0)(_ + _)

      def product(as: List[Int]): Int = foldLeft(as, 1)(_ * _)

      def len(as: List[Int]): Int = foldLeft(as, 0)((b, a) => b + 1)

      val x = L12345
      assert(sum(x) == 15)
      assert(product(x) == 120)
      assert(len(x) == 5)
    }

    "Ex3-12_reverse_using_fold" in {
      def rev[A](as: List[A]): List[A] = foldLeft(as, nil[A])((b, a) => Cons(a, b))

      assert(rev(L12345) == List(5, 4, 3, 2, 1))
    }

    "Ex3-13_foldLeftRight_via_foldRightLeft-HARD" in {
      def foldLeftViaFoldRight1[A, B](as: List[A], z: B)(f: (B, A) => B): B =
        foldRight(as, (b: B) => b)((a, g) => b => g(f(b, a)))(z)

      def foldRightViaFoldLeft1[A, B](as: List[A], z: B)(f: (A, B) => B): B =
        foldLeft(as, (b: B) => b)((g, a) => b => g(f(a, b)))(z)

      assert(foldLeftViaFoldRight1(L123, 10)(_ - _) == ((10 - 1) - 2) - 3)
      assert(foldRightViaFoldLeft1(L123, 10)(_ - _) == 1 - (2 - (3 - 10)))
    }

    "Ex3-14_append_via_foldLeft_or_foldRight" in {
      assert(appendViaFoldRight(L0, 10) == List(10))
      assert(appendViaFoldRight(L1, 10) == List(1, 10))
      assert(appendViaFoldRight(L123, 10) == List(1, 2, 3, 10))
    }

    "Ex3-15_concatenate list of lists (HARD)" in {
      def concat2[A](as: List[A], bs: List[A]): List[A] = {
        (as, bs) match {
          case (Nil, Nil) => Nil
          case (as, Nil) => as
          case (Nil, bs) => bs
          case (Cons(ha, ta), bs) => Cons(ha, concat2(ta, bs))
        }
      }

      def concatenate[A](as: List[List[A]]): List[A] = {
        as match {
          case Nil => Nil
          case Cons(h, t) => concat2(h, concatenate(t))
        }
      }

      assert(concatenate(List()) == List())
      assert(concatenate(List(L0)) == L0)
      assert(concatenate(List(L0, L0, L0)) == L0)
      assert(concatenate(List(L0, L1)) == L1)
      assert(concatenate(List(L1, L0)) == L1)
      assert(concatenate(List(L1, L1)) == List(1, 1))
      assert(concatenate(List(L1, L0, L123, L1)) == List(1, 1, 2, 3, 1))
    }

    "Ex3-16_add_one" in {
      def add_one(as: List[Int]): List[Int] = map(as)(_ + 1)

      assert(add_one(L0) == L0)
      assert(add_one(L123) == List(2, 3, 4))
    }

    "Ex3-17_convert_to_strings" in {
      def convert(as: List[Double]): List[String] = map(as)(_.toString)

      assert(convert(List()) == List())
      assert(convert(List(1.0, 2.1, 3.1415)) == List("1.0", "2.1", "3.1415"))
    }

    "Ex3-18_map" in {
      assert(map(L0)(2 * _) == L0)
      assert(map(L123)(2 * _) == List(2, 4, 6))
    }

    "Ex3-19_filter" in {
      assert(filter(L0)(_ < 5) == L0)
      assert(filter(L12345)(_ < 4) == L123)
    }

    "Ex3-20_flatMap" in {
      assert(flatMap(L0)(i => List(i, i)) == L0)
      assert(flatMap(L123)(i => List(i, i)) == List(1, 1, 2, 2, 3, 3))
    }

    "Ex3-21_filterViaFlatMap" in {
      assert(filterViaFlatMap(L0)(_ < 5) == L0)
      assert(filterViaFlatMap(L12345)(_ < 4) == L123)
    }

    "Ex3-22_zipAdd" in {
      def zipAdd(as: List[Int], bs: List[Int]): List[Int] = {
        (as, bs) match {
          case (Nil, Nil) => Nil
          case (Cons(ha, ta), Cons(hb, tb)) => Cons(ha + hb, zipAdd(ta, tb))
        }
      }

      assert(zipAdd(L0, L0) == L0)
      assert(zipAdd(List(1, 2, 3), List(4, 5, 6)) == List(5, 7, 9))
    }

    "Ex3-23_zipWith" in {
      def zipAdd(as: List[Int], bs: List[Int]): List[Int] = zipWith(as, bs)(_ + _)

      assert(zipAdd(L0, L0) == L0)
      assert(zipAdd(List(1, 2, 3), List(4, 5, 6)) == List(5, 7, 9))
    }

    "Ex3-24_hasSubsequence (HARD)" in {
      def startsWith[A](as: List[A], bs: List[A]): Boolean = {
        (as, bs) match {
          case (_, Nil) => true
          case (Nil, _) => false
          case (Cons(ha, ta), Cons(hb, tb)) => ha == hb && startsWith(ta, tb)
        }
      }

      def hasSubsequence[A](as: List[A], bs: List[A]): Boolean = {
        (as, bs) match {
          case (_, Nil) => true
          case (Nil, _) => false
          case (Cons(ha, ta), bs) => startsWith(as, bs) || hasSubsequence(ta, bs)
        }
      }

      assert(!hasSubsequence(L0, List(1)))
      assert(!hasSubsequence(L0, List(1, 2, 3)))

      assert(hasSubsequence(L1, List(1)))

      assert(hasSubsequence(L12, List(1)))
      assert(hasSubsequence(L12, List(2)))
      assert(!hasSubsequence(L12, List(10)))
      assert(hasSubsequence(L12, List(1, 2)))
      assert(!hasSubsequence(L12, List(2, 1)))
      assert(!hasSubsequence(L12, List(1, 10)))
      assert(!hasSubsequence(L12, List(10, 2)))

      assert(hasSubsequence(L123, List(1)))
      assert(hasSubsequence(L123, List(2)))
      assert(hasSubsequence(L123, List(3)))
      assert(!hasSubsequence(L123, List(10)))
      assert(hasSubsequence(L123, List(1, 2)))
      assert(hasSubsequence(L123, List(2, 3)))
      assert(!hasSubsequence(L123, List(2, 1)))
      assert(!hasSubsequence(L123, List(3, 2)))
      assert(hasSubsequence(L123, List(1, 2, 3)))
      assert(!hasSubsequence(L123, List(1, 3, 2)))
      assert(!hasSubsequence(L123, List(2, 1, 3)))
    }

  }

  "Illustrations" - {
    "foldLeft illustration" in {
      /*
              op                          4
            /----\                      /----\
           op    3                     7     3
         /----\          =           /----\          =       op(op(op(z, 1), 2), 3)
        op    2                     9     2
      /----\                      /----\
      z    1                     10    1

     */

      type Op[B, A] = (B, A) => B
      type LeftFold[A, B] = (List[A], B) => Op[B, A] => B

      val ident = 10.0

      def op(b: Double, a: Int): Double = b - a

      def f1[A, B]: LeftFold[A, B] = foldLeft[A, B]

      assert(f1(L123, ident)(op) == op(op(op(ident, 1), 2), 3))
      assert(f1(L123, ident)(op) == 4)

      def f2: Op[Double, Int] => Double = foldLeft(L123, ident) _

      assert(f2(op) == op(op(op(ident, 1), 2), 3))
      assert(f2(op) == 4)

      def f3: (List[Int], Double) => Double = foldLeft(_: List[Int], _: Double)(op)

      assert(f3(L123, ident) == op(op(op(ident, 1), 2), 3))
      assert(f3(L123, ident) == 4)
    }

    "foldRight illustration" in {
      /*
         op                          -8
       /----\                      /----\
      3      op                    1    9
           /----\          =         /----\           =       op(1, op(2, op(3, z)))
          2     op                   2    -7
              /----\                    /----\
              3    z                    3    10

     */

      type Op[A, B] = (A, B) => B
      type RightFold[A, B] = (List[A], B) => Op[A, B] => B

      val ident = 10.0

      def op(a: Int, b: Double): Double = a - b

      def f1[A, B]: RightFold[A, B] = foldRight[A, B]

      assert(f1(L123, ident)(op) == op(1, op(2, op(3, ident))))
      assert(f1(L123, ident)(op) == -8)

      def f2: Op[Int, Double] => Double = foldRight(L123, ident) _

      assert(f2(op) == op(1, op(2, op(3, ident))))
      assert(f2(op) == -8)

      def f3: (List[Int], Double) => Double = foldRight(_: List[Int], _: Double)(op)

      assert(f3(L123, ident) == op(1, op(2, op(3, ident))))
      assert(f3(L123, ident) == -8)
    }

    "foldLeft in term of foldRight" in {
      val Z = 10.0

      def sub(d: Double, i: Int) = d - i

      val ident = identity[Double] _

      // Not stack-safe
      def foldLeftViaFoldRight[A, B](as: List[A], z: B)(f: (B, A) => B): B = {
        val ident: B => B = identity[B] _
        val comb: (A, B => B) => B => B = (a, g) => b => g(f(b, a))
        val eval: B => B = foldRight(as, ident)(comb)
        eval(z)
      }

      val res0 = foldLeftViaFoldRight(L0, Z)(sub)
      assert(res0 == foldLeft(L0, Z)(sub))
      assert(res0 == Z)
      // = ident(_)
      assert(res0 == ident(Z))

      val res1 = foldLeftViaFoldRight(L1, Z)(sub)
      assert(res1 == foldLeft(L1, Z)(sub))
      assert(res1 == sub(Z, 1))
      // = comb(1, ident(_))
      // = ident(sub(_, 1))
      assert(res1 == ident(sub(Z, 1)))

      val res2 = foldLeftViaFoldRight(L12, Z)(sub)
      assert(res2 == foldLeft(L12, Z)(sub))
      assert(res2 == sub(sub(Z, 1), 2))
      // = comb(1, comb(2, ident(_)))
      // = comb(1, ident((sub(_, 2))))
      // = ident((sub(sub(_, 1), 2)))
      assert(res2 == ident((sub(sub(Z, 1), 2))))

      val res3 = foldLeftViaFoldRight(L123, Z)(sub)
      assert(res3 == foldLeft(L123, Z)(sub))
      assert(res3 == sub(sub(sub(Z, 1), 2), 3))
      // = comb(1, comb(2, comb(3, ident(_))))
      // = comb(1, comb(2, ident(sub(_, 3))))
      // = comb(1, ident(sub(sub(_, 2), 3)))
      // = ident(sub(sub(sub(_, 1), 2), 3))
      assert(res3 == ident(sub(sub(sub(Z, 1), 2), 3)))
    }

    "foldRight in term of foldLeft" in {
      val Z = 10.0

      def sub(i: Int, d: Double) = i - d

      val ident = identity[Double] _

      // Not stack-safe
      def foldRightViaFoldLeft[A, B](as: List[A], z: B)(f: (A, B) => B): B = {
        val ident: B => B = identity[B] _
        val comb: (B => B, A) => B => B = (g, a) => b => g(f(a, b))
        val eval: B => B = foldLeft(as, ident)(comb)
        eval(z)
      }

      val res0 = foldRightViaFoldLeft(L0, Z)(sub)
      assert(res0 == foldRight(L0, Z)(sub))
      assert(res0 == Z)
      // = ident(_)
      assert(res0 == ident(Z))

      val res1 = foldRightViaFoldLeft(L1, Z)(sub)
      assert(res1 == foldRight(L1, Z)(sub))
      assert(res1 == sub(1, Z))
      // = comb(ident(_), 1)
      // = ident(sub(1, _))
      assert(res1 == ident(sub(1, Z)))

      val res2 = foldRightViaFoldLeft(L12, Z)(sub)
      assert(res2 == foldRight(L12, Z)(sub))
      assert(res2 == sub(1, sub(2, Z)))
      // = comb(comb(ident(_), 1), 2)
      // = comb(ident(sub(1, _)), 2)
      // = ident(sub(1, sub(2, _)))
      assert(res2 == ident(sub(1, sub(2, Z))))

      val res3 = foldRightViaFoldLeft(L123, Z)(sub)
      assert(res3 == foldRight(L123, Z)(sub))
      assert(res3 == sub(1, sub(2, sub(3, Z))))
      // = comb(comb(comb(ident(_), 1), 2), 3)
      // = comb(comb(ident(sub(1, _)), 2), 3)
      // = comb(ident(sub(1, sub(2, _))), 3)
      // = ident(sub(1, sub(2, sub(3, _))))
      assert(res3 == ident(sub(1, sub(2, sub(3, Z)))))
    }
  }
}