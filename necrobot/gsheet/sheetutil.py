import string
import unittest


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


class SheetRange(object):
    def __init__(self, ul_cell=None, lr_cell=None, wks_name=None, range_name=None):
        self.ul_cell = ul_cell
        self.lr_cell = lr_cell
        self.wks_name = wks_name
        self.range_name = range_name

        if range_name is not None:
            self._init_from_range_name(range_name)
        else:
            self._update_range_name()

    def __str__(self):
        return self.range_name

    @property
    def left(self):
        return self.ul_cell[1]

    @property
    def right(self):
        return self.lr_cell[1]

    @property
    def top(self):
        return self.ul_cell[0]

    @property
    def bottom(self):
        return self.lr_cell[0]

    def barf(self):
        return '{2}:{0}:{1} -- {3}'.format(self.ul_cell, self.lr_cell, self.wks_name, self.range_name)

    def get_offset_by(self, row, col):
        new_ul = (self.ul_cell[0] + row, self.ul_cell[1] + col,)
        new_lr = (self.lr_cell[0] + row, self.lr_cell[1] + col,)
        return SheetRange(ul_cell=new_ul, lr_cell=new_lr, wks_name=self.wks_name)

    def _init_from_range_name(self, range_name):
        args = range_name.split('!')
        if len(args) == 2:
            self.wks_name = args[0].strip("'")
            args.pop(0)

        range_args = args[0].split(':')
        self.ul_cell = self._get_cell_as_int_pair(range_args[0])
        self.lr_cell = self._get_cell_as_int_pair(range_args[1])

    def _update_range_name(self):
        self.range_name = get_range_name(ul_cell=self.ul_cell, lr_cell=self.lr_cell, wks_name=self.wks_name)

    @staticmethod
    def _get_cell_as_int_pair(cell_str):
        col_str = ''
        row_str = ''
        for char in cell_str:
            if char in string.ascii_uppercase:
                col_str += char
            else:
                row_str += char

        col_str = col_str[::-1]  # Reverse this string
        col_num = 0
        for idx, char in enumerate(col_str):
            col_num += pow(26, idx)*(string.ascii_uppercase.index(char) + 1)

        return int(row_str), col_num


def get_range_name(ul_cell: tuple, lr_cell: tuple, wks_name=None) -> str:
    """Get a string representing the range specified.
    :param ul_cell: A 2-tuple(int) giving the upper-left cell coordinates
    :param lr_cell: A 2-tuple(int) giving the lower-left cell coordinates
    :param wks_name: An Optional[str] giving the worksheet name
    :return: The GSheet name of the range specified (e.g. 'Sheet1!'B3:C4)
    """

    range_name = '{0}{1}:{2}{3}'.format(
        num_to_colname(ul_cell[1]), ul_cell[0],
        num_to_colname(lr_cell[1]), lr_cell[0]
    )
    if wks_name is None:
        return range_name
    else:
        return "'{0}'!{1}".format(wks_name, range_name)


def num_to_colname(num: int) -> str:
    """Convert the given number to a gsheet column name.
    :param num: The column number to be converted
    :return: A string giving the name of the gsheet column (e.g. 'AB' for num=28)
    :exception IndexError: If num <= 0
    """

    if num <= 0:
        raise IndexError

    colname = ''
    while num != 0:
        mod = (num - 1) % 26
        num = int((num - mod) // 26)
        colname += string.ascii_uppercase[mod]
    return colname[::-1]    # [::-1] reverses the sequence


class TestSheetUtil(unittest.TestCase):
    def test_num_to_colname(self):
        self.assertEqual(num_to_colname(1), 'A')
        self.assertEqual(num_to_colname(5), 'E')
        self.assertEqual(num_to_colname(26), 'Z')
        self.assertEqual(num_to_colname(28), 'AB')
        self.assertEqual(num_to_colname(701), 'ZY')
        self.assertEqual(num_to_colname(704), 'AAB')
        self.assertRaises(IndexError, num_to_colname, 0)

    def test_sheetrange(self):
        sheetrange = SheetRange(range_name="'Sheet1'!A10:AB22")
        self.assertEqual(sheetrange.left, 1)
        self.assertEqual(sheetrange.right, 28)
        self.assertEqual(sheetrange.top, 10)
        self.assertEqual(sheetrange.bottom, 22)
        self.assertEqual(sheetrange.wks_name, 'Sheet1')

        sheetrange2 = SheetRange(ul_cell=(3, 15), lr_cell=(17, 27), wks_name='Hello')
        self.assertEqual(str(sheetrange2), "'Hello'!O3:AA17")
