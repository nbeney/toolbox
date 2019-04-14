package samples

import org.scalatest.AsyncFreeSpec

import scala.concurrent.Future
import scala.concurrent.duration._

class FutureSpec extends AsyncFreeSpec {

  private def future(n: Int, delay: Option[Duration] = None, exc: Boolean = false): Future[Int] = Future {
    if (delay.isDefined) Thread.sleep(delay.get.toMillis)
    if (exc) throw new IllegalStateException
    n
  }

  "Basic tests" - {
    "with successful Future" in {
      val f = future(1)
      f map { res => assert(res == 1) }
      f map { res => assert(res == 1) }
    }

    "with failed Exception" in {
      val f = future(1, exc = true)
      recoverToSucceededIf[IllegalStateException] {
        f
      }
      recoverToSucceededIf[IllegalStateException] {
        f
      }
    }

    "with successful" in {
      val f = Future.successful(1)
      f map { res => assert(res == 1) }
      f map { res => assert(res == 1) }
    }

    "with failed" in {
      val f = Future.failed(new IllegalStateException())
      recoverToSucceededIf[IllegalStateException] {
        f
      }
      recoverToSucceededIf[IllegalStateException] {
        f
      }
    }
  }

  "Future of future" - {
    "xxx" in {
      val ff: Future[Future[Int]] = Future {
        Future(1)
      }

      val res = for {
        x: Future[Int] <- ff
        y: Int <- x
      } yield y

      assert(res == 1)
    }
  }
}
