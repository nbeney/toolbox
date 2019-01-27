package samples

import java.util.NoSuchElementException

import org.scalatest.prop.TableDrivenPropertyChecks
import org.scalatest.{FreeSpec}

class OptionSpec extends FreeSpec with TableDrivenPropertyChecks {

  private val SOME_1: Option[Int] = Some(1)
  private val SOME_2: Option[Int] = Some(2)
  private val SOME_3: Option[Int] = Some(3)
  private val NONE: Option[Int] = None

  private def toTextIfOdd(x: Int): Option[String] =
    if (x % 2 == 1) Some(x.toString) else None.asInstanceOf[Option[String]]

  private type Operation3 = (Option[Int], Option[Int], Option[Int]) => Option[Int]

  private val allAddOperations: List[Operation3] = List(
    addUsingFor,
    addUsingFlatmap,
    addUsingMatch,
    addUsingIf,
    addUsingTry
  )

  private def addUsingFor(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] = {
    for {
      x <- a
      y <- b
      z <- c
    } yield x + y + z
  }

  private def addUsingFlatmap(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] = {
    a.flatMap(x =>
      b.flatMap(y =>
        c.map(z =>
          x + y + z
        )
      )
    )
  }

  private def addUsingMatch(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] = {
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
  }

  private def addUsingIf(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] = {
    if (a.isDefined && b.isDefined && c.isDefined)
      Some(a.get + b.get + c.get)
    else
      None
  }

  private def addUsingTry(a: Option[Int], b: Option[Int], c: Option[Int]): Option[Int] = {
    try {
      Some(a.get + b.get + c.get)
    } catch {
      case ex: NoSuchElementException => None
    }
  }

  "A defined Option (Some)" - {
    "has size 1, is defined, and is not empty" in {
      assert(SOME_1.size == 1)
      assert(SOME_1.isDefined)
      assert(!SOME_1.isEmpty)
      assert(SOME_1.nonEmpty)
    }

    "has a value" in {
      assert(SOME_1.get == 1)
      assert(SOME_1.getOrElse(10) == 1)
      assert(SOME_1.contains(SOME_1.get))
    }

    "has a non empty String from mkString" in {
      assert(SOME_1.mkString(",") == "1")
    }

    "matches Some" in {
      SOME_1 match {
        case Some(x) => assert(x == 1)
        case None => fail()
      }
    }

    "maps to another defined Option (Some)" in {
      assert(SOME_1.map(_.toString) == Some("1"))
    }

    "flatMaps to another defined Option (Some)" in {
      assert(SOME_1.flatMap(toTextIfOdd) == Some("1"))
      assert(SOME_2.flatMap(toTextIfOdd) == None)
      assert(SOME_3.flatMap(toTextIfOdd) == Some("3"))
    }
  }

  "An empty Option (None)" - {
    "has size 0, is nnot defined, and is empty" in {
      assert(NONE.size == 0)
      assert(!NONE.isDefined)
      assert(NONE.isEmpty)
      assert(!NONE.nonEmpty)
    }

    "has no value" in {
      assertThrows[NoSuchElementException] {
        NONE.get
      }
      assert(NONE.getOrElse(10) == 10)
    }

    "has an empty String from mkString" in {
      assert(NONE.mkString(",") == "")
    }

    "matches None" in {
      NONE match {
        case Some(_) => fail()
        case None =>
      }
    }

    "maps to another empty Option (None)" in {
      assert(NONE.map(_.toString) == None)
    }

    "flatMaps to another defined Option (Some)" in {
      assert(NONE.flatMap(toTextIfOdd) == None)
    }
  }

  "Adding three Options should return an empty Option (None) unless they are all defined (Some)" in {
    val ops = Table(
      ("op", "opIdx"),
      allAddOperations.zipWithIndex: _*
    )

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

    forAll(ops) { (op: Operation3, opIdx: Int) =>
      forAll(inputs) { (a: Option[Int], b: Option[Int], c: Option[Int], expected: Option[Int]) =>
        assert(op(a, b, c) == expected)
      }
    }
  }
}
