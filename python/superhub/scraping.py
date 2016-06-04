from utils.table import Table


def get_table(table_elem, caption=None):
    return Table(
        caption=caption or get_caption(table_elem),
        headers=get_headers(table_elem),
        rows=get_rows(table_elem),
    )


def get_caption(table_elem):
    captions = table_elem.find_elements_by_xpath("caption")
    return captions[0].text if captions else None


def get_headers(table_elem):
    return [get_value(_) for _ in table_elem.find_elements_by_xpath("thead/tr/*")]


def get_rows(table_elem):
    rows = []
    for tr in table_elem.find_elements_by_xpath("tbody/tr"):
        values = [get_value(td) for td in tr.find_elements_by_tag_name("td")]
        rows.append(values)
    return rows


def get_value(td):
    inputs_ = td.find_elements_by_xpath("input")
    if inputs_:
        return inputs_[0].is_selected()
    else:
        return td.text.strip()
