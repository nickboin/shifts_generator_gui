import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import askokcancel, WARNING, showwarning, showerror
import ttkwidgets.autocomplete as autocomplete
import input_helper
from input_helper import DAY_OFFSET

class Mansione(tk.Toplevel):

    __unsaved_changes = False

    __action = "view"   # default action on errors
    __selected_key = str()
    __input_file_path = str()

    # action: ["view" or "edit" or "add"], selected_key: the key from the json to show/edit
    def __init__(self, parent_window:tk.Widget, selected_key, action, input_file_path, is_generate_running:bool=False):
        super().__init__(master=parent_window.master)
        self.parent_window = parent_window
        self.withdraw() # stay hidden until window has been centered
        
        self.__action = action
        self.__selected_key = selected_key

        if (self.__action == "add"):
            __title = "Aggiungi mansione"
        elif (self.__action == "edit"):
            __title = "Modifica mansione"
        elif (self.__action == "view"):
            __title = "Dettagli mansione"
        else:
            __title = "Errore"
        
        self.title(__title)

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        if self.__action == "view":
            self.bind("<Escape>", self.on_window_close)

        self.__input_file_path = input_file_path
        self.__input_helper = input_helper.InputHelper(self.__input_file_path)

        # ---- MAIN FRAMES DEFINITIONS ----
        # FRAME for the input/edit elements
        self.frm_records = ttk.Frame( master=self, padding=10)
        self.frm_records.grid(row=0, sticky="nesw")
        # FRAME for the action buttons, hidden in "view" action
        self.frm_buttons = ttk.Frame( master=self, padding=10)
        self.frm_buttons.grid(row=1, sticky="ew")

        sanitized_job_names = self.__input_helper.getSanitizedJobNameList()
        sanitized_job_locations = self.__input_helper.getSanitizedJobLocationList()

        # --- FRAME for the current record selection ---
        if (self.__action == "view") | (self.__action == "edit") :
            human_readable_key = self.__input_helper.getSanitizedJobLocation(self.__selected_key) + ": " + self.__input_helper.getSanitizedJobName(self.__selected_key)
            self.var_job_key = tk.StringVar(value=human_readable_key)
            human_readable_keys = tuple()
            for i in range(0, len(sanitized_job_names)):
                human_readable_keys += (( sanitized_job_locations[i] + ": " + sanitized_job_names[i] ), )
            self.cmb_job_key = ttk.Combobox( master=self.frm_records, 
                                            textvariable=self.var_job_key, 
                                            values=human_readable_keys, 
                                            state="readonly" )
            self.cmb_job_key.bind("<<ComboboxSelected>>", self.currentKey_change)

        # --- FRAME for the record fields ---
        # NAME entry
        self.var_job_name = tk.StringVar()
        # entry with autocompletions from already present values
        # TODO remove ": Principale"/": Secondario" part from autocompletion
        self.etr_job_name = autocomplete.AutocompleteEntry( master=self.frm_records, 
                                                           textvariable=self.var_job_name, 
                                                           completevalues=sanitized_job_names )
        # in view action set not editable
        if self.__action == "view":
            self.etr_job_name.configure( state="readonly" )

        # LOCATION entry
        self.var_job_location = tk.StringVar()
        # in view action, use a not editable entry, in add/edit use a combobox
        if self.__action == "view":
            self.cmb_job_location = ttk.Entry(master=self.frm_records, textvariable=self.var_job_location, state="readonly" )
        else:
            self.cmb_job_location = autocomplete.AutocompleteCombobox( master=self.frm_records, 
                                        textvariable=self.var_job_location, 
                                        completevalues=list(set(sanitized_job_locations)) )

        # SUB-FRAME for category entry and multi-operator check-box
        self.frm_category_multioperator = ttk.Frame(master=self.frm_records)

        # CATEGORY entry
        self.var_job_category = tk.StringVar()
        # entry with autocompletions from already present values
        self.etr_job_category = autocomplete.AutocompleteEntry( master=self.frm_category_multioperator, 
                                                           textvariable=self.var_job_category, 
                                                           completevalues=self.__input_helper.getSanitizedJobCategoriesList())
        # in view action set not editable
        if self.__action == "view":
            self.etr_job_category.configure( state="readonly" )

        # MULTIPLE OPERATOR entry
        self.var_job_muliple_operator = tk.IntVar()
        self.chk_job_multiple_operator = ttk.Checkbutton(master=self.frm_category_multioperator, 
                                                         variable=self.var_job_muliple_operator,
                                                         text="Multi-operatore",
                                                         command=self.chkbtn_moTask_changed )
        # in view and edit (for the moment) action set not editable
        if ( self.__action == "view" ) | ( self.__action == "edit" ):
            self.chk_job_multiple_operator.configure( state="disabled" )
        
        # placing category and multiple-operator on the SUB-FRAME
        self.etr_job_category.pack(side="left", expand=True, fill=tk.X)
        self.chk_job_multiple_operator.pack(side="right")

        '''
        the following fields are declared by default for a single operator task input.
        When the multiple operator task chechbutton get pressed, the following fields will get disabled
        and the input follow a new window for the two jobs created input.
        '''

        # DAYS entry
        if self.__action == "view":
            self.var_job_days = tk.IntVar()
            self.etr_job_days = ttk.Entry( master=self.frm_records, 
                                          textvariable=self.var_job_days, 
                                           state="readonly" )
        else:
            # SUB-FRAME to contain checkboxes
            self.frm_job_days = ttk.Frame( master=self.frm_records )
            # initialize a StringVar for each day
            #self.var_job_days = (tk.StringVar(value=0), )*7   # NO, this replicate the same pointer :/
            self.var_job_days = tuple()
            for i in range(0,7):
                self.var_job_days += (tk.StringVar(value = 0), )
            # make a tuple of checkboxes
            self.chk_job_days = tuple()
            day_labels = ["L", "M", "M", "G", "V", "S", "D"]
            for i in range(0,7):
                self.chk_job_days += ( ttk.Checkbutton( master=self.frm_job_days, text=day_labels[i], variable=self.var_job_days[i] ) ,)
                self.chk_job_days[i].grid(row=0, column=i, sticky="w")

        # TIME entry
        if self.__action == "view":
            self.var_job_hours = tk.StringVar()
            self.etr_job_hours = ttk.Entry( master=self.frm_records, 
                                            textvariable=self.var_job_hours, 
                                            state="readonly" )
        else:
            self.var_job_time = ( tk.StringVar() , tk.StringVar() )
            # Sub-frame to contain spinboxes
            self.frm_job_time = ttk.Frame( master=self.frm_records )
            self.spn_job_time = tuple() # tuple for the spinbox objects
            self.validation_command = ( self.register(self.validate_spinbox_int), "%P" )
            for i in range(0,2):
                self.spn_job_time += ( ttk.Spinbox( master=self.frm_job_time, width=2 ,
                                                    from_=0, to=23, wrap=False, format="%02.0f",
                                                    textvariable=self.var_job_time[i],
                                                    validate="key", validatecommand=self.validation_command ) ,)
            # placing elements
            ttk.Label(master=self.frm_job_time, text="dalle ").grid(row=0, column=0, sticky="w")
            self.spn_job_time[0].grid(                              row=0, column=1, sticky="w")
            ttk.Label( master=self.frm_job_time, text=":").grid(    row=0, column=2, sticky="w")
            # minute spinbox completely not functional
            self.dummy_min_var = tk.StringVar(value="00")
            ttk.Spinbox( master=self.frm_job_time, width=2, 
                        textvariable=self.dummy_min_var, 
                        format="%02.0f", state="readonly").grid(    row=0, column=3, sticky="w")
            ttk.Label( master=self.frm_job_time, text="alle ").grid(row=0, column=4, sticky="w")
            self.spn_job_time[1].grid(                              row=0, column=5, sticky="w")
            ttk.Label( master=self.frm_job_time, text=":").grid(    row=0, column=6, sticky="w")
            # minute spinbox completely not functional
            ttk.Spinbox( master=self.frm_job_time, width=2, 
                        textvariable=self.dummy_min_var, 
                        format="%02.0f", state="readonly" ).grid(   row=0, column=7, sticky="w")

                    
        # OPERATORS entry
        self.var_job_new_operator = tk.StringVar()
        # Sub-frame to contain the add entry + button, hidden on view mode
        self.frm_job_operators = ttk.Frame( master=self.frm_records )
        if not self.__action == "view":
            self.btn_job_add_operator = ttk.Button( master=self.frm_job_operators, 
                                                    text="+", width=2, 
                                                    command=self.btn_job_add_operator_pressed )
            self.etr_job_new_operator = autocomplete.AutocompleteEntry( master=self.frm_job_operators, 
                                                                        textvariable=self.var_job_new_operator, 
                                                                        completevalues=list(self.__input_helper.getSanitizedOperatorSet()) )
            self.etr_job_new_operator.bind('<Return>', self.btn_job_add_operator_pressed)
            self.etr_job_new_operator.bind('<KP_Enter>', self.btn_job_add_operator_pressed)
            self.btn_job_rm_operator = ttk.Button(  master=self.frm_job_operators, 
                                                    text="-", width=2, 
                                                    command=self.btn_job_rm_operator_pressed )
            self.etr_job_new_operator.grid(row=0, column=0, columnspan=2, sticky="we")
            self.btn_job_add_operator.grid(row=0, column=2, padx=2)
            self.btn_job_rm_operator.grid(row=1, column=2, padx=2, sticky="nw")
        
        self.var_job_list_operators = tk.Variable()
        self.lst_job_operators = tk.Listbox( master=self.frm_job_operators, 
                                            height=5,
                                            listvariable=self.var_job_list_operators )
        self.lst_job_operators.grid( row=int(not self.__action == "view") , column=0, sticky="nwse")
        if self.__action == "view":
            self.lst_job_operators.configure( selectmode=tk.SINGLE )
        else:
            self.lst_job_operators.configure( selectmode=tk.EXTENDED )
            self.lst_job_operators.bind("<Delete>", self.btn_job_rm_operator_pressed)
        # listbox scrollbar
        self.scr_list_operators_scrollbar = ttk.Scrollbar(self.frm_job_operators, orient=tk.VERTICAL, command=self.lst_job_operators.yview)
        self.lst_job_operators.configure( yscrollcommand=self.scr_list_operators_scrollbar.set)
        self.scr_list_operators_scrollbar.grid(row=(not self.__action == "view"), column=1, sticky="ns")


        # NOW set the current selected key values
        self.setCurrentKeyValues()


        # BUILGING the frm_records GRID

        # Record selector row:
        frm_operators_row_offset = 0
        if ( (self.__action == "view") | (self.__action == "edit") ):
            # show the record selection entry, so the following rows have +1 offsed
            ttk.Label(master=self.frm_records, text="Mansione selezionata: ").grid(row=0, column=0, sticky="ne")
            self.cmb_job_key.grid(row=0, column=1, sticky="nwe")
            # set a row minsize to distance the record input section
            self.frm_records.rowconfigure(index=0, minsize=50)
            frm_operators_row_offset = 1

        # COLUMN of LABELS:
        labels = ["Mansione: ", "Sede: ", "Categoria: ", "Giorni di operatività: ", 
                    "Orario operatività: ", "Medici qualificati: "]
        for i in range(len(labels)):
            ttk.Label(master=self.frm_records, text=labels[i]).grid(row=( frm_operators_row_offset + i ), column=0, sticky="ne", pady=2)
        # add preference button under "Medici qualificati" label
        if (self.__action == "edit"):
            self.btn_job_operator_preference = ttk.Button(master=self.frm_records, text="Preferenze", command=self.btn_job_operator_preference_pressed)
            self.btn_job_operator_preference.grid(row=int(frm_operators_row_offset + len(labels)), column=0, sticky="ne", padx=5, pady=5)

        # COLUMN of entries, checkboxes, comboboxes and so on:
        self.etr_job_name.grid(row=( frm_operators_row_offset + 0 ), column=1, sticky="nwe", pady=2)
        self.cmb_job_location.grid(row=( frm_operators_row_offset + 1 ), column=1, sticky="nwe", pady=2)
        self.frm_category_multioperator.grid(row=( frm_operators_row_offset + 2 ), column=1, sticky="nwe", pady=2)
        if self.__action == "view":
            self.etr_job_days.grid(row=( frm_operators_row_offset + 3 ), column=1, sticky="nwe", pady=2)
            self.etr_job_hours.grid(row=( frm_operators_row_offset + 4 ), column=1, sticky="nwe", pady=2)
        else:
            self.frm_job_days.grid(row=( frm_operators_row_offset + 3 ), column=1, sticky="nw", pady=2)
            self.frm_job_time.grid(row=( frm_operators_row_offset + 4 ), column=1, sticky="nw", pady=2)
        self.frm_job_operators.grid(row=( frm_operators_row_offset + 5 ), rowspan=2, column=1, sticky="nwse", pady=2)
        
        # re-sizability comlpliant
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.frm_job_operators.columnconfigure(0, weight=1)
        self.frm_job_operators.rowconfigure(int(not self.__action == "view"), weight=1)
        self.frm_records.columnconfigure(1, weight=1)
        self.frm_records.rowconfigure((frm_operators_row_offset + 5), weight=1)
        self.frm_records.rowconfigure((frm_operators_row_offset + 6), weight=1)

        # --- FRAME for the buttons ---

        # if not self.frm_buttons.winfo_ismapped(): # this works, but I don't rely on this anymore
        if ( (self.__action == "add") | (self.__action == "edit") ):
            self.btn_submit = ttk.Button(master=self.frm_buttons, text="Salva", command=self.submit_button_pressed)
            self.btn_submit.pack(side="right", padx=2)
            self.btn_cancel = ttk.Button(master=self.frm_buttons, text="Annulla", command=self.cancel_button_pressed)
            self.btn_cancel.pack(side="right", padx=2)
        elif (self.__action == "view"):
            self.btn_edit = ttk.Button(master=self.frm_buttons, text="Modifica", command=self.edit_button_pressed)
            self.btn_edit.pack(side="right")
            if is_generate_running:
                self.btn_edit.configure(state="disabled")
        # in edit and view action add the compatibility button
        if ((self.__action == "edit") | (self.__action == "view")):
            self.btn_compatibility = ttk.Button(master=self.frm_buttons, text="Compatibilità", command=self.compatibility_button_pressed)
            self.btn_compatibility.pack(side="left", padx=2)
        # in edit action add the delete button
        if (self.__action == "edit"):
            self.btn_delete = ttk.Button(master=self.frm_buttons, text="Elimina", command=self.delete_button_pressed)
            self.btn_delete.pack(side="left", padx=2)
        
        # after placing all elements, set the created wundow size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())

        from gui import center_window
        center_window(self)
        self.deiconify()
        


    def validate_spinbox_int(self, u_input):
        if u_input == "":
            return True
        elif u_input.isdigit():
            return ( int(u_input) in range(0,24) )
        else:
            return False

    def on_window_close(self, event=None):
        changed_list = self.checkForChanges()

        popup_message = ""
        for changed in changed_list:
            popup_message += ("- {}\n".format(changed))
        popup_message += "\nChiudere lo stesso?"

        if ( not self.__action == "view" ) & self.__unsaved_changes:
            # popup
            if (askokcancel(parent=self, title="Modifiche non salvate", icon=WARNING, message="Attenzione, modifiche non salvate in:", detail=popup_message)):
                self.destroy()
        else:
            self.destroy()

    # get the array created from the selected days checkboxes
    def getSelectedDays(self):
        days_list = set()
        for i in range(0,7):
            if int(self.var_job_days[i].get()) != 0:
                days_list.add( (DAY_OFFSET + i) )
        return days_list

    # get the array from the input time spinboxes
    def getInputTime(self):
        return ( int(self.var_job_time[0].get()), int(self.var_job_time[1].get()) )
    
    # in edit/view mode, load the current selected key values on the widgets (on frm_records)
    def setCurrentKeyValues(self):
        if ( self.__input_helper.existsJobKey(self.__selected_key) ) & ( ( self.__action == "view" ) | ( self.__action == "edit" ) ):
            if (self.__action == "view"):
                self.var_job_name.set( value=self.__input_helper.getFullSanitizedJobName(self.__selected_key) )
            else:
                self.var_job_name.set( value=self.__input_helper.getSanitizedJobName(self.__selected_key) )
            self.var_job_location.set( value=self.__input_helper.getSanitizedJobLocation(self.__selected_key) )
            self.var_job_category.set( value=self.__input_helper.getSanitizedJobCategory(self.__selected_key) )
            multiple_operator_state = 0
            if self.__input_helper.isMultipleOperatorTask(self.__selected_key):
                multiple_operator_state = 1
            elif self.__input_helper.hasMultipleOperatorTask(self.__selected_key):
                multiple_operator_state = 2 # a value !=0 and !=1 should set the tri-state on checkbox
            self.var_job_muliple_operator.set( value=multiple_operator_state )
            # days and time input are a single entry in "view" action
            # but days is a checkbox list and time is a spinbox list in "edit" action
            if self.__action == "view":
                self.var_job_days.set( value=self.__input_helper.getSanitizedJobDays(self.__selected_key) )
                self.var_job_hours.set( value=self.__input_helper.getSanitizedJobTime(self.__selected_key) )
            else:
                # preload existing values on checkbox (set "1" for checkbox where needed)
                current_job_days = self.__input_helper.getJobDays(self.__selected_key)
                for i in range(len(self.var_job_days)):
                    if ( i + DAY_OFFSET ) in current_job_days:
                        self.var_job_days[i].set(value=1)
                    else:
                        self.var_job_days[i].set(value=0)
                # preload existing values on spinboxes
                time_tuple = tuple(self.__input_helper.getJobTime(self.__selected_key))  # tuple format: (start_time, end_time)
                for i in range(2):
                    self.var_job_time[i].set( value=time_tuple[i] )
            self.var_job_list_operators.set( value=self.__input_helper.getSanitizedJobOperatorsList(self.__selected_key) )


    def checkForChanges(self):
        self.__unsaved_changes = False
        changed_list = list()
        if self.__action == "edit":
            if (self.var_job_name.get() != self.__input_helper.getSanitizedJobName(self.__selected_key)):
                self.__unsaved_changes = True
                changed_list.append("Nome mansione")
            if (self.var_job_location.get() != self.__input_helper.getSanitizedJobLocation(self.__selected_key)):
                self.__unsaved_changes = True
                changed_list.append("Sede")
            if (self.var_job_category.get() != self.__input_helper.getSanitizedJobCategory(self.__selected_key)):
                self.__unsaved_changes = True
                changed_list.append("Categoria")
            if set(self.getSelectedDays()) != set(self.__input_helper.getJobDays(self.__selected_key)):
                self.__unsaved_changes = True
                changed_list.append("Giorni")
            spn_time_tuple = self.getInputTime()
            if spn_time_tuple != tuple(self.__input_helper.getJobTime(self.__selected_key)):
                self.__unsaved_changes = True
                changed_list.append("Orario")
            if set(self.__input_helper.getSanitizedJobOperatorsList(self.__selected_key)) != set(self.var_job_list_operators.get()):
                self.__unsaved_changes = True
                changed_list.append("Medici qualificati")
        elif self.__action == "add":
            if (self.var_job_name.get() != ""):
                self.__unsaved_changes = True
                changed_list.append("Nome mansione")
            if (self.var_job_location.get() != ""):
                self.__unsaved_changes = True
                changed_list.append("Sede")
            if (self.var_job_category.get() != ""):
                self.__unsaved_changes = True
                changed_list.append("Categoria")
            if len(self.getSelectedDays()) != 0:
                self.__unsaved_changes = True
                changed_list.append("Giorni")
            spn_time_tuple = (self.var_job_time[0].get(), self.var_job_time[1].get())
            if spn_time_tuple != ("", ""):
                self.__unsaved_changes = True
                changed_list.append("Orario")
            if len(self.var_job_list_operators.get()) != 0:
                self.__unsaved_changes = True
                changed_list.append("Medici qualificati")
        return changed_list
    
    def update_changed_fields(self):
        updated_job_name = None
        updated_job_location = None
        updated_job_category = None
        updated_job_days = None
        updated_job_time = None
        updated_job_operators = None
        changed_list = self.checkForChanges()
        if "Nome mansione" in changed_list:
            updated_job_name = self.var_job_name.get()
        if "Sede" in changed_list:
            updated_job_location = self.var_job_location.get()
        if "Categoria" in changed_list:
            updated_job_category = self.var_job_category.get()
        if "Giorni" in changed_list:
            updated_job_days = list(self.getSelectedDays())
            updated_job_days.sort()
        if "Orario" in changed_list:
            updated_job_time = self.getInputTime()
        if "Medici qualificati" in changed_list:
            updated_job_operators = list(self.var_job_list_operators.get())
        new_key =  self.__input_helper.updateJob( job_key = self.__selected_key, 
                                                    new_name = updated_job_name, 
                                                    new_location = updated_job_location, 
                                                    new_category = updated_job_category, 
                                                    new_days = updated_job_days, 
                                                    new_time = updated_job_time, 
                                                    new_operators = updated_job_operators )
        return self.__input_helper.existsJobKey(new_key)
            
    def checkInvalidInput(self):
        '''
            check all required fields and format
            returns a list of human readable name of invalid fields
        '''
        # HINT Per migliorarla in futuro si può pensare alla validazione in 'focusout' dei singoli campi, con cambio colore se il campo non è valido
        invalid_fields = list()
        if (self.var_job_name.get() == ""):
            invalid_fields.append("Nome")
        if (self.var_job_location.get() == ""):
            invalid_fields.append("Sede")
        if (self.var_job_category.get() == ""):
            invalid_fields.append("Categoria")
        if len(self.getSelectedDays()) == 0:
            invalid_fields.append("Giorni")
        job_time = ( self.var_job_time[0].get(), self.var_job_time[1].get() )
        if ((job_time[0] == "") | (job_time[1] == "")):
            invalid_fields.append("Orario")
        elif ((not job_time[0].isdigit()) | (not job_time[1].isdigit())):
            invalid_fields.append("Orario")
        elif ((int(job_time[0]))<0 | (int(job_time[0]))>23 | (int(job_time[1]))<0 | (int(job_time[1]))>23):
            invalid_fields.append("Orario")
        return invalid_fields
            
    def getCurrentInputDict(self):
        current_input_dict = dict()
        if (len(self.var_job_name.get())!=0):
            current_input_dict.update({"job_name":self.var_job_name.get()})
        if (len(self.var_job_location.get())!=0):
            current_input_dict.update({"job_location":self.var_job_location.get()})
        if (len(self.var_job_category.get())!=0):
            current_input_dict.update({"job_category":self.var_job_category.get()})
        selected_days = list(self.getSelectedDays())
        if (len(selected_days)!=0):
            current_input_dict.update({"job_days":selected_days})
        job_time = ( self.var_job_time[0].get(), self.var_job_time[1].get() )
        if ((len(job_time[0])+len(job_time[1]))!=0):
            current_input_dict.update({"job_time":job_time})
        if (len(self.var_job_list_operators.get())!=0):
            current_input_dict.update({"job_operators":self.var_job_list_operators.get()})
        return current_input_dict

    def currentKey_change(self, event=None):
        previous_key = self.__selected_key
        
        self.checkForChanges()

        selected_index = self.cmb_job_key.current()
        self.__selected_key = self.__input_helper.getJobKey_byIndex(selected_index)

        if ( self.__action == "edit" ) & self.__unsaved_changes:
            # popup
            if (askokcancel(parent=self, title='Modifiche non salvate', icon=WARNING, 
                    message='Attenzione, le modifiche effettuate non sono state salvate. Cambiare mansione?')):
                self.setCurrentKeyValues()
            else:
                self.cmb_job_key.current( newindex=self.__input_helper.getJobKeyIndex_byKey(previous_key) )
                self.__selected_key = previous_key
        else:
            self.setCurrentKeyValues()
            
    def chkbtn_moTask_changed(self, event=None):
        if(self.__action == "add"):     # the chkbtn is editable only in add action, but to be sure...
            if (self.var_job_muliple_operator.get() == 0):
                # MULTIPLE OPERATORS OFF
                self.btn_submit.configure(text="Salva")
                # enabling days input
                for chkbtn_day in self.chk_job_days:
                    chkbtn_day.configure(state="normal")
                # enabling time input
                for spn_time in self.spn_job_time:
                    spn_time.configure(state="normal")
                # enabling operators input
                self.etr_job_new_operator.configure(state="normal")
                self.btn_job_add_operator.configure(state="normal")
                self.btn_job_rm_operator.configure(state="normal")
                self.lst_job_operators.configure(selectmode=tk.MULTIPLE)
            else:
                # MULTIPLE OPERATORS ON
                self.btn_submit.configure(text="Avanti")
                # disabling days input
                for chkbtn_day in self.chk_job_days:
                    chkbtn_day.configure(state="disabled")
                # disabling time input
                for spn_time in self.spn_job_time:
                    spn_time.configure(state="disabled")
                # enabling operators input
                self.etr_job_new_operator.configure(state="disabled")
                self.btn_job_add_operator.configure(state="disabled")
                self.btn_job_rm_operator.configure(state="disabled")
                self.lst_job_operators.configure(selectmode=tk.SINGLE)
                self.lst_job_operators.select_clear(0,"end")


    def submit_button_pressed(self, event=None):
        if (self.var_job_muliple_operator.get() == 0):
            invalid_fields = self.checkInvalidInput()
            # formatting string for the popup
            invalids = ""
            if (len(invalid_fields) != 0):
                for i in range(len(invalid_fields)-1):
                    invalids += ("- " + invalid_fields[i] + "\n")
                showwarning( title="Input non corretto", message="Attenzione, i seguenti campi sono mancanti o non rispettano il formato richiesto:", detail=invalids)
            else:
                saved = False
                if self.__action == "add":
                    saved = self.__input_helper.addNewJob(job_name = self.var_job_name.get(), 
                                    job_location = self.var_job_location.get(), 
                                    job_category = self.var_job_category.get(), 
                                    job_days = list(self.getSelectedDays()), 
                                    job_time = self.getInputTime(), 
                                    job_operators = list(self.var_job_list_operators.get()), 
                                    multiple_operator_task=False,
                                    sanitized_input=True )
                elif self.__action == "edit":
                    saved = self.update_changed_fields()
                # now close the window if done correctly
                if saved:
                    try:
                        if self.parent_window.winfo_exists():
                            if self.parent_window.state() == "normal":
                                self.parent_window.refreshTable()
                    except tk.TclError:
                        # the exception get thrown when the parent_window has been already closed
                        pass
                    finally:
                        self.destroy()
                else:
                    showerror(title="Errore aggiunta mansione",
                            message="C'è stato un errore nell'aggiunta/salvataggio della mansione!")
        else:
            # open a new window for the 2 jobs input
            preload=self.getCurrentInputDict()
            import mansione_multipla
            mansione_multipla.MultipleOperatorInput(parent_window=self.master, 
                                                    mansioni_refresh_command=self.parent_window.refreshTable, 
                                                    preload_input=preload, 
                                                    inputHelper=self.__input_helper)
            # close the current window
            self.destroy()

    def cancel_button_pressed(self, event=None):
        self.on_window_close()

    
    def delete_button_pressed(self, event=None):
        if (askokcancel(parent=self, title="Conferma eliminazione",
            message=f"Si vuole veramente eliminare la mansione {self.var_job_key.get()}?")):
            if self.__input_helper.deleteJob(self.__selected_key):
                try:
                    if self.parent_window.winfo_exists():
                        if self.parent_window.state() == "normal":
                            self.parent_window.refreshTable()
                except tk.TclError:
                    # the exception get thrown when the parent_window has been already closed
                    pass
                except KeyError:
                    showerror(title="Non eliminato", message=f"Errore: elemento {self.__selected_key} non trovato.")
                finally:
                    self.destroy()
            else:
                showerror(title="Non eliminato", message="Errore: elemento non eliminato.")
        else:
            pass

    # button visible only on view action
    def edit_button_pressed(self, event=None):
        self.wm_withdraw()
        Mansione(
            parent_window=self.master, 
            selected_key=self.__selected_key, 
            action="edit", 
            input_file_path=self.__input_file_path)
        self.destroy()

    def compatibility_button_pressed(self, event=None):
        self.wm_withdraw()
        import compatibility
        compatibility.Compatibility(
            parent_window=self.master, 
            selected_job_key=self.__selected_key, 
            inputHelper=self.__input_helper)
        self.destroy()

    # button visible only on edit action
    def btn_job_operator_preference_pressed(self, event=None):
        import preferenze
        preferenze.Preferenze( 
            parent_window=self, 
            input_file_path=self.__input_file_path, 
            selected_job_key=self.__selected_key )

    def btn_job_add_operator_pressed(self, event=None):
        new_value = self.__input_helper.sanitize_operator(self.var_job_new_operator.get())
        if (new_value != ""):
            operator_list = tuple(self.var_job_list_operators.get())
            # check if already present
            if not operator_list.count(new_value):
                operator_list = (new_value, ) + operator_list
                self.var_job_list_operators.set(operator_list)
                # clear entry after adding
                self.var_job_new_operator.set(value="")
    
    def btn_job_rm_operator_pressed(self, event=None):
        operator_list = tuple(self.var_job_list_operators.get())
        selected_indexes = tuple(self.lst_job_operators.curselection())
        new_operator_list = tuple()
        # create new list without the selected items
        for i in range(0, len(operator_list)):
            if not i in selected_indexes:               # if i is not present in selected_indexes
                new_operator_list += (operator_list[i], )   # then add the element in the new list
        self.var_job_list_operators.set(new_operator_list)
        self.lst_job_operators.select_clear(0,"end")
