"""Reference, decoder and incremental log viewer; all processing is local."""
import csv
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from urllib.parse import urlparse

from src import __version__
from src.paths import project_root
from src.nmea.catalog import load_catalog
from src.nmea.parser import parse
from src.ui import theme

MAX_BYTES = 20 * 1024 * 1024
MAX_LINES = 25000


def table(parent, columns, widths, height=10):
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True)
    view = ttk.Treeview(frame, columns=columns, show='headings', height=height, selectmode='browse')
    for name, width in zip(columns, widths):
        view.heading(name, text=name)
        view.column(name, width=width, minwidth=55, stretch=True)
    y = ttk.Scrollbar(frame, orient='vertical', command=view.yview)
    x = ttk.Scrollbar(frame, orient='horizontal', command=view.xview)
    view.configure(yscrollcommand=y.set, xscrollcommand=x.set)
    view.grid(row=0, column=0, sticky='nsew')
    y.grid(row=0, column=1, sticky='ns')
    x.grid(row=1, column=0, sticky='ew')
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    return view


def text_panel(parent, height=5):
    frame = ttk.Frame(parent)
    frame.pack(fill='both', expand=True, pady=(8, 0))
    text = tk.Text(frame, height=height, wrap='word', relief='flat', padx=14, pady=12,
                   background='white', foreground=theme.INK, font=('Segoe UI', 10))
    scroll = ttk.Scrollbar(frame, command=text.yview)
    text.configure(yscrollcommand=scroll.set)
    text.pack(side='left', fill='both', expand=True)
    scroll.pack(side='right', fill='y')
    text.configure(state='disabled')
    return text


def set_text(widget, value):
    widget.configure(state='normal')
    widget.delete('1.0', 'end')
    widget.insert('1.0', value)
    widget.configure(state='disabled')


class Workbench:
    def __init__(self, root):
        self.root = root
        self.base = project_root()
        self.catalog, self.catalog_errors = load_catalog(self.base / 'data' / 'sentences')
        self.current = None
        self.ref_code = None
        self.log_records = []
        self.generation = 0
        self.log_loading = False
        root.title(f'NMEA Workbench | {__version__}')
        root.geometry('1180x820')
        root.minsize(900, 680)
        theme.apply(root)
        icon = self.base / 'assets' / 'icons' / 'workbench.png'
        if icon.exists():
            self.icon = tk.PhotoImage(file=icon)
            root.iconphoto(True, self.icon)
        banner = tk.Frame(root, bg=theme.NAVY, padx=25, pady=18)
        banner.pack(fill='x')
        tk.Label(banner, text='NMEA WORKBENCH', bg=theme.NAVY, fg='white', font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        tk.Label(banner, text='Explore the messages behind navigation.', bg=theme.NAVY, fg='#b7d5df', font=('Segoe UI', 11)).pack(anchor='w', pady=(5, 0))
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill='both', expand=True, padx=20, pady=(16, 8))
        self.decoder_tab = ttk.Frame(self.tabs, padding=18)
        self.reference_tab = ttk.Frame(self.tabs, padding=18)
        self.log_tab = ttk.Frame(self.tabs, padding=18)
        for frame, title in ((self.decoder_tab, 'Message decoder'), (self.reference_tab, 'Sentence reference'), (self.log_tab, 'Log viewer')):
            self.tabs.add(frame, text=title)
        self.build_decoder()
        self.build_reference()
        self.build_log()
        self.status = tk.StringVar(value='Offline • NMEA 0183 • Reference, decoding and saved logs')
        ttk.Label(root, textvariable=self.status, style='Muted.TLabel', padding=(22, 8)).pack(fill='x')
        root.bind('<Control-o>', lambda _: self.choose_log())
        root.bind('<Control-Return>', lambda _: self.decode())
        self.populate_reference()
        if self.catalog:
            self.input.set(next(iter(self.catalog.values()))['example'])
            self.decode()
        if self.catalog_errors:
            root.after(150, lambda: messagebox.showwarning('Reference files need attention', '\n'.join(self.catalog_errors)))

    def build_decoder(self):
        ttk.Label(self.decoder_tab, text='Make a sentence readable', style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.decoder_tab, text='Paste one complete sentence. Empty fields stay visible; checksum and data issues are reported separately.',
                  style='Muted.TLabel', wraplength=950).pack(anchor='w', pady=(7, 15))
        bar = ttk.Frame(self.decoder_tab)
        bar.pack(fill='x')
        self.input = tk.StringVar()
        self.entry = ttk.Entry(bar, textvariable=self.input, font=('Consolas', 11))
        self.entry.pack(side='left', fill='x', expand=True, ipady=8, padx=(0, 10))
        self.entry.bind('<Return>', lambda _: self.decode())
        ttk.Button(bar, text='Decode', style='Accent.TButton', command=self.decode).pack(side='right')
        examples = ttk.Frame(self.decoder_tab)
        examples.pack(fill='x', pady=12)
        ttk.Label(examples, text='Try an example:').pack(side='left', padx=(0, 10))
        for code in ('RMC', 'GGA', 'VTG', 'HDT'):
            ttk.Button(examples, text=code, command=lambda c=code: self.use_example(c)).pack(side='left', padx=(0, 6))
        ttk.Button(examples, text='Copy sentence', command=self.copy_sentence).pack(side='right')
        self.summary = tk.StringVar(value='Ready to decode')
        ttk.Label(self.decoder_tab, textvariable=self.summary, font=('Segoe UI', 11, 'bold'), wraplength=980).pack(anchor='w', pady=(5, 10))
        self.fields = table(self.decoder_tab, ('#', 'Field', 'Raw value', 'Decoded value'), (55, 220, 160, 480))
        self.fields.bind('<<TreeviewSelect>>', self.field_selected)
        self.explanation = text_panel(self.decoder_tab, height=5)

    def use_example(self, code):
        if code not in self.catalog:
            messagebox.showinfo('Example unavailable', f'No valid {code} reference file is loaded.')
            return
        self.input.set(self.catalog[code]['example'])
        self.tabs.select(self.decoder_tab)
        self.decode()

    def decode(self):
        self.current = parse(self.input.get(), self.catalog)
        self.fields.delete(*self.fields.get_children())
        for row in self.current.rows:
            self.fields.insert('', 'end', iid=str(row[0]), values=row[:4])
        m = self.current
        self.summary.set(f'{m.talker or "—"} / {m.kind or "Unknown"}   •   Checksum: {m.checksum}   •   {len(m.values)} fields   •   {m.health}')
        entry = self.catalog.get(m.kind, {})
        details = [entry.get('description', 'No supported sentence definition.'),
                   f'Checksum supplied: {m.supplied or "none"} | Computed: {m.expected or "unavailable"}',
                   'Checksum integrity is separate from sensor status and measurement accuracy.']
        if m.checksum != 'Valid':
            details.append('Checksum warning: treat this as an inspection of unverified data.')
        if m.issues:
            details.append('Review:\n' + '\n'.join(m.issues))
        if entry.get('notes'):
            details.append(entry['notes'])
        set_text(self.explanation, '\n\n'.join(details))

    def field_selected(self, _):
        selection = self.fields.selection()
        if selection and self.current:
            row = self.current.rows[int(selection[0]) - 1]
            set_text(self.explanation, f'{row[1]}\n\n{row[4]}\n\nRaw: {row[2]}\nDecoded: {row[3]}\n\nChecksum: {self.current.checksum}. Select Decode again to see the overall report.')

    def copy_sentence(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.input.get())
        self.status.set('Sentence copied to clipboard.')

    def build_reference(self):
        ttk.Label(self.reference_tab, text='A practical sentence library', style='Title.TLabel').pack(anchor='w')
        controls = ttk.Frame(self.reference_tab)
        controls.pack(fill='x', pady=12)
        self.search = tk.StringVar()
        self.search.trace_add('write', lambda *_: self.populate_reference())
        ttk.Label(controls, text='Search').pack(side='left', padx=(0, 10))
        ttk.Entry(controls, textvariable=self.search).pack(side='left', fill='x', expand=True, ipady=6)
        ttk.Button(controls, text='Reload reference files', command=self.reload_catalog).pack(side='right', padx=(10, 0))
        self.references = table(self.reference_tab, ('Type', 'Purpose'), (100, 650), height=4)
        self.references.bind('<<TreeviewSelect>>', self.reference_selected)
        self.ref_text = text_panel(self.reference_tab, height=12)
        buttons = ttk.Frame(self.reference_tab)
        buttons.pack(fill='x', pady=(12, 0))
        ttk.Button(buttons, text='Decode this example', style='Accent.TButton', command=lambda: self.use_example(self.ref_code)).pack(side='left')
        ttk.Button(buttons, text='Open source documentation', command=self.open_source).pack(side='left', padx=10)
        ttk.Label(buttons, text='Edit data/sentences/*.json to extend the library.', style='Muted.TLabel').pack(side='right')

    def populate_reference(self):
        self.references.delete(*self.references.get_children())
        query = self.search.get().lower()
        for code, entry in sorted(self.catalog.items()):
            if query in (code + ' ' + entry['title'] + ' ' + entry['description']).lower():
                self.references.insert('', 'end', iid=code, values=(code, entry['title']))
        children = self.references.get_children()
        self.ref_code = None
        set_text(self.ref_text, 'No matching entries.' if not children else 'Select a sentence type.')
        if children:
            self.references.selection_set(children[0])
            self.reference_selected(None)

    def reference_selected(self, _):
        selected = self.references.selection()
        if not selected:
            return
        self.ref_code = selected[0]
        entry = self.catalog[self.ref_code]
        fields = '\n'.join(f'{i}. {f["name"]}: {f["description"]}' for i, f in enumerate(entry['fields'], 1))
        set_text(self.ref_text, f'{self.ref_code} — {entry["title"]}\n\n{entry["description"]}\n\nEXAMPLE\n{entry["example"]}\n\nFIELDS\n{fields}\n\nLEARNING NOTES\n{entry["notes"]}\n\nSOURCE\n{entry["source"]}')

    def reload_catalog(self):
        self.catalog, errors = load_catalog(self.base / 'data' / 'sentences')
        self.populate_reference()
        self.decode()
        self.status.set(f'Loaded {len(self.catalog)} reference entries.')
        if errors:
            messagebox.showwarning('Reference files need attention', '\n'.join(errors))

    def open_source(self):
        if self.ref_code:
            url = self.catalog[self.ref_code]['source']
            if urlparse(url).scheme == 'https':
                webbrowser.open(url)
            else:
                messagebox.showinfo('Source link', 'The source must be an HTTPS URL.')

    def build_log(self):
        ttk.Label(self.log_tab, text='Inspect a recorded stream', style='Title.TLabel').pack(anchor='w')
        ttk.Label(self.log_tab, text='One sentence per line. Select a row to decode it. Logs are processed locally.', style='Muted.TLabel').pack(anchor='w', pady=(7, 12))
        bar = ttk.Frame(self.log_tab)
        bar.pack(fill='x')
        ttk.Button(bar, text='Open log…', style='Accent.TButton', command=self.choose_log).pack(side='left')
        ttk.Button(bar, text='Load demo', command=lambda: self.load_log(self.base / 'examples' / 'logs' / 'demo.txt')).pack(side='left', padx=8)
        ttk.Button(bar, text='Export report CSV…', command=self.export_log).pack(side='right')
        ttk.Label(bar, text='Filter:').pack(side='left', padx=(20, 6))
        self.log_filter = tk.StringVar(value='All')
        combo = ttk.Combobox(bar, textvariable=self.log_filter, values=('All', 'Needs review', 'RMC', 'GGA', 'VTG', 'HDT'), width=15, state='readonly')
        combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>', lambda _: self.refresh_log())
        self.log_summary = tk.StringVar(value='No log loaded. Try the demo to see valid, missing and damaged checksums.')
        ttk.Label(self.log_tab, textvariable=self.log_summary, wraplength=980).pack(anchor='w', pady=12)
        self.log_table = table(self.log_tab, ('Line', 'Type', 'Checksum', 'Review', 'Sentence'), (60, 75, 100, 90, 600))
        self.log_table.bind('<<TreeviewSelect>>', self.log_selected)
        ttk.Label(self.log_tab, text='Limits: 20 MB / 25,000 lines. Timestamp prefixes, proprietary decoding and AIS multipart decoding are outside this version.',
                  wraplength=950, style='Muted.TLabel').pack(anchor='w', pady=(12, 0))

    def choose_log(self):
        path = filedialog.askopenfilename(title='Open NMEA log', filetypes=[('Navigation logs', '*.txt *.log *.nmea'), ('All files', '*.*')])
        if path:
            from pathlib import Path
            self.load_log(Path(path))

    def load_log(self, path):
        try:
            if path.stat().st_size > MAX_BYTES:
                raise ValueError('Log exceeds the 20 MB limit.')
            text = path.read_text(encoding='utf-8-sig', errors='replace')
            lines = text.splitlines()
            if len(lines) > MAX_LINES:
                raise ValueError('Log exceeds the 25,000-line limit. Split it into smaller files.')
        except (OSError, ValueError) as exc:
            messagebox.showerror('Cannot open log', str(exc))
            return
        self.tabs.select(self.log_tab)
        self.generation += 1
        generation = self.generation
        self.log_records = []
        self.log_loading = True
        self.log_table.delete(*self.log_table.get_children())
        self.log_summary.set(f'Loading {path.name}…')
        indexed = [(n, line) for n, line in enumerate(lines, 1) if line.strip()]
        def batch(offset=0):
            if generation != self.generation:
                return
            for number, line in indexed[offset:offset + 200]:
                self.log_records.append((number, parse(line, self.catalog)))
            if offset + 200 < len(indexed):
                self.root.after(1, lambda: batch(offset + 200))
            else:
                self.log_loading = False
                good = sum(m.checksum == 'Valid' for _, m in self.log_records)
                review = sum(m.health != 'OK' for _, m in self.log_records)
                self.log_summary.set(f'{path.name}  •  {len(self.log_records)} messages  •  {good} valid checksums  •  {review} need review')
                self.refresh_log()
        batch()

    def refresh_log(self):
        self.log_table.delete(*self.log_table.get_children())
        generation = self.generation
        choice = self.log_filter.get()
        rows = [(n, m) for n, m in self.log_records if choice == 'All' or (choice == 'Needs review' and m.health != 'OK') or choice == m.kind]
        # Separate generation prevents an old filter insertion from continuing.
        self.render_generation = getattr(self, 'render_generation', 0) + 1
        render = self.render_generation
        def insert(offset=0):
            if generation != self.generation or render != self.render_generation:
                return
            for number, m in rows[offset:offset + 200]:
                self.log_table.insert('', 'end', iid=str(number), values=(number, m.kind or '—', m.checksum, m.health, m.raw))
            if offset + 200 < len(rows):
                self.root.after(1, lambda: insert(offset + 200))
        insert()

    def log_selected(self, _):
        selected = self.log_table.selection()
        if selected:
            row = self.log_table.item(selected[0], 'values')
            self.input.set(row[4])
            self.decode()
            self.tabs.select(self.decoder_tab)

    def export_log(self):
        if self.log_loading:
            messagebox.showinfo('Loading', 'Wait until the log finishes loading before exporting.')
            return
        if not self.log_records:
            messagebox.showinfo('No log', 'Load a log before exporting a report.')
            return
        path = filedialog.asksaveasfilename(title='Export full log report', defaultextension='.csv', filetypes=[('CSV report', '*.csv')])
        if path:
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as handle:
                    writer = csv.writer(handle)
                    writer.writerow(('Line', 'Talker', 'Type', 'Checksum', 'Computed checksum', 'Review', 'Issues', 'Sentence'))
                    for number, m in self.log_records:
                        writer.writerow((number, m.talker, m.kind, m.checksum, m.expected, m.health, '; '.join(m.issues), m.raw))
                self.status.set('Full log report exported.')
            except OSError as exc:
                messagebox.showerror('Export failed', str(exc))
