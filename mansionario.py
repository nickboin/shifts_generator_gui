import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
from ttkwidgets.autocomplete import AutocompleteCombobox
from tkinter.messagebox import showinfo, showerror
import input_helper
import gui


class Mansionario(tk.Toplevel):

    __input_file_path:str
    __is_generate_running:bool

    def __init__(self, parent_window: tk.Widget, input_file_path, is_generate_running:bool):
        super().__init__()
        self.title("Mansionario")
        self.parent_window = parent_window

        self.geometry("800x500")
        self.wm_minsize(width=700, height=205)

        # TODO: set minsize

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind("<Escape>", self.on_window_close)

        # ---- DEFINIZIONE FRAMES PRINCIPALI ----
        # FRAME header
        self.frm_header = ttk.Frame(master=self, padding=10)
        self.frm_header.grid(row=0, column=0, sticky="ew")
        # FRAME for the list
        self.frm_treeview = ttk.Frame(master=self, padding=10)
        self.frm_treeview.grid(row=1, column=0, sticky="nesw")

        # enable window resizing, treeview frame is the one to expand
        self.columnconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=1)
        self.frm_treeview.columnconfigure(index=0, weight=1)
        self.frm_treeview.rowconfigure(index=0, weight=1)

        self.__is_generate_running = is_generate_running
        self.__input_file_path = input_file_path
        self.inputHelper = input_helper.InputHelper(self.__input_file_path)

        # FRAME header
        self.viewmodes = ("per Medico", "per Mansione")
        self.var_cmb_viewmode = tk.StringVar(value=self.viewmodes[0])  # DEFAULT VIEWMODE SET HERE
        self.cmb_viewmode = ttk.Combobox(
            master=self.frm_header,
            textvariable=self.var_cmb_viewmode,
            values=self.viewmodes,
            width=13,
            state="readonly" )
        self.cmb_viewmode.bind("<<ComboboxSelected>>", self.cmb_viewmode_changed)
        self.cmb_viewmode.pack(side="left", anchor="e", pady=9)
        ttk.Button(
            master=self.frm_header, 
            text="i", width=3, 
            command=self.info_button_pressed ).pack(side="right", anchor="w", padx=5, pady=10)

        # SUB-FRAME with elements to operate on selected item
        self.frm_operations = ttk.Frame(master=self.frm_header, relief="ridge")
        self.rebuildOperationFrame()

        # FRAME per l'elenco
        column_headers = {
            "job": {"header": "Mansione", "width": 250},
            "operators": {"header": "Medici qualificati", "width": 750},
        }
        self.treeview = ttk.Treeview(
            master=self.frm_treeview,
            columns=tuple(column_headers.keys()),
            show="headings",
            selectmode="extended" )
        for header_id in column_headers.keys():
            self.treeview.heading( header_id, text=column_headers.get(header_id).get("header") )
            self.treeview.column( header_id, minwidth=50, width=column_headers.get(header_id).get("width") )
        self.treeview.bind("<<TreeviewSelect>>", self.treeview_item_selected)
        self.treeview.bind("<Double-Button-1>", self.doubleClick_treeview)
        self.bind("<F5>", self.refreshTable)

        self.populateTable()

        self.treeview.grid(row=0, column=0, sticky="nesw")

        # scrollbars
        self.treeview_yscrollbar = ttk.Scrollbar(self.frm_treeview, orient=tk.VERTICAL, command=self.treeview.yview)
        self.treeview.configure(yscroll=self.treeview_yscrollbar.set)
        self.treeview_yscrollbar.grid(row=0, rowspan=2, column=1, sticky="ns")
        self.treeview_xscrollbar = ttk.Scrollbar(self.frm_treeview, orient=tk.HORIZONTAL, command=self.treeview.xview)
        self.treeview.configure(xscroll=self.treeview_xscrollbar.set)
        self.treeview_xscrollbar.grid(row=1, column=0, sticky="ew")
        # TODO: fix horizontal scrollbar
        
        gui.center_window(self)


    def rebuildOperationFrame(self):
        # delete the frame and replace elements
        try:
            if (self.frm_operations.winfo_ismapped()):
                self.frm_operations.destroy()
        except tk.TclError:
            pass
        # the frame now doesn't exist for sure

        self.frm_operations = ttk.Frame(master=self.frm_header, relief="ridge")  # highlightbackground="black", highlightthickness=1 )
        
        stato = "disabled" if self.__is_generate_running else "normal"

        if (self.var_cmb_viewmode.get().lower() == "per mansione"):
            ttk.Label(master=self.frm_operations, text="Mansioni selezionate:").pack(side="left", padx=5, pady=5)
            ttk.Button( 
                master=self.frm_operations, 
                text="Aggiungi Medico", 
                command=self.add_medic_button_pressed, 
                state=stato 
                ).pack(side="right", padx=5, pady=5)
            ttk.Button( 
                master=self.frm_operations, 
                text="Rimuovi Medico", 
                command=self.rm_medic_button_pressed, 
                state=stato 
                ).pack(side="right", padx=5, pady=5)

            
        elif (self.var_cmb_viewmode.get().lower() == "per medico"):
            ttk.Label(master=self.frm_operations, text="Medici selezionati:").pack(side="left", padx=5, pady=5)
            ttk.Button(
                master=self.frm_operations,
                text="Aggiungi Mansione",
                command=self.add_job_button_pressed, 
                state=stato  
                ).pack(side="right", padx=5, pady=5)
            ttk.Button(
                master=self.frm_operations,
                text="Rimuovi Mansione",
                command=self.rm_job_button_pressed, 
                state=stato  
                ).pack(side="right", padx=5, pady=5)
            
        self.btn_view_details = ttk.Button(
            master=self.frm_operations,
            text="Dettaglio",
            command=self.doubleClick_treeview )
        # self.btn_view_medic.pack(side="right", padx=5, pady=5) # TO SHOW ONLY WHEN 1 ELEMENT IS SELECTED

        # to show the frame with the buttons:
        # self.frm_edit_view.pack(padx=5, expand=True)


    def populateTable(self):
        self.update()
        # redefine column headers
        column_headers = dict()
        if (self.var_cmb_viewmode.get().lower() == "per medico"):
            column_headers = {
                "operator": {"header": "Medici", "width": 20, "stretch": False},
                "jobs": {"header": "Mansioni assegnate", "width": 2480, "stretch": True},
            }
        elif (self.var_cmb_viewmode.get().lower() == "per mansione"):
            column_headers = {
                "job": {"header": "Mansione", "width": 50, "stretch": False},
                "operators": {"header": "Medici qualificati", "width": 2450, "stretch": True},
            }
        
        self.treeview.configure(columns=tuple(column_headers.keys()))
        for header_id in column_headers.keys():
            self.treeview.heading( 
                header_id, 
                text=column_headers.get(header_id).get("header"), 
                anchor="w" )
            self.treeview.column( 
                header_id, 
                minwidth=50, 
                width=column_headers.get(header_id).get("width"), 
                stretch=column_headers.get(header_id).get("stretch") )
            # TODO fix the width thing

        # populate rows
        if (self.var_cmb_viewmode.get().lower() == "per medico"):
            job_operators = list(self.inputHelper.getSanitizedOperatorSet())
            job_operators.sort()
            for operator in job_operators:
                job_keys_list = self.inputHelper.getOperatorJobKeysList( operator, sanitized_operator=True )
                clean_job_list = self.sanitize_job_list(job_keys_list=job_keys_list)
                tree_line = (operator, self.merge_string_list(clean_job_list))
                self.treeview.insert("", tk.END, values=tree_line)

        elif (self.var_cmb_viewmode.get().lower() == "per mansione"):
            self.job_keys_list_treeview = self.inputHelper.getJobKeyList()  # saving in main class, needed for index retrieving
            self.job_keys_list_treeview.sort()
            for job_key in self.job_keys_list_treeview:
                job_name = self.inputHelper.getFullSanitizedJob(job_key)
                job_operators_list = self.inputHelper.getSanitizedJobOperatorsList( job_key )
                tree_line = (job_name, self.merge_string_list(job_operators_list))
                self.treeview.insert("", tk.END, values=tree_line)
        
        # re_set column width (auto)
        used_font = tkfont.nametofont("TkTextFont")     # this is the default font used into treeview
        # find the maximum lenght of columns:
        column_names = list(column_headers.keys())
        for line in self.treeview.get_children():
            row = self.treeview.item(line).get("values")
            for i in range(len(column_names)):
                cur_width = used_font.measure(text=row[i])
                if (cur_width > column_headers[column_names[i]]["width"]):
                    column_headers[column_names[i]]["width"] = cur_width
        # set the column width
        for header_id in column_names:
            self.treeview.column(header_id, width=(column_headers.get(header_id).get("width")+10) )
        

    def refreshTable(self, event=None):
        self.inputHelper.reload_from_file()
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        self.populateTable()

    def merge_string_list(self, string_list):
        merged = ""
        if ( isinstance(string_list, list) | isinstance(string_list, tuple) | isinstance(string_list, set) ):
            for stringa in string_list:
                merged += stringa + "; "
            merged = merged[0:-2]  # remove final ", "
        else:
            raise ValueError("string_list is not a list/tuple/set!")
        return merged


    def on_window_close(self, event=None):
        try:
            if self.parent_window.winfo_exists():
                if (self.parent_window.state() == "withdrawn"):
                    self.parent_window.deiconify()
            else:
                self.parent_window.deiconify()
        except tk.TclError:
            # the exception get thrown when the parent_window has been already closed
            self.parent_window = gui.GUI()
        finally:
            # close eventuals input dialogs (MansionarioQuickEdit)
            for widget in self.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    widget.destroy()
            self.destroy()


    def treeview_item_selected(self, event=None):
        selected_item_num = len(self.treeview.selection())
        try:
            # when nothing is selected, hide the operation frame
            if selected_item_num == 0:
                if self.frm_operations.winfo_ismapped():
                    self.frm_operations.pack_forget()
            elif selected_item_num > 0:
                # when at least 1 item is selected, show the operations frame if not already shown
                if not self.frm_operations.winfo_ismapped():
                    self.frm_operations.pack(anchor="e", padx=5, expand=True)

                # in viewmode "per mansione", show "Dettagli" button only when 1 row on treeview is selected
                if (selected_item_num == 1) & ( not self.btn_view_details.winfo_ismapped() ):
                    self.btn_view_details.pack(side="right", padx=5, pady=5)
                elif (selected_item_num != 1) & self.btn_view_details.winfo_ismapped():
                    self.btn_view_details.pack_forget()
        except tk.TclError:
            pass


    def cmb_viewmode_changed(self, event=None):
        self.rebuildOperationFrame()
        self.refreshTable()

    # @staticmethod --- NOPE, i need self.inputHelper UNLESS i make also sanitization methods static
    def sanitize_job_list(self, job_keys_list):
        ''' rreceive a list of job_keys, returns a list of jobs formatted as "Location: Name" '''
        sanitized_list = list()
        for job_key in job_keys_list:
            job_name = self.inputHelper.getSanitizedJobName(job_key)
            job_location = self.inputHelper.getSanitizedJobLocation(job_key)
            sanitized_list.append( (job_location + ": " + job_name) )
        return sanitized_list

    def is_1_row_selected(self):
        return (len(self.treeview.selection()) == 1)
    

    def getSelectedJobKeys(self):
        items = self.treeview.selection()
        selected_job_keys = list()
        if (self.var_cmb_viewmode.get().lower() == "per mansione"):
            for item in items:
                selected_job_keys.append( self.job_keys_list_treeview[self.treeview.index(item)] )  # using the variable created in populateTable()
        return selected_job_keys


    def getSelectedOperators(self):
        items = self.treeview.selection()
        selected_operators = list()
        if (self.var_cmb_viewmode.get().lower() == "per medico"):
            for item in items:
                # Build the list with the values on the first column
                selected_operators.append(self.treeview.item(item)["values"][0])
        return selected_operators
    

    def doubleClick_treeview(self, event=None):
        if self.is_1_row_selected():
            if (self.var_cmb_viewmode.get().lower() == "per mansione"):
                import mansione
                mansione.Mansione(
                    parent_window=self,
                    selected_key=self.getSelectedJobKeys()[0],
                    action="view",
                    input_file_path=self.__input_file_path )
            elif (self.var_cmb_viewmode.get().lower() == "per medico"):
                operator = self.getSelectedOperators()[0]
                job_list = ""
                for job_key in self.inputHelper.getOperatorJobKeysList(operator=operator, sanitized_operator=True):
                    job_list += ( "\n - " + self.inputHelper.getFullSanitizedJob(job_key) )
                showinfo(
                    title="Dettaglio mansioni",
                    message=f"Elenco mansioni di {operator}:",
                    detail=job_list )
                

    def add_medic_button_pressed(self, event=None):
        """open a quick input form to add a qualified operator on selected jobs"""
        MansionarioQuickEdit(
            parent_window=self,
            selected_values=self.getSelectedJobKeys(),
            action="add_medic",
            input_file_path=self.__input_file_path )

    def rm_medic_button_pressed(self, event=None):
        """open a quick input form to remove a qualified operator on selected jobs"""
        MansionarioQuickEdit(
            parent_window=self,
            selected_values=self.getSelectedJobKeys(),
            action="rm_medic",
            input_file_path=self.__input_file_path )

    def add_job_button_pressed(self, event=None):
        """open a quick input form to add jobs on selected operators"""
        MansionarioQuickEdit(
            parent_window=self,
            selected_values=self.getSelectedOperators(),
            action="add_job",
            input_file_path=self.__input_file_path )

    def rm_job_button_pressed(self, event=None):
        """open a quick input form to remove jobs from selected operators"""
        MansionarioQuickEdit(
            parent_window=self,
            selected_values=self.getSelectedOperators(),
            action="rm_job",
            input_file_path=self.__input_file_path )

    def info_button_pressed(self, event=None):
        showinfo(
            title="Info",
            message="""La tabella supporta la selezione multipla:""",
            detail="- Maiusc (tieni premuto): seleziona intervallo\n- Ctrl (tieni premuto): selezione multipla sparsa" )


class MansionarioQuickEdit(tk.Toplevel):
    __action = str()
    # selected_values keep the selected values (jobs or operators) from the calling window, the ones where to operate edits
    __selected_values = list()
    # operating_list keep the value to put in combobox, that are also the only admitted input values
    __operating_list = list()

    def __init__( self, parent_window: Mansionario, selected_values, action, input_file_path ):
        super().__init__(master=parent_window)

        if (action == "add_job"):
            self.title("Assegna mansione")
        elif (action == "rm_job"):
            self.title("Rimozione mansione")
        elif (action == "add_medic"):
            self.title("Assegna medico")
        elif (action == "rm_medic"):
            self.title("Rimozione medico")
        else:
            self.title("?")

        self.resizable(False, False)

        self.inputHelper = input_helper.InputHelper(input_file_path)

        self.parent_window = parent_window
        self.__action = action
        self.__selected_values = ( selected_values if isinstance(selected_values, list) else list(selected_values) )
        self.__operating_list = self.smartAutocompleteList()

        # building and placing elements
        # label with action and selected elements
        recap = ""
        if (action == "add_job"):
            recap = "Assegna mansione ai medici:\n\n"
        elif (action == "rm_job"):
            recap = "Rimuovi mansione dei medici:\n\n"
        elif (action == "add_medic"):
            recap = "Assegna medico alle mansioni:\n\n"
        elif (action == "rm_medic"):
            recap = "Rimuovi medico dalle mansioni:\n\n"

        if ((action == "add_job") | (action == "rm_job")):
            for operator in self.__selected_values:
                recap += "- " + operator + "\n"
        elif ( (action == "add_medic") | (action == "rm_medic") ):
            for job_key in self.__selected_values:
                recap += ( "- " + self.inputHelper.getFullSanitizedJob(job_key) + "\n" )
        ttk.Label(master=self, text=recap).pack(anchor="nw", padx=10, pady=10, expand=True)

        # the __operating_list, in add/rm_job action, keeps the jobs keys; so we have to sanitize them
        sanitized_list = list()
        if ((action == "add_job") | (action == "rm_job")):
            # calling function on parent_window is dangerous, but this window doesn't exists if parent_window is destroyed
            sanitized_list = self.parent_window.sanitize_job_list(self.__operating_list)
        elif ( (action == "add_medic") | (action == "rm_medic") ):
            # in medic action, __operating_list contains already sanitized operators
            sanitized_list = self.__operating_list

        # SUB-FRAME for input Combobox
        self.frm_input = ttk.Frame(master=self)
        # label on left side of combobox
        lbl_combobox = str()
        if ( (action == "add_job") | (action == "rm_job") ):
            lbl_combobox = "Mansione: "
        elif ( (action == "add_medic") | (action == "rm_medic") ):
            lbl_combobox = "Medico: "
        ttk.Label(master=self.frm_input, text=lbl_combobox).pack(side="left", padx=5)
        # combobox
        self.var_combobox = tk.StringVar()
        self.combobox = AutocompleteCombobox(
            master=self.frm_input,
            textvariable=self.var_combobox,
            width=40,
            completevalues=sanitized_list )
        self.combobox.pack(side="right", expand=True, padx=5)
        self.frm_input.pack(anchor="w", padx=5, pady=10)
        # SUB-FRAME for buttons
        self.frm_buttons = ttk.Frame(master=self)
        ttk.Button(master=self.frm_buttons, text="Salva", command=self.save_button_pressed).pack(side="right", padx=5)
        ttk.Button(master=self.frm_buttons, text="Annulla", command=self.destroy).pack(side="right", padx=5)
        self.frm_buttons.pack(anchor="se", padx=5, pady=10)
        self.bind("<Escape>", lambda event=None: self.destroy())


    def smartAutocompleteList(self):
        ''' 
        build an operators/job_keys list with values that are not already included in all jobs/operators selected 
        returns the job_keys if action="rm/add_job", operators (sanitized) if action="rm/add_medic"
        '''
        # this method use the power of python sets;
        output_list = list()

        if (self.__action == "add_job"):
            # in add job action, the list is made by (all_jobs - jobs_common_in_all_selected_operators)
            all_jobs = set(self.inputHelper.getJobKeyList())
            # building a matrix with every job of a selected operator
            operators_job = list()
            for operator in self.__selected_values:
                operators_job.append( self.inputHelper.getOperatorJobKeysList( operator=operator, sanitized_operator=True ) )
            # now building a set with common jobs
            common_jobs = set(operators_job[0])
            for operator_jobs in operators_job[1:]:
                common_jobs.intersection_update(set(operator_jobs))
            # now the common jobs contains the jobs in common with selected operators; we have to remove them from all_jobs list
            output_list = list(all_jobs.difference(common_jobs))

        elif (self.__action == "rm_job"):
            # in remove job action, the list is made by (all_jobs_of_selected_operators)
            operators_jobs = set()
            for operator in self.__selected_values:
                operator_jobs = self.inputHelper.getOperatorJobKeysList(operator=operator, sanitized_operator=True)
                operators_jobs.update(set(operator_jobs))
            output_list = list(operators_jobs)

        elif (self.__action == "add_medic"):
            # in add medic action, the list is made by (all_operators - operators_common_in_all_selected_jobs)
            all_operators = self.inputHelper.getSanitizedOperatorSet()
            # building a set with common operators
            common_operators = set(self.inputHelper.getSanitizedJobOperatorsList(self.__selected_values[0]))
            for job_key in self.__selected_values[1:]:
                common_operators.intersection_update(set(self.inputHelper.getSanitizedJobOperatorsList(job_key)))
            # now removing the common operators
            output_list = list(all_operators.difference(common_operators))

        elif (self.__action == "rm_medic"):
            # in remove medic action, the list is made by (all_operators_of_selected_jobs)
            all_operators = set()
            # now removing the common operators
            for job_key in self.__selected_values:
                all_operators.update(set(self.inputHelper.getSanitizedJobOperatorsList(job_key)))
            output_list = list(all_operators)

        output_list.sort()
        return output_list
    

    def checkValidInput(self):
        if ((self.__action == "add_job") | (self.__action == "rm_job") | (self.__action == "rm_medic")):
            # the input has to be a job, corresponding to one of the completion list;
            if (self.combobox.current()<0):     # if not found in completions list
                # try cleaning starting and ending spaces
                self.var_combobox.set(value=self.var_combobox.get().strip())
                # recheck
                if (self.combobox.current()<0):     # still not present, require user's correction
                    return False
                
        # elif ((self.__action == "add_medic"):
        #    nothing to check here, three cases:
        #    - new operator: new operators are allowed
        #    - operator from list: ok
        #    - existent operator but not in list: this means to add an operator that's already there, nothing happens

        return True
    

    def getInput_JobKey(self):
        ''' return the job_key, using the self.__operating_list, from the input on combobox (if valid, so check it out before calling this) '''
        if ( (self.__action == "add_job") | (self.__action == "rm_job") ):
            cmb_index = self.combobox.current()     # query the selected index
            if (cmb_index<-1):      # if the value entered is not on the combobox autocompletion list
                self.var_combobox.set(value=self.var_combobox.get().strip())    # try removin eccessive spaces
                cmb_index = self.combobox.current()     #re-query selected index
                if (cmb_index<-1):
                    raise IndexError("Entered Job not valid (not found in list)!")
            return self.__operating_list[cmb_index]
        else:
            raise AttributeError("Cannot return a job_jey from an operator list!")


    def save_button_pressed(self, event=None):
        # TODO improvements: details of what has not been saved;

        if (self.checkValidInput()):
            saved = True
            if (self.__action == "add_job"):
                for operator in self.__selected_values:
                    saved &= self.inputHelper.addJobOperator(job_key=self.getInput_JobKey(), operator=operator, sanitized_operator=True)

            elif (self.__action == "rm_job"):
                for operator in self.__selected_values:
                    saved &= self.inputHelper.deleteJobOperator(job_key=self.getInput_JobKey(), operator=operator, sanitized_operator=True)

            elif (self.__action == "add_medic"):
                for job_key in self.__selected_values:
                    saved &= self.inputHelper.addJobOperator(job_key=job_key, operator=self.var_combobox.get(), sanitized_operator=True)
                
            elif (self.__action == "rm_medic"):
                for job_key in self.__selected_values:
                    saved &= self.inputHelper.deleteJobOperator(job_key=job_key, operator=self.var_combobox.get(), sanitized_operator=True)

            if saved:
                self.parent_window.refreshTable()
                self.destroy()
                showinfo(title="Modifiche salvate", message="Modifiche salvate correttamente!")
            else:
                showerror(title="Errore salvataggio", message="Si sono verificati problemi durante il salvataggio delle modifiche!")
        else:
            if ((self.__action == "add_job") | (self.__action == "rm_job")):
                showerror(
                    title="Errore input", 
                    message="Attenzione, la mansione inserita non è stata trovata.", 
                    detail="Per un input corretto si suggerisce di utilizzare il menu a tendina" )
            elif (self.__action == "rm_medic"):
                showerror(
                    title="Errore input", 
                    message="Attenzione, il medico inserito non risulta in nessuna delle mansioni selezionate.", 
                    detail="Per un input corretto si suggerisce di utilizzare il menu a tendina" )
