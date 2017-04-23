from necrobot.gsheet.sheetutil import num_to_colname


class SheetCell(object):
    def __init__(self, row, col, wks_name=None):
        self.row = row
        self.col = col
        self.wks_name = wks_name

        _cell_str = '{0}{1}'.format(num_to_colname(self.col), self.row)
        if wks_name:
            self._cell_str = "'{0}'!{1}".format(wks_name, _cell_str)
        else:
            self._cell_str = _cell_str

    def __str__(self):
        return self._cell_str
