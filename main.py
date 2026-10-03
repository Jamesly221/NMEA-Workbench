"""Run with Python 3.11+; packaging uses this same entry point."""
import sys
import tkinter as tk
from src.ui.app import Workbench


def main():
    root = tk.Tk()
    app = Workbench(root)
    if '--smoke-test' in sys.argv:
        # Exercise real widgets and log selection in CI, including frozen resources.
        root.update()
        assert len(app.catalog) >= 4
        app.use_example('RMC')
        assert app.current.checksum == 'Valid'
        assert len(app.fields.get_children()) >= 11
        app.load_log(app.base / 'examples' / 'logs' / 'demo.txt')
        for _ in range(30):
            root.update()
        assert len(app.log_records) == 9
        app.log_table.selection_set('1')
        app.log_selected(None)
        assert app.current.kind == 'RMC'
        root.destroy()
        return
    root.mainloop()


if __name__ == '__main__':
    main()
