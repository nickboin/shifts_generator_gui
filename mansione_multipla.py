import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import askokcancel, WARNING, showwarning, showerror
from ttkwidgets import autocomplete
import input_helper
from input_helper import DAY_OFFSET
#from idlelib.tooltip import Hovertip

class MultipleOperatorInput(tk.Toplevel):

    def __init__(self, parent_window:tk.Widget, mansioni_refresh_command, preload_input, inputHelper:input_helper.InputHelper):
        super().__init__(master=parent_window.master)
        self.withdraw() # stay hidden until window has been centered
        
        self.refresh_mansioni_table = mansioni_refresh_command
        self.__input_helper = inputHelper

        self.title("Inserimento mansione multi-operatore")

        # ---- MAIN FRAMES DEFINITIONS ----
        # FRAME for the input/edit elements
        self.frm_common_job= ttk.Frame( master=self, padding=10)
        # FRAME for the MAIN job input
        self.frm_main_job = ttk.LabelFrame( master=self, padding=10, text="Mansione principale")
        # FRAME for the MULTIOPERATOR job input
        self.frm_multi_job = ttk.LabelFrame( master=self, padding=10, text="Mansione multi-operatore")
        # FRAME for the action buttons, hidden in "view" action
        self.frm_buttons = ttk.Frame( master=self, padding=10)


        # --- FRAME for the common fields, given by the previous window ---
        # NAME entry
        ttk.Label(master=self.frm_common_job, text="Mansione: ").grid(row=0, column=0, pady=2, sticky="e")
        self.var_job_name = tk.StringVar()
        # entry with autocompletions from already present values
        self.etr_job_name = autocomplete.AutocompleteEntry( master=self.frm_common_job, 
                                                           textvariable=self.var_job_name, 
                                                           completevalues=self.__input_helper.getFullSanitizedJobNameList() )
        self.var_job_name.trace_add("write", self.var_job_name_updated)
        self.etr_job_name.grid(row=0, column=1, pady=2, sticky="ew")
        # LOCATION entry
        ttk.Label(master=self.frm_common_job, text="Sede: ").grid(row=1, column=0, pady=2, sticky="e")
        self.var_job_location = tk.StringVar()
        # in view action, use a not editable entry, in add/edit use a combobox
        self.cmb_job_location = autocomplete.AutocompleteCombobox( master=self.frm_common_job, 
                                        textvariable=self.var_job_location, 
                                        completevalues=list(set(self.__input_helper.getSanitizedJobLocationList())) )
        self.cmb_job_location.grid(row=1, column=1, pady=2, sticky="ew")
        # CATEGORY entry
        ttk.Label(master=self.frm_common_job, text="Categoria: ").grid(row=2, column=0, pady=2, sticky="e")
        self.var_job_category = tk.StringVar()
        # entry with autocompletions from already present values
        self.etr_job_category = autocomplete.AutocompleteEntry( master=self.frm_common_job, 
                                                           textvariable=self.var_job_category, 
                                                           completevalues=self.__input_helper.getSanitizedJobCategoriesList())
        self.etr_job_category.grid(row=2, column=1, pady=2, sticky="ew")
        
        # variable used for the cycle
        parent_frm = [ self.frm_main_job, self.frm_multi_job ]
        day_labels = ["L", "M", "M", "G", "V", "S", "D"]
        
        # arrayed elements, predecleared:
        self.frm_job_days = ( ttk.Frame( master=parent_frm[0] ) , ttk.Frame( master=parent_frm[1] ) )   # SUB-FRAME to contain checkboxes
        self.frm_job_time = ( ttk.Frame( master=parent_frm[0] ) , ttk.Frame( master=parent_frm[1] ) )   # SUB-FRAME to contain spinboxes
        self.frm_input_operator = ( ttk.Frame( master=parent_frm[0] ) , ttk.Frame( master=parent_frm[1] ) )   # Sub-frame to contain the add entry + button
        self.var_job_days = [ list(), list() ]
        self.chk_job_days = [ list(), list() ]
        self.var_job_time = [ ( tk.StringVar() , tk.StringVar() ), ( tk.StringVar() , tk.StringVar() ) ]
        self.spn_job_time = [ list(), list() ]
        self.var_job_new_operator = (tk.StringVar(), tk.StringVar())
        self.var_job_list_operators = (tk.Variable(), tk.Variable())
        self.btn_job_add_operator = tuple()
        self.btn_job_add_operator_command = ( lambda event=None:self.btn_job_add_operator_pressed(which_frame=0),
                                              lambda event=None:self.btn_job_add_operator_pressed(which_frame=1) )
        #self.btn_job_add_operator_command = ( self.btn_mainJob_add_operator_pressed, self.btn_otherJob_add_operator_pressed )
        self.etr_job_new_operator = tuple()
        self.btn_job_rm_operator = tuple()
        self.btn_job_rm_operator_command = ( lambda event=None:self.btn_job_rm_operator_pressed(which_frame=0),
                                             lambda event=None:self.btn_job_rm_operator_pressed(which_frame=1) )
        self.lst_job_operators = tuple()
        self.scr_list_operators_scrollbar = tuple()

        for i in range(2):
            # DAYS input
            for j in range(0,7):
                val = 0
                if "job_days" in preload_input:     # preload eventual given values
                    val = int( ((j+1) in preload_input["job_days"]) )
                self.var_job_days[i].append( tk.IntVar(value=val) )
            #self.chk_job_days.append( list() )
            for j in range(0,7):
                self.chk_job_days[i].append( ttk.Checkbutton( master=self.frm_job_days[i], text=day_labels[j], variable=self.var_job_days[i][j] ) )
                self.chk_job_days[i][j].grid(row=0, column=j, sticky="w")

            # TIME input
            self.validation_command = ( self.register(self.validate_spinbox_int), "%P" )
            for j in range(0,2):
                self.spn_job_time[i].append( ttk.Spinbox( master=self.frm_job_time[i], width=2 ,
                                                    from_=0, to=23, wrap=False, format="%02.0f",
                                                    textvariable=self.var_job_time[i][j],
                                                    validate="key", validatecommand=self.validation_command ) )
            # placing elements in subframe
            ttk.Label(master=self.frm_job_time[i], text="dalle ").grid( row=0, column=0, sticky="w")
            self.spn_job_time[i][0].grid(                               row=0, column=1, sticky="w")
            ttk.Label( master=self.frm_job_time[i], text=":").grid(     row=0, column=2, sticky="w")
            # minute spinbox completely not functional
            self.dummy_min_var = tk.StringVar(value="00")
            ttk.Spinbox( master=self.frm_job_time[i], width=2, 
                        textvariable=self.dummy_min_var, 
                        format="%02.0f", state="readonly").grid(        row=0, column=3, sticky="w")
            ttk.Label( master=self.frm_job_time[i], text="alle ").grid( row=0, column=4, sticky="w")
            self.spn_job_time[i][1].grid(                               row=0, column=5, sticky="w")
            ttk.Label( master=self.frm_job_time[i], text=":").grid(     row=0, column=6, sticky="w")
            # minute spinbox completely not functional
            ttk.Spinbox( master=self.frm_job_time[i], width=2, 
                        textvariable=self.dummy_min_var, 
                        format="%02.0f", state="readonly" ).grid(       row=0, column=7, sticky="w")   
                     
            # OPERATORS input
            self.btn_job_add_operator += ( ttk.Button( master=self.frm_input_operator[i], 
                                                    text="+", width=2, command=self.btn_job_add_operator_command[i]) ,)
            self.etr_job_new_operator += ( autocomplete.AutocompleteEntry( master=self.frm_input_operator[i], 
                                                                        textvariable=self.var_job_new_operator[i], 
                                                                        completevalues=list(self.__input_helper.getSanitizedOperatorSet()) ) ,)
            self.etr_job_new_operator[i].bind('<Return>', self.btn_job_add_operator_command[i])
            self.etr_job_new_operator[i].bind('<KP_Enter>', self.btn_job_add_operator_command[i])
            self.btn_job_rm_operator += ( ttk.Button( master=self.frm_input_operator[i], 
                                                  text="-", width=2, command=self.btn_job_rm_operator_command[i]) ,)
            #Hovertip(anchor_widget=self.btn_job_rm_operator[i], text="Ctrl/Maiusc per selezione multipla", hover_delay=1000)
            self.frm_input_operator[i].columnconfigure(index=0, weight=1)
            self.etr_job_new_operator[i].grid(row=0, column=0, columnspan=2, sticky="we")
            self.btn_job_add_operator[i].grid(row=0, column=2, padx=2)
            self.btn_job_rm_operator[i].grid(row=1, column=2, padx=2, sticky="nw")
        
            self.lst_job_operators += ( tk.Listbox( master=self.frm_input_operator[i], 
                                                    height=5,
                                                    listvariable=self.var_job_list_operators[i] ) ,)
            self.lst_job_operators[i].bind("<Delete>", self.btn_job_rm_operator_command[i])
            self.lst_job_operators[i].configure( selectmode=tk.EXTENDED )
            self.lst_job_operators[i].grid( row=1 , column=0, sticky="nwse")
            # listbox scrollbar
            self.scr_list_operators_scrollbar += ( ttk.Scrollbar(self.frm_input_operator[i], orient=tk.VERTICAL, command=self.lst_job_operators[i].yview) ,)
            self.lst_job_operators[i].configure( yscrollcommand=self.scr_list_operators_scrollbar[i].set)
            self.scr_list_operators_scrollbar[i].grid(row=1, column=1, sticky="ns")
        
            # BUILGING the frm_main_job and frm_other_job GRID

            # COLUMN of LABELS:
            labels = ["Giorni di operatività: ", "Orario operatività: ", "Medici qualificati: "]
            for j in range(len(labels)):
                ttk.Label(master=parent_frm[i], text=labels[j]).grid(row=j, column=0, sticky="ne", pady=2)
            # COLUMN of checkboxes, comboboxes and so on:
            self.frm_job_days[i].grid(row=0, column=1, sticky="nw", pady=2)
            self.frm_job_time[i].grid(row=1, column=1, sticky="nw", pady=2)
            self.frm_input_operator[i].grid(row=2, column=1, sticky="nwse", pady=2)
        
        # Preloading with given input, if there's
        self.setGivenInput(preload_input_dict=preload_input)

        # --- FRAME for the buttons ---

        # if not self.frm_buttons.winfo_ismapped(): # this works, but I don't rely on this anymore
        self.btn_submit = ttk.Button(master=self.frm_buttons, text="Salva", command=self.submit_button_pressed)
        self.btn_cancel = ttk.Button(master=self.frm_buttons, text="Annulla", command=self.cancel_button_pressed)
        self.btn_submit.pack(side="right", padx=2)
        self.btn_cancel.pack(side="right", padx=2)
        
        # now BUILDING the main frames GRID
        self.frm_common_job.grid(row=0, column=0, columnspan=2, sticky="ew")
        self.frm_main_job.grid( row=1, column=0, sticky="nesw", padx=2)
        self.frm_multi_job.grid(row=1, column=1, sticky="nesw", padx=2)
        self.frm_buttons.grid(  row=2, column=0, columnspan=2, sticky="ew")

        # re-sizability comlpliant
        self.frm_common_job.columnconfigure(index=1, weight=1)
        self.rowconfigure(1, weight=1)
        for i in range(len(parent_frm)):
            self.columnconfigure(i, weight=1)
            parent_frm[i].rowconfigure(index=2, weight=1)
            parent_frm[i].columnconfigure(index=1, weight=1)
            self.frm_input_operator[i].rowconfigure(index=1, weight=1)
            self.frm_input_operator[i].columnconfigure(index=0, weight=1)


        # after placing all elements, set the created wundow size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())

        from gui import center_window
        center_window(self)
        self.deiconify()

    
    def setGivenInput(self, preload_input_dict ):
        ''' preload fields with given input '''
        if ( "job_name" in preload_input_dict ):
            self.var_job_name.set(value=preload_input_dict["job_name"])
        if ( "job_location" in preload_input_dict ):
            self.var_job_location.set(value=preload_input_dict["job_location"])
        if ( "job_category" in preload_input_dict ):
            self.var_job_category.set(value=preload_input_dict["job_category"])
        if ( "job_days" in preload_input_dict ):
            for day in preload_input_dict["job_days"]:
                self.var_job_days[0][day-DAY_OFFSET].set(value=1)
                self.var_job_days[1][day-DAY_OFFSET].set(value=1)
        if ( "job_time" in preload_input_dict ):
            for i in range(len(self.var_job_time)):
                for j in range(len(self.var_job_time[i])):
                    self.var_job_time[i][j].set(value=preload_input_dict["job_time"][j])
        if ( "job_operators" in preload_input_dict ):
            for i in range(len(self.var_job_list_operators)):
                if (isinstance(preload_input_dict["job_operators"],list) | isinstance(preload_input_dict["job_operators"],tuple) | 
                    isinstance(preload_input_dict["job_operators"],set) & len(preload_input_dict)!=0 ):
                    self.var_job_list_operators[i].set(value=preload_input_dict["job_operators"])


    def validate_spinbox_int(self, u_input):
        if u_input == "":
            return True
        elif u_input.isdigit():
            return ( int(u_input) in range(0,24) )
        else:
            return False

    # return an array with the numbers corresponding to the selected days
    def getSelectedDays(self, which_frame):
        '''
        Get the array of selected days from the checkboxes
        which_frame = 0 if from MAIN job frame, 1 if from OTHER job frame
        '''
        selected_days = list()
        if (which_frame in [0,1]):
            for j in range(len(self.var_job_days[which_frame])):
                if ( self.var_job_days[which_frame][j].get() != 0 ):
                    selected_days.append( (DAY_OFFSET + j) )
            return selected_days
        else:
            raise ValueError(f"which_job='{which_frame}' is not a supported value")

    def btn_job_add_operator_pressed(self, which_frame, event=None):
        '''
        which_frame = 0 if from MAIN job frame, 1 if from OTHER job frame
        '''
        new_value = self.__input_helper.sanitize_operator(self.var_job_new_operator[which_frame].get())
        if (new_value != ""):
            operator_list = tuple(self.var_job_list_operators[which_frame].get())
            # check if already present
            if not new_value in operator_list:
                operator_list = (new_value, ) + operator_list
                self.var_job_list_operators[which_frame].set(operator_list)
                # clear entry after adding
                self.var_job_new_operator[which_frame].set(value="")

    def btn_job_rm_operator_pressed(self, which_frame, event=None):
        '''
        which_frame = 0 if from MAIN job frame, 1 if from OTHER job frame
        '''
        operator_list = tuple(self.var_job_list_operators[which_frame].get())
        selected_indexes = tuple(self.lst_job_operators[which_frame].curselection())
        new_operator_list = tuple()
        # create new list without the selected items
        for i in range(len(operator_list)):
            if not i in selected_indexes:
                new_operator_list += (operator_list[i], )   # then add the element in the new list
        self.var_job_list_operators[which_frame].set(new_operator_list)
        self.lst_job_operators[which_frame].select_clear(0,"end")

    def var_job_name_updated(self, name=None, index=None, mode=None):
        job_name = self.__input_helper.sanitize_string(self.var_job_name.get())
        if ((len(job_name) <= 0) | (len(job_name) >= 40)):
            frm_titles = [ "Mansione principale" , "Mansione Multi-operatore" ]
        else:
            frm_titles = [ ( job_name + ": Principale" ), ( job_name + ": Secondario (multi-operatore)" ) ]
        self.frm_main_job.configure(text = frm_titles[0] )
        self.frm_multi_job.configure(text = frm_titles[1] )
    
    def checkForChanges(self):
        ''' Return TRUE if fields are NOT EMPTY, False otherwise '''
        # Check common job fields
        if ( (self.var_job_name.get() != "") |
             (self.var_job_location.get() != "") | 
             (self.var_job_category.get() != "") ):
            return True
        # Check dedicated fields
        for i in range(2):
            if self.getSelectedDays(which_frame=i) != list():
                return True
            job_time = [ self.var_job_time[i][0].get(), self.var_job_time[i][1].get() ]
            if job_time != ["", ""]:
                return True
            if len(self.var_job_list_operators[i].get()) != 0:
                return True
        return False
    
    def checkInvalidInput(self):
        '''
            check all required fields and format
            returns a list of human readable name of invalid fields
        '''
        # HINT Per migliorarla in futuro si può pensare alla validazione in 'focusout' dei singoli campi, con cambio colore se il campo non è valido
        invalid_fields = list()
        # common fields
        if (self.var_job_name.get() == ""):
            invalid_fields.append("Nome")
        if (self.var_job_location.get() == ""):
            invalid_fields.append("Sede")
        if (self.var_job_category.get() == ""):
            invalid_fields.append("Categoria")
        # main job fields
        if len(self.getSelectedDays(which_frame=0)) == 0:
            invalid_fields.append("Giorni mansione principale")
        job_time = [ self.var_job_time[0][0].get() , self.var_job_time[0][1].get() ]
        if ((job_time[0] == "") | (job_time[1] == "")):
            invalid_fields.append("Orario mansione principale")
        elif ((not job_time[0].isdigit()) | (not job_time[1].isdigit())):
            invalid_fields.append("Orario mansione principale")
        elif ((int(job_time[0]))<0 | (int(job_time[0]))>23 | (int(job_time[1]))<0 | (int(job_time[1]))>23):
            invalid_fields.append("Orario mansione principale")
        # other job fields
        if len(self.getSelectedDays(which_frame=1)) == 0:
            invalid_fields.append("Giorni mansione secondaria")
        job_time = [ self.var_job_time[1][0].get() , self.var_job_time[1][1].get() ]
        if ((job_time[0] == "") | (job_time[1] == "")):
            invalid_fields.append("Orario mansione secondaria")
        elif ((not job_time[0].isdigit()) | (not job_time[1].isdigit())):
            invalid_fields.append("Orario mansione secondaria")
        elif ((int(job_time[0]))<0 | (int(job_time[0]))>23 | (int(job_time[1]))<0 | (int(job_time[1]))>23):
            invalid_fields.append("Orario mansione secondaria")

        return invalid_fields
            
    def on_window_close(self, event=None):
        if self.checkForChanges():
            # popup
            if (askokcancel(parent=self, title='Modifiche non salvate', icon=WARNING, 
                message='Attenzione, le modifiche effettuate non sono state salvate. Chiudere lo stesso?')):
                self.destroy()
        else:
            self.destroy()

    def cancel_button_pressed(self, event=None):
        self.on_window_close()

    def submit_button_pressed(self, event=None):
        
        invalid_fields = self.checkInvalidInput()
        # formatting string for the popup
        invalids = ""
        if (len(invalid_fields) != 0):
            for i in range(len(invalid_fields)-1):
                invalids += (invalid_fields[i] + ", ")
            invalids += invalid_fields[len(invalid_fields)-1]
            showwarning( title="Input non corretto", message=("Attenzione, i seguenti campi sono mancanti o non rispettano il formato richiesto:\n" + invalids))
        else:
            # get common values:
            job_name = self.var_job_name.get()
            job_location = self.var_job_location.get()
            job_category = self.var_job_category.get()
            # get values from MAIN and OTHER job (values in list, item 0 is main job, item 1 is other job)
            job_days = [ self.getSelectedDays(0), 
                        self.getSelectedDays(1) ]
            job_time = [ [ int(self.var_job_time[0][0].get()), int(self.var_job_time[0][1].get()) ],
                        [ int(self.var_job_time[1][0].get()), int(self.var_job_time[1][1].get()) ] ]
            job_operators = [ list(self.var_job_list_operators[0].get()),
                            list(self.var_job_list_operators[1].get()) ]
            # effective save
            # TODO: exception handling
            saved = self.__input_helper.addNewJob(
                job_name=job_name, 
                job_location=job_location, 
                job_category=job_category,
                job_days=job_days, 
                job_time=job_time, 
                job_operators=job_operators,
                multiple_operator_task=True, 
                sanitized_input=True)
            # now close the window if done correctly
            if saved:
                try:    # refresh the mansioni table, if its window is opened
                    self.refresh_mansioni_table()
                except tk.TclError:
                    pass
                finally:
                    self.destroy()
            else:
                showerror(title="Errore aggiunta mansione",
                        message="C'è stato un errore nell'aggiunta/salvataggio della mansione!")