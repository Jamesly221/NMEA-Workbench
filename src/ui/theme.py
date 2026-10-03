from tkinter import ttk

BG = '#edf2f7'
NAVY = '#13283f'
INK = '#172e46'
MUTED = '#53677d'
TEAL = '#007e87'


def apply(root):
    root.configure(bg=BG)
    root.option_add('*Font', ('Segoe UI', 10))
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', font=('Segoe UI', 10), background=BG, foreground=INK)
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=INK)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('Title.TLabel', font=('Segoe UI', 19, 'bold'))
    style.configure('TButton', padding=(12, 8), background='white')
    style.map('TButton', background=[('active', '#dce8ef')])
    style.configure('Accent.TButton', background=TEAL, foreground='white')
    style.map('Accent.TButton', background=[('active', '#00656c')], foreground=[('active', 'white')])
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', padding=(22, 12), background='#dce5ef')
    style.map('TNotebook.Tab', background=[('selected', 'white')], foreground=[('selected', TEAL)])
    style.configure('Treeview', background='white', fieldbackground='white', rowheight=31, borderwidth=0)
    style.configure('Treeview.Heading', background='#dce5ef', font=('Segoe UI', 10, 'bold'), padding=7)
    style.map('Treeview', background=[('selected', '#007e87')], foreground=[('selected', 'white')])
