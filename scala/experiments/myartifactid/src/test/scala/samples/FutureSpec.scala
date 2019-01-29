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
    "called once" in {
      future(1) map { res => assert(res == 1) }
    }

    "called twice" in {
      val x = future(1)
      x map { res => assert(res == 1) }
      x map { res => assert(res == 1) }
    }

    "with Exception" in {
      recoverToSucceededIf[IllegalStateException] {
        future(1, exc = true)
      }
    }
  }
}
