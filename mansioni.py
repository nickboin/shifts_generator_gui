import tkinter as tk
import tkinter.ttk as ttk
import input_helper
import gui

# TODO salvare finestra di dettaglio per uso mutuale

class Mansioni(tk.Toplevel):

    __input_file_path:str
    __is_generate_running:bool

    def __init__(self, parent_window:gui.GUI, input_file_path, is_generate_running:bool=False, **kwargs):
        super().__init__(master=parent_window, **kwargs)
        self.withdraw() # stay hidden until window has been centered

        self.title("Mansioni")
        self.parent_window = parent_window

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind("<Escape>", self.on_window_close)

        # ---- DEFINIZIONE FRAMES PRINCIPALI ----
        # FRAME for the buttons
        self.frm_buttons = ttk.Frame(master=self, padding=10)
        self.frm_buttons.grid(row=0, column=0, sticky="ew")
        # FRAME for the list
        self.frm_treeview = ttk.Frame( master=self, padding=10)
        self.frm_treeview.grid(row=1, column=0, sticky="nesw")

        # enable window resizing, treeview frame is the one to expand
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)
        self.frm_treeview.columnconfigure(index=0, weight=1)
        self.frm_treeview.rowconfigure(index=0, weight=1)

        self.__is_generate_running = is_generate_running
        self.__input_file_path = input_file_path
        self.inputHelper = input_helper.InputHelper(self.__input_file_path)

        # FRAME for the buttons
        ttk.Label(master=self.frm_buttons, text="Elenco mansioni:").pack(side="left", anchor="ne")

        # SUB-FRAME hidden to contain edit and view selected item
        self.frm_edit_view = ttk.Frame( master=self.frm_buttons, relief="ridge") # highlightbackground="black", highlightthickness=1 )
        ttk.Label(master=self.frm_edit_view, text="Selezione:").grid(row=0, column=0, padx=5, pady=5)
        self.btn_edit = ttk.Button(master=self.frm_edit_view, text="Modifica", command=self.edit_button_pressed)
        self.btn_edit.grid(row=0, column=1, padx=5, pady=5)
        self.btn_view = ttk.Button(master=self.frm_edit_view, text="Dettagli", command=self.view_button_pressed)
        self.btn_view.grid(row=0, column=2, padx=5, pady=5)
        # to show the frame with the buttons:
        # self.frm_edit_view.pack(padx=5, expand=True)
        
        self.btn_add = ttk.Button(master=self.frm_buttons, text="Aggiungi", command=self.add_button_pressed)
        self.btn_add.pack(side="right", pady=6, anchor="se")

        # FRAME per l'elenco
        colonne_headers = { "job":{"header":"Mansione", "width":250}, 
                            "location":{"header":"Sede", "width":50}, 
                            "category":{"header":"Categoria", "width":150}, 
                            "days":{"header":"Giorni", "width":150}, 
                            "time":{"header":"Orario", "width":130} }
        self.treeview = ttk.Treeview(master=self.frm_treeview, columns=tuple(colonne_headers.keys()), show="headings", selectmode="browse")
        for header_id in colonne_headers.keys():
            self.treeview.heading(header_id, text=colonne_headers.get(header_id).get("header"))
            self.treeview.column(header_id, minwidth=50, width=colonne_headers.get(header_id).get("width"))
        self.treeview.bind("<<TreeviewSelect>>", self.treeview_item_selected)
        self.treeview.bind("<Double-Button-1>", self.view_button_pressed)
        self.treeview.bind("<Double-Button-2>", self.edit_button_pressed)
        self.bind("<F5>", self.refreshTable)
        
        self.populateTable()

        self.treeview.grid(row=0, column=0, sticky="nesw")

        # scrollbar
        self.treeview_scrollbar = ttk.Scrollbar(self.frm_treeview, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=self.treeview_scrollbar.set)
        self.treeview_scrollbar.grid(row=0, column=1, sticky="ns")

        if is_generate_running:
            self.btn_edit.configure(state="disabled")
            self.btn_add.configure(state="disabled")

        # after placing all elements, set the created wundow size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())
        
        gui.center_window(self)
        self.deiconify()

    
    def populateTable(self):
        # populate treeview
        row_num = self.inputHelper.getJobCount()
        job_name_list = self.inputHelper.getFullSanitizedJobNameList()
        job_location_list = self.inputHelper.getSanitizedJobLocationList()
        job_category_list = self.inputHelper.getSanitizedJobCategoriesList()
        job_days_list = self.inputHelper.getSanitizedJobDayList()
        job_time_list = self.inputHelper.getSanitizedJobTimeList()
        for i in range(0, row_num):
            tree_line = ( job_name_list[i], 
                         job_location_list[i], 
                         job_category_list[i],
                         job_days_list[i],
                         job_time_list[i] )
            self.treeview.insert("", tk.END, values=tree_line)

    def refreshTable(self, event=None):
        self.inputHelper.reload_from_file()
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        self.update()
        self.populateTable()


    def on_window_close(self, event=None):
        try:
            if self.master.winfo_exists():
                if (self.master.state() == "withdrawn"):
                    self.master.deiconify()
            else:
                self.master.deiconify()
        except tk.TclError:
            # the exception get thrown when the parent_window has been already closed
            self.parent_window = gui.GUI()
        finally:
            self.destroy()

    def treeview_item_selected(self, event=None):
        # show edit and view buttons if not already shown
        if not self.frm_edit_view.winfo_ismapped():
            self.frm_edit_view.pack(anchor="e", padx=5, expand=True)

    def is_a_row_selected(self):
        return bool(len(self.treeview.selection()))
    
    def getSelectedInputKey(self):
        item = self.treeview.selection()[0] # selection return a tuple, but treeview.selectionmode="browse", so only 1 element
        item = self.inputHelper.getJobKey_byIndex(self.treeview.index(item)) # effective non-sanitized key value in json file
        return item
        
    def edit_button_pressed(self, event=None):
        import mansione
        if self.is_a_row_selected():
            mansione.Mansione(parent_window=self, selected_key=self.getSelectedInputKey(), action="edit", input_file_path=self.__input_file_path)
        
    def view_button_pressed(self, event=None):
        import mansione
        if self.is_a_row_selected():
            mansione.Mansione( 
                parent_window=self, 
                selected_key=self.getSelectedInputKey(), 
                action="view", 
                input_file_path=self.__input_file_path, 
                is_generate_running=self.__is_generate_running )
        
    def add_button_pressed(self, event=None):
        import mansione
        mansione.Mansione(parent_window=self, selected_key=None, action="add", input_file_path=self.__input_file_path)