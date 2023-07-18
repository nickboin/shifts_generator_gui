import tkinter as tk
from tkinter import ttk
from tkinter import font as tkfont
from tkinter.messagebox import showerror
import itertools
import input_helper
import gui

class Preferenze(tk.Toplevel):

    __input_file_path = str()
    __selected_job_key = str()

    def __init__(self, parent_window, input_file_path, selected_job_key=None, is_generate_running:bool=False,**kwargs):
        super().__init__(master=parent_window, **kwargs)
        #self.parent_window = parent_window
        self.withdraw() # stay hidden until window has been centered

        self.title("Preferenze Medici")

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind("<Escape>", self.on_window_close)
        self.bind("<F5>", self.reload_operator_table)

        self.__input_file_path = input_file_path
        self.inputHelper = input_helper.InputHelper(input_file_path)
        self.__selected_job_key = selected_job_key if (selected_job_key != None) else None

        # ---- MAIN FRAMES DEFINITION ----
        # FRAME for the job selector
        self.frm_job_selector = ttk.Frame(master=self, padding=10)
        # FRAME for the operator table
        self.frm_operators_list = ttk.Frame( master=self, padding=10)
        # FRAME for the edit operator
        self.frm_operators_edit = ttk.LabelFrame( master=self, padding=10)
        # FRAME for the buttons
        self.frm_buttons = ttk.Frame(master=self, padding=10)
        # Placing Main Frames
        self.frm_job_selector.grid(row=0, column=0, sticky="ew")
        self.frm_operators_list.grid(row=1, column=0, sticky="nesw")
        self.frm_operators_edit.grid(row=2, column=0, sticky="ew", padx=10)
        self.frm_buttons.grid(row=3, column=0, sticky="ew")
        # resizability compliant
        self.rowconfigure(index=1, weight=1)
        self.columnconfigure(index=0, weight=1)

        # job selector FRAME
        ttk.Label(master=self.frm_job_selector, text="Masione: ").pack(side="left")
        self.var_cmb_job_selector = tk.StringVar()
        self.cmb_job_selector = ttk.Combobox(
            master=self.frm_job_selector,
            values=self.inputHelper.getFullSanitizedJobList(),
            textvariable=self.var_cmb_job_selector,
            state="readonly" )
        self.cmb_job_selector.bind("<<ComboboxSelected>>", self.cmb__job_selector_changed)
        # function for setting default value requires trv_operators instanced, will do later
        # inglobing lbl_job_days in a frame with fixed width (to set to the maximum possible lenght
        job_days_frame_width = self.getMaxDaysWidth() + 5
        self.frm_job_days = ttk.Frame(master=self.frm_job_selector, width=job_days_frame_width)
        self.lbl_job_days = ttk.Label(master=self.frm_job_days, text="")
        self.lbl_job_days.grid(row=0, column=0, sticky="w")
        self.frm_job_days.columnconfigure(0, minsize=job_days_frame_width)
        self.frm_job_days.pack(side="right", padx=5)
        self.cmb_job_selector.pack(side="right", fill=tk.X, expand=True)


        # operator list table FRAME
        colonne_headers = { "operator":{"header":"Medico", "width":200}, 
                            "preference":{"header":"Preferenza?", "width":80}, 
                            "penality":{"header":"Penalità", "width":60}, 
                            "days":{"header":"Giorni", "width":150} }
        self.trv_operators = ttk.Treeview(
            master=self.frm_operators_list, 
            show="headings", 
            columns=tuple(colonne_headers.keys()), 
            selectmode="extended", 
            height=8 )
        for header_id in colonne_headers.keys():
            self.trv_operators.heading(header_id, text=colonne_headers.get(header_id).get("header"))
            self.trv_operators.column(header_id, minwidth=50, width=colonne_headers.get(header_id).get("width"))
        self.trv_operators.pack(side="left", fill=tk.BOTH, expand=True)
        self.trv_operators.bind("<<TreeviewSelect>>", self.trv_operators_selected)
        # scrollbar
        self.scr_trv_operators = ttk.Scrollbar(self.frm_operators_list, orient=tk.VERTICAL, command=self.trv_operators.yview)
        self.trv_operators.configure(yscroll=self.scr_trv_operators.set)
        self.scr_trv_operators.pack(fill=tk.Y, expand=True)


        # edit operator FRAME
        self.frm_operators_edit.configure(text="Preferenze medico:")
        # preference checkbutton
        self.var_preference = tk.IntVar(value=0)
        self.chk_preference = ttk.Checkbutton(
            master=self.frm_operators_edit, 
            variable=self.var_preference, 
            text="Preferenza",
            command=self.reload_preference_editor )
        # penality SUBFRAME
        self.frm_preference_penality = ttk.LabelFrame( master=self.frm_operators_edit, text="Penalità" )
        self.var_penality_status = tk.IntVar(value=0)
        self.var_penality = tk.StringVar(value="0")
        self.chk_penality_status = ttk.Checkbutton(
            master=self.frm_preference_penality, 
            variable=self.var_penality_status, 
            text="Personalizzata",
            command=self.reload_preference_editor )
        self.validation_command = ( self.register(self.validate_spinbox_int), "%P" )
        self.spn_penality = ttk.Spinbox(
            master=self.frm_preference_penality,
            textvariable=self.var_penality,
            from_=-10, to=10, wrap=False, width=3, 
            validate="key", validatecommand=self.validation_command )
        self.chk_penality_status.pack(side="top", anchor="ne", padx=(10,20), pady=(5,0))
        self.spn_penality.pack(side="left", padx=(30,10), pady=10)
        # days SUBFRAME
        self.frm_preference_days = ttk.LabelFrame( master=self.frm_operators_edit, text="Giorni", padding=10)
        # variables
        self.var_pref_days_status = tk.IntVar(value=0)
        self.var_pref_days = list()
        for i in range(7):
            self.var_pref_days.append(tk.IntVar(value=0))
        # widgets
        self.chk_pref_days_status = ttk.Checkbutton(
            master=self.frm_preference_days, 
            variable=self.var_pref_days_status, 
            text="Personalizzati",
            command=self.reload_preference_editor )
        self.chk_pref_days_status.grid(row=0, column=0, columnspan=7, sticky="nw")
        self.frm_preference_days.rowconfigure(index=0, minsize=30)
        self.chk_pref_days = tuple()
        day_labels = ["L", "M", "M", "G", "V", "S", "D"]
        for i in range(0,7):
            self.chk_pref_days += ( ttk.Checkbutton( master=self.frm_preference_days, \
                text=day_labels[i], variable=self.var_pref_days[i] ) ,)
            self.chk_pref_days[i].grid(row=1, column=i, sticky="w")
        self.btn_submit = ttk.Button(master=self.frm_operators_edit, text="Applica", command=self.apply_button_pressed)
        
        #placing all elements in frm_operators_edit
        self.chk_preference.grid(row=0, column=0, padx=(10,0), sticky="w")
        self.frm_preference_penality.grid(row=0, column=1, padx=20, sticky="nws")
        self.frm_preference_days.grid(row=0, column=2, sticky="nws")
        self.btn_submit.grid(row=1, column=0, columnspan=3, padx=5, pady=(15,0), sticky="se")
        self.frm_operators_edit.columnconfigure(2, weight=1)

        # setting default values/conditions
        select_job_index = 0
        if (self.__selected_job_key != None):
            select_job_index = self.inputHelper.getJobKeyIndex_byKey(self.__selected_job_key)
        self.var_cmb_job_selector.set(value=self.cmb_job_selector.cget("values")[select_job_index])
        if (is_generate_running):
            self.btn_submit.configure(state="disabled")
        self.cmb__job_selector_changed()

        # buttons FRAME
        self.btn_cancel = ttk.Button(master=self.frm_buttons, text="Ok", command=self.on_window_close)
        self.btn_cancel.pack(side="right")

        # after placing all elements, set the created wundow size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())

        gui.center_window(self)
        self.deiconify()


    def populate_operator_table(self):
        operator_list = self.inputHelper.getSanitizedJobOperatorsList(self.__selected_job_key)
        for operator in operator_list:
            row = (operator,) + tuple( self.inputHelper.getSanitizedJobOperatorPreference(
                job_key=self.__selected_job_key, 
                operator=operator,
                sanitized_operator=True ) )
            self.trv_operators.insert("", tk.END, values=row)

    
    def reload_operator_table(self, event=None):
        self.inputHelper.reload_from_file()
        #self.trv_operators.selection_set(tuple())  # clear selection
        for row in self.trv_operators.get_children():
            self.trv_operators.delete(row)
        self.update()
        self.populate_operator_table()


    def cmb__job_selector_changed(self, event=None):
        selected_index = self.cmb_job_selector.current()
        if (selected_index >= 0):
            self.__selected_job_key = self.inputHelper.getJobKey_byIndex(selected_index)
            # using getJobKey_byIndex works because we put the job list in combobox without reordering
            self.lbl_job_days.configure(text=f" ({self.inputHelper.getSanitizedJobDays(self.__selected_job_key)})")
        self.reload_operator_table()
        self.reset_operator_editor()


    def getSelectedOperators_list(self):
        selected_items = self.trv_operators.selection()
        selected_operators = list()
        for s_item in selected_items:
            item_dict = self.trv_operators.item(s_item)
            selected_operators.append(item_dict.get("values")[0])
        return selected_operators

    def getSelectedOperators_string(self):
        return str(self.getSelectedOperators_list()).replace("'","")[1:-1]
    

    def trv_operators_selected(self, event=None):
        operators = self.getSelectedOperators_string()
        job_name = self.inputHelper.getSanitizedJobName(self.__selected_job_key)
        self.frm_operators_edit.configure(text=f"{operators} (in {job_name})")

        self.load_preferences()

    
    def reset_operator_editor(self):
        # reset frame title
        self.frm_operators_edit.configure(text="Preferenze medico:")
        # reset preferences inputs
        self.load_preferences()


    def load_preferences(self):
        ''' 
        load selected operator preference to the editor frame;
        this method only loads data, it doesn't change component status accordingly
        '''
        # default values (new preference)
        pref_enable = pref_penality_enable = pref_days_enable = False
        pref_penality = 1
        pref_days = [ False, ] * 7

        # analyzing preference of selected operators
        operators = self.getSelectedOperators_list()
        have_same_prefs =   self.inputHelper.hasJobOperatorTheSamePreference(job_key=self.__selected_job_key, operators_list=operators, sanitized_operators=True) \
                            if (len(operators)>1) else False

        if ( (len(operators)==1) | have_same_prefs ):
            # load selected operator preferences
            preferences = self.inputHelper.getJobOperatorPreference( 
                job_key=self.__selected_job_key, 
                operator=operators[0], 
                sanitized_operator=True )
            pref_enable = preferences["preference"]
            pref_penality_enable = ( preferences["penality"] != 0 )
            pref_penality = preferences["penality"]
            pref_days_enable = ( len(preferences["day"]) > 0 )
            for day_index in preferences["day"]:
                pref_days[ (day_index - input_helper.DAY_OFFSET) ] = True
        elif (len(operators)>1):
            # load common preferences of selected operators
            # if a preference attribute is not equal between operators, put checkboxes in third state 
            common_preferences = self.inputHelper.getJobOperatorEqualPreferences(job_key=self.__selected_job_key, operators_list=operators, sanitized_operators=True)
            if ("preference" in common_preferences):
                pref_enable = True
                if ("penality" in common_preferences):
                    pref_penality_enable = True
                    self.var_penality.set(value=str(common_preferences["penality"]))
                else:
                    pref_penality_enable = None
                if ("day" in common_preferences):
                    pref_days_enable = True
                    for day in common_preferences["day"]:
                        pref_days[ (day - input_helper.DAY_OFFSET) ] = True
                else:
                    pref_days_enable = None
            else:
                pref_enable = None
                # leave others checkboxes to default disabled

        # setting preference to checkboxes and spinbox; alternate state (tristate) i done by putting its var to 2
        self.var_preference.set( value=( int(pref_enable) if (pref_enable!=None) else 2 ) )
        self.var_penality_status.set( value=( int(pref_penality_enable) if (pref_penality_enable!=None) else 2 ) )
        self.var_penality.set(value=str(pref_penality))
        self.var_pref_days_status.set(value= ( int(pref_days_enable) if (pref_days_enable!=None) else 2 ) )
        for i in range(len(self.var_pref_days)):
            self.var_pref_days[i].set(value=int(pref_days[i]))
        # reload now widget status with the just loaded values
        self.reload_preference_editor()


    def reload_preference_editor(self, event=None):
        ''' enable or disable the preference input forms based on associated variable values set '''
        if (len(self.getSelectedOperators_list())==0):
            self.chk_preference.configure(state="disabled")
        else:
            self.chk_preference.configure(state="normal")

        preference_var = self.var_preference.get()
        if (preference_var == 1):
            # preference enabled, enable the penality and days pref status chechboxes
            # and evalutate them to enable spinbox and days selection
            self.chk_penality_status.configure(state="normal")
            pref_penality_var = self.var_penality_status.get()
            if ((pref_penality_var!=0) & (pref_penality_var!=1)): # penality status in tristate
                self.chk_penality_status.state(['alternate'])
            self.set_pref_penality_input_status( enabled = (self.var_penality_status.get()==1) )

            self.chk_pref_days_status.configure(state="normal")
            pref_day_var = self.var_pref_days_status.get()
            if ((pref_day_var!=0) & (pref_day_var!=1)): # pref day status in tristate
                self.chk_pref_days_status.state(['alternate'])
            self.set_pref_days_input_status( enabled = (self.var_pref_days_status.get()==1) )
        else:
            # disable all elements on sub_frames list
            self.chk_penality_status.configure(state="disabled")
            self.set_pref_penality_input_status(enabled=False)
            self.chk_pref_days_status.configure(state="disabled")
            self.set_pref_days_input_status(enabled=False)

        if ((preference_var!=0) & (preference_var!=1)): # preference checkbox in tristate
            self.chk_preference.state(['alternate'])
            

    def set_pref_penality_input_status(self, enabled:bool):
        ''' if status=1, enable spinbox '''
        if enabled:
            self.spn_penality.configure(state="normal")
            if (not self.var_penality.get().isdigit()):
                self.var_penality.set(value="1")
        else:
            self.spn_penality.configure(state="disabled")
            self.var_penality.set(value="")

    def set_pref_days_input_status(self, enabled:bool):
        ''' if status=1, enable days checkbox '''
        state = "normal" if (enabled) else "disabled"
        for chk_day in self.chk_pref_days:
            chk_day.configure(state=state)

    
    def apply_button_pressed(self, event=None):
        operators = self.getSelectedOperators_list()
        saved = True
        if (self.var_preference.get() == 0):
            for op in operators:
                saved = self.inputHelper.deleteJobOperatorPreference(
                    job_key=self.__selected_job_key, 
                    operator=op, 
                    sanitized_operator=True )
        elif (self.var_preference.get() == 1):

            pref_penality = None   # default, penality tristate case; 
            if (self.var_penality_status.get()==0):
                pref_penality = 0
            elif (self.var_penality_status.get()==1):
                pref_penality = int(self.var_penality.get())
            
            pref_days = None  # default, days in tristate case
            if (self.var_pref_days_status.get()==0):
                pref_days = list()
            if (self.var_pref_days_status.get()==1):
                pref_days = list()
                for i, var_day in enumerate(self.var_pref_days):
                    if (var_day.get()==1):
                        pref_days.append( i + input_helper.DAY_OFFSET )

            for op in operators:
                effective_pref_penality = pref_penality
                effective_pref_days = pref_days
                # checking the third state preferences: if so place its existing value
                if (pref_penality==None) | (pref_days==None):
                    preferences = self.inputHelper.getJobOperatorPreference(
                        job_key=self.__selected_job_key, 
                        operator=op, 
                        sanitized_operator=True )
                    if (pref_penality == None):
                        effective_pref_penality = preferences["penality"]
                    if (pref_days == None):
                        effective_pref_days = preferences["day"]
                    elif (len(pref_days) < 1):
                        effective_pref_days = None
                
                saved &= self.inputHelper.setJobOperatorPreference(
                    job_key=self.__selected_job_key, 
                    operator=op, 
                    pref_penality=effective_pref_penality, 
                    pref_day=effective_pref_days, 
                    sanitized_operator=True )
        else:   # preference in tristate
            showerror(title="Errore input", message="Attenzione, preferenza non ben indicata!")

        if not saved:
            showerror(title="Errore salvataggio", message="Attenzione, il salvataggio non è andato a buon fine!")
        
        self.reload_operator_table()

    
    def validate_spinbox_int(self, u_input:str):
        if (u_input[0:1] == '-'):
            u_input = u_input[1:]

        if u_input.isdigit():
            min_range = int(self.spn_penality.cget("from"))
            max_range = int(self.spn_penality.cget("to"))
            return ( int(u_input) in range(min_range,(max_range+1)) )
        else:
            return (u_input == "")
        
    
    def getMaxDaysWidth(self):
        ''' return the maximum possible pixel occupation for days list, considerint the default label font '''

        used_font = tkfont.nametofont("TkTextFont")

        # now i'm gonna do a dumb thing: i will measure every combination to find the max
        # iterations will be something like 127, really limited
        # thank you Oscar Lopez: https://stackoverflow.com/questions/8371887/making-all-possible-combinations-of-a-list/8371891#8371891
        days_values = list(range(7))
        max_length = 0
        for i in range(1, len(days_values)+1):
            for curr_comb in itertools.combinations(days_values, i):
                cur_length = used_font.measure(text=f"({self.inputHelper.sanitize_days(curr_comb)})")
                if ( cur_length > max_length ):
                    max_length = cur_length
        return max_length


    def on_window_close(self, event=None):
        try:
            # theres something to DEBUG; the right condition has to be isinstance(self.master, gui.GUI)
            # but for some reason it say always False. Of course, using isinstance(self.master, tk.Tk)
            # works anyway because the main windows is the only Tk instance (by my design)
            # but it would be more precise checking "isinstance(self.master, gui.GUI)"
            # it may be something with imports, i will debug when I will have free time
            if ( self.master.winfo_exists() & 
                isinstance(self.master, tk.Tk) & 
                (self.master.state() == "withdrawn")):
                self.master.deiconify()
        except tk.TclError:
            # the exception get thrown when the parent_window has been already closed
            pass
        finally:
            self.destroy()