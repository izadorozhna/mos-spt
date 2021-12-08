import texttable as tt


class helpers(object):

    def __init__(self):
        pass

    def draw_table_with_results(self, global_results):
        tab = tt.Texttable()
        header = [
            'node name 1',
            'node name 2',
            'network',
            'bandwidth >',
            'bandwidth <',
        ]
        tab.set_cols_align(['l', 'l', 'l', 'l', 'l'])
        tab.set_cols_width([27, 27, 15, 20, '20'])
        tab.header(header)
        for row in global_results:
            tab.add_row(row)
        s = tab.draw()
        print(s)
