class Table:
    def __init__(self, caption, headers, rows):
        self.caption = caption
        self.headers = headers
        self.rows = rows

    def __str__(self):
        return "Table(caption={}, headers={}, rows={})".format(self.caption, self.headers, len(self.rows))

    def is_empty(self):
        return not (self.has_caption() or self.has_headers() or self.has_values())

    def has_caption(self):
        return self.caption not in (None, "")

    def has_headers(self):
        return any(len(str(_)) > 0 for _ in self.headers)

    def has_values(self):
        def has(row):
            return any(len(str(_)) > 0 for _ in row)
        return any(has(_) for _ in self.rows)

    def pretty_print(self, caption=True):
        n = len(self.headers)
        widths = [max([len(str(_[idx])) for _ in [self.headers] + self.rows]) for idx in range(n)]
        fmt1 = "+-" + "-+-".join(["{:-<%d}" % _ for _ in widths]) + "-+"
        fmt2 = "| " + " | ".join(["{!s: <%d}" % _ for _ in widths]) + " |"
        sep = fmt1.format(*([""] * n))

        if self.caption and caption:
            print(self.caption)
        print(sep)
        print(fmt2.format(*self.headers))
        print(sep)
        for row in self.rows:
            print(fmt2.format(*row))
        print(sep)


if __name__ == "__main__":
    Table(None, ["red", "green", "blue"], [["alabama", "box", ""]]).pretty_print()
    print()
    Table("XXX", [], []).pretty_print()
