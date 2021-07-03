
from docutils import nodes
from docutils.parsers.rst import Directive, states, directives

from rhombus.lib.utils import get_dbhandler
from rhombus.lib.tags import literal

class EnumKeyList(Directive):

    required_arguments = 1
    has_content = False

    def run(self):

        ek_group = self.arguments[0].strip()
        dbh = get_dbhandler()
        eks = list(dbh.list_ekeys(ek_group))

        data = [ (ek.key, ek.desc) for ek in eks ]
        tbl = create_table(("Key", "Description"), data, [30, 40])

        return tbl

directives.register_directive('list_ekeys', EnumKeyList)


def create_table(header, data, colwidths=None):

    table = nodes.table()

    tgroup = nodes.tgroup(cols=len(header))
    table += tgroup
    for colwidth in colwidths:
        tgroup += nodes.colspec(colwidth=colwidth)

    thead = nodes.thead()
    tgroup += thead
    thead += create_table_row(header)

    tbody = nodes.tbody()
    tgroup += tbody

    for data_row in data:
        tbody += create_table_row(data_row)

    return [table]


def create_table_row(row_cells):
    row = nodes.row()
    for cell in row_cells:
        entry = nodes.entry()
        row += entry
        entry += nodes.paragraph(text=cell)
    return row
