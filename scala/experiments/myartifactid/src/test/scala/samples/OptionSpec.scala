package samples

import java.util.NoSuchElementException

import org.scalatest.prop.TableDrivenPropertyChecks
import org.scalatest.FreeSpec

import scala.util.Try

class OptionSpec extends FreeSpec with TableDrivenPropertyChecks {

  "Basic operations (based on Neophyte's Guide to Scala)" - {
    val VALUE_ODD = 123
    val VALUE_EVEN = 456
    val SOME_ODD: Option[Int] = Some(VALUE_ODD)
    val SOME_EVEN: Option[Int] = Some(VALUE_EVEN)
    val NONE: Option[Int] = None
    val SOME_SOME: Option[Option[Int]] = Some(SOME_ODD)
    val SOME_NONE: Option[Option[Int]] = Some(NONE)

    "Option (constructor)" in {
      assert(Option(1) == Some(1))
      assert(Option(null) == None)
    }

    "== and !=" in {
      assert(Some(1) == Some(1))
      assert(Some(1) != Some(2))
      assert(Some(1) != None)
      assert(None != Some(2))
      assert(None == None)
      assert(NONE == None)
    }

    "toString" in {
      assert(SOME_ODD.toString == s"Some(${SOME_ODD.get})")
      assert(NONE.toString == "None")
    }

    "mkString" in {
      assert(SOME_ODD.mkString("x", ",", "y") == s"x${SOME_ODD.get}y")
      assert(NONE.mkString("x", ",", "y") == "xy")
    }

    "isDefined" in {
      assert(SOME_ODD.isDefined)
      assert(!NONE.isDefined)
    }

    "isEmpty" in {
      assert(!SOME_ODD.isEmpty)
      assert(NONE.isEmpty)
    }

    "nonEmpty" in {
      assert(SOME_ODD.nonEmpty)
      assert(!NONE.nonEmpty)
    }

    "size" in {
      assert(SOME_ODD.size == 1)
      assert(NONE.size == 0)
    }

    "contains" in {
      assert(SOME_ODD contains VALUE_ODD)
      assert(!(NONE contains VALUE_ODD))
    }

    "get" in {
      assert(SOME_ODD.get == VALUE_ODD)
      assert(Try {NONE.get}.isFailure)
    }

    "getOrElse" in {
      assert(SOME_ODD.getOrElse(VALUE_EVEN) == SOME_ODD.get)
      assert(NONE.getOrElse(VALUE_EVEN) == VALUE_EVEN)
    }

    "orElse" in {
      assert((SOME_ODD orElse SOME_EVEN) == SOME_ODD)
      assert((SOME_ODD orElse NONE) == SOME_ODD)
      assert((NONE orElse SOME_EVEN) == SOME_EVEN)
      assert((NONE orElse NONE) == NONE)
    }

    "match" in {
      assert(Try {SOME_ODD match {case Some(_) => }}.isSuccess)
      assert(Try {SOME_ODD match {case Some(VALUE_ODD) => }}.isSuccess)
      assert(Try {SOME_ODD match {case Some(VALUE_EVEN) => }}.isFailure)
      assert(Try {NONE match {case None => }}.isSuccess)
    }

    "foreach" in {
      var ugly = 0
      SOME_ODD.foreach { x => ugly = x }
      assert(ugly == SOME_ODD.get)
      NONE.foreach { x => ugly += 1 }
      assert(ugly == SOME_ODD.get)
    }

    "for" in {
      assert((for (x <- SOME_ODD) yield 2 * x) == Some(2 * SOME_ODD.get))
      assert((for (x <- NONE) yield 2 * x) == None)

      assert((for (x <- SOME_SOME; y <- x) yield 2 * y) == Some(2 * SOME_SOME.get.get))
      assert((for (x <- SOME_NONE; y <- x) yield 2 * y) == None)

      assert({for (x <- SOME_ODD; y <- SOME_EVEN) yield x + y} == Some(SOME_ODD.get + SOME_EVEN.get))
      assert({for (x <- SOME_ODD; y <- NONE) yield x + y} == None)
      assert({for (x <- NONE; y <- SOME_EVEN) yield x + y} == None)
      assert({for (x <- NONE; y <- NONE) yield x + y} == None)
    }

    "map" in {
      assert(SOME_ODD.map(2 * _) == Some(2 * SOME_ODD.get))
      assert(NONE.map(2 * _) == None)

      assert(SOME_SOME.map(_.map(_ * 2)) == Some(Some(2 * SOME_SOME.get.get)))
      assert(SOME_NONE.map(_.map(_ * 2)) == Some(None))
    }

    "flatMap" in {
      assert(SOME_SOME.flatMap(identity) == SOME_SOME.get)
      assert(SOME_NONE.flatMap(identity) == None)

      assert(SOME_SOME.flatMap(_.map(_ * 2)) == Some(2 * SOME_SOME.get.get))
      assert(SOME_NONE.flatMap(_.map(_ * 2)) == None)
    }

    "flatten" in {
      assert(SOME_SOME.flatten == Some(SOME_SOME.get.get))
      assert(SOME_NONE.flatten == None)
    }

    "filter" in {
      assert(SOME_ODD.filter(_ % 2 == 0) == None)
      assert(SOME_ODD.filter(_ % 2 == 1) == SOME_ODD)
      assert(NONE.filter(_ % 2 == 1) == None)
    }
  }

  "Adding three Options should return an empty Option (None) unless they are all defined (Some)" in {
    def addUsingFor(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      for {x <- a; y <- b; z <- c} yield x + y + z

    def addUsingFlatmap(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      a.flatMap(x => b.flatMap(y => c.map(z => x + y + z)))

    def addUsingMatch(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      a match {
        case Some(x) =>
          b match {
            case Some(y) =>
              c match {
                case Some(z) => Some(x + y + z)
                case None => None
              }
            case None => None
          }
        case None => None
      }

    def addUsingIf(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      if (a.isDefined && b.isDefined && c.isDefined) Some(a.get + b.get + c.get) else None

    def addUsingTryStatement(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      try {
        Some(a.get + b.get + c.get)
      } catch {
        case ex: NoSuchElementException => None
      }

    def addUsingTryObject(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] =
      Try {a.get + b.get + c.get}.toOption

    type Op3 = (Option[Int], Option[Int], Option[Int]) => Option[Int]

    val allAddOperations: List[Op3] = List(
      addUsingFor,
      addUsingFlatmap,
      addUsingMatch,
      addUsingIf,
      addUsingTryStatement,
      addUsingTryObject
    )

    val ops = Table(
      ("op", "opIdx"),
      allAddOperations.zipWithIndex: _*
    )

    val SOME_1: Option[Int] = Some(1)
    val SOME_2: Option[Int] = Some(2)
    val SOME_3: Option[Int] = Some(3)
    val NONE: Option[Int] = None

    val inputs = Table(
      ("a", "b", "c", "expected"),
      (SOME_1, SOME_2, SOME_3, Some(6)),
      (NONE, SOME_2, SOME_3, None),
      (SOME_1, NONE, SOME_3, None),
      (SOME_1, SOME_2, NONE, None),
      (SOME_1, NONE, NONE, None),
      (NONE, SOME_2, NONE, None),
      (NONE, NONE, SOME_3, None),
      (NONE, NONE, NONE, None)
    )

    forAll(ops) { (op: Op3, opIdx: Int) =>
      forAll(inputs) { (a: Option[Int], b: Option[Int], c: Option[Int], expected: Option[Int]) =>
        assert(op(a, b, c) == expected)
      }
    }
  }
}
