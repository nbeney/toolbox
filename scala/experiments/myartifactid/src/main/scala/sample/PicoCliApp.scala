package sample

import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter

import picocli.CommandLine
import picocli.CommandLine.{Command, ITypeConverter, Option => Opt}

//class LocalDateConverter extends ITypeConverter[LocalDate] {
//  val df = DateTimeFormatter.ofPattern("yyyyMMdd")
//  def convert(x: String): LocalDate = LocalDate.parse(x, df)
//}

@Command(name = "my-app", description = Array("\nThis is a simple test app.\n"))
class PicoCliApp extends Runnable {
  @Opt(names = Array("-c", "--count"), paramLabel = "COUNT", description = Array("the count (default: ${DEFAULT-VALUE})"))
  var count: Int = 5

  @Opt(names = Array("-d", "--dir"), paramLabel = "DIR", description = Array("the directory (default: ${DEFAULT-VALUE})"))
  var _dir: File = null

  def dir = Option(_dir)

  @Opt(names = Array("-D", "--date"), paramLabel = "DATE", description = Array("the directory (default: ${DEFAULT-VALUE})"),
    required = true,
//    converter = Array(classOf[LocalDateConverter])
  )
  var date: LocalDate = LocalDate.now

  @Opt(names = Array("-h", "--help"), usageHelp = true, description = Array("print this help and exit"))
  var helpRequested: Boolean = false

  def run(): Unit = {
    if (helpRequested) {
      new CommandLine(this).usage(System.err)
    } else {
      for (i <- 0 until count) {
        println(s"hello world ${i}...")
      }
    }
  }
}

object PicoCliApp extends App {
  val cmd = CommandLine.populateCommand(new PicoCliApp(), args: _*)
  println("count", cmd.count)
  println("dir", cmd.dir)
  println("date", cmd.date)
  CommandLine.run(new PicoCliApp(), System.err, args: _*)
}
