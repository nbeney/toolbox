package sample

object App {

  def foo(xs: Array[String]) = xs.foldLeft("")((a, b) => a + b)

  def main(args: Array[String]) {
    println("Hello World!")
    println("concat arguments = " + foo(args))
  }
}
