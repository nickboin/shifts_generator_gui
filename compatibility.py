import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror, askokcancel, WARNING
from tkinter import font as tkfont
from ttkwidgets import autocomplete
import itertools
import input_helper
import gui

class Compatibility(tk.Toplevel):

    __input_helper:input_helper.InputHelper
    __is_generate_running:bool              # from the main program, keep the window edit widget disabled
    __selected_job_key:str                  # hold the job_key selected by cmb_job_selector
    __current_job_compatibility_keys:list   # to save the key list of compatibilities shown in treeview
    __current_add_job_autocompletions:list  # to save keys of autocomletions on add compatibility combobox
    __checkbox_days_status:dict             # useful to save the status of checkboxes and reveil changes

    def __init__(self, parent_window, inputHelper:input_helper.InputHelper, selected_job_key=None, is_generate_running:bool=False, **kwargs):
        super().__init__(master=parent_window, **kwargs)
        self.withdraw() # stay hidden until window has been centered

        self.title("Compatibilità mansioni")

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind("<Escape>", self.on_window_close)
        self.bind("<F5>", self.reload_compatibility_table)

        self.__input_helper = inputHelper
        self.__selected_job_key = selected_job_key if (selected_job_key != None) else None
        self.__is_generate_running = is_generate_running

        # ---- MAIN FRAMES DEFINITION ----
        # FRAME for the job selector and the compatibility list
        self.frm_job_selector = ttk.Frame(master=self)
        # FRAME for the compatibility list
        self.frm_compatibility = ttk.Frame(master=self, padding=10)
        # FRAME for adding/removing a compatibility
        self.frm_comp_edit = ttk.Frame(master=self)
        # FRAME for the edit compatibility days
        self.frm_comp_days = ttk.LabelFrame( master=self, padding=10, text="Giorni di compatibilità:")
        # FRAME for the buttons
        self.frm_buttons = ttk.Frame(master=self, padding=10)

        # Placing Main Frames
        self.frm_job_selector.grid(row=0, column=0, sticky="ew", padx=(10,0), pady=10)
        self.frm_compatibility.grid(row=1, column=0, sticky="nesw")
        self.frm_comp_edit.grid(row=2, column=0, sticky="ew")
        self.frm_comp_days.grid(row=3, column=0, sticky="ew", padx=10)
        self.frm_buttons.grid(row=4, column=0, sticky="ew")
        # resizability compliant
        self.rowconfigure(index=1, weight=1)
        self.columnconfigure(index=0, weight=1)


        # TODO: placing frame and label with days
        # TODO: some keyboard shortcut
        # job selector FRAME
        ttk.Label(master=self.frm_job_selector, text="Masione: ").pack(side="left")
        self.var_cmb_job_selector = tk.StringVar()
        self.cmb_job_selector = ttk.Combobox(
            master=self.frm_job_selector,
            values=self.__input_helper.getFullSanitizedJobList(),
            textvariable=self.var_cmb_job_selector,
            state="readonly" )
        self.cmb_job_selector.bind("<<ComboboxSelected>>", self.cmb__job_selector_changed)
        self.lbl_job_days = ttk.Label(master=self.frm_job_selector, text="")
        self.lbl_job_days.pack(side="right", padx=5)

        # inglobing lbl_job_days in a frame with fixed width (to set to the maximum possible lenght
        job_days_frame_width = self.getMaxDaysWidth() + 5
        self.frm_job_days = ttk.Frame(master=self.frm_job_selector, width=job_days_frame_width)
        self.lbl_job_days = ttk.Label(master=self.frm_job_days, text="")
        self.lbl_job_days.grid(row=0, column=0, sticky="w")
        self.frm_job_days.columnconfigure(0, minsize=job_days_frame_width)
        self.frm_job_days.pack(side="right", padx=5)
        self.cmb_job_selector.pack(side="right", fill=tk.X, expand=True)



        # operator list table FRAME
        colonne_headers = { "job":{"header":"Mansioni compatibili", "width":400}, 
                            "days":{"header":"Giorni", "width":200} }
        self.trv_compatibility = ttk.Treeview(
            master=self.frm_compatibility, 
            show="headings", 
            columns=tuple(colonne_headers.keys()), 
            selectmode="extended", 
            height=8 )
        for header_id in colonne_headers.keys():
            self.trv_compatibility.heading(header_id, text=colonne_headers.get(header_id).get("header"))
            self.trv_compatibility.column(header_id, minwidth=50, width=colonne_headers.get(header_id).get("width"))
        self.trv_compatibility.pack(side="left", fill=tk.BOTH, expand=True)
        self.trv_compatibility.bind("<<TreeviewSelect>>", self.comp_selection_change)
        self.trv_compatibility.bind("<Delete>", self.btn_rm_comp_pressed)
        # scrollbar
        self.scr_trv_compatibility = ttk.Scrollbar(self.frm_compatibility, orient=tk.VERTICAL, command=self.trv_compatibility.yview)
        self.trv_compatibility.configure(yscroll=self.scr_trv_compatibility.set)
        self.scr_trv_compatibility.pack(fill=tk.Y, expand=True)

        # FRAME for adding/edit(removing) a compatibility
        # SUB-FRAME for adding compatibility
        self.frm_add_comp = ttk.LabelFrame(master=self.frm_comp_edit, text="Aggiunta compatibilità")
        self.var_cmb_add_comp = tk.StringVar()
        self.cmb_add_comp = autocomplete.AutocompleteCombobox( 
            master=self.frm_add_comp, 
            completevalues=list(), 
            textvariable=self.var_cmb_add_comp )
        self.var_cmb_add_comp.trace_add("write", self.validate_add_compatibility)
        #self.cmb_add_comp.bind("<<ComboboxSelected>>", )
        self.cmb_add_comp.pack(side="left", fill=tk.X, expand=True, padx=8, pady=8)
        self.cmb_add_comp.bind('<Return>', self.btn_add_comp_pressed)
        self.cmb_add_comp.bind('<KP_Enter>', self.btn_add_comp_pressed)
        self.btn_add_comp = ttk.Button( master=self.frm_add_comp, text="Aggiungi", command=self.btn_add_comp_pressed, state="disabled" )
        self.btn_add_comp.pack(side="right", anchor="e", padx=8, pady=8)
        # SUB-FRAME for edit(remove) compatibility
        self.frm_edit_selection = ttk.LabelFrame(master=self.frm_comp_edit, text="Selezione:")
        self.btn_rm_comp = ttk.Button( master=self.frm_edit_selection, text="Rimuovi", command=self.btn_rm_comp_pressed, state="disabled" )
        self.btn_rm_comp.pack(side="right", padx=8, pady=8)
        # placing Sub-Frames
        self.frm_add_comp.pack(side="left", fill=tk.X, expand=True, padx=(10,5))
        self.frm_edit_selection.pack(side="right", padx=(5,10))

        # edit compatibility days FRAME
        # variables
        self.var_comp_days_status = tk.StringVar(value="Come mansione")
        self.var_comp_days = list()
        for i in range(7):
            self.var_comp_days.append(tk.IntVar(value=0))
        # widgets
        # enable chekbutton, in a subsubframe to fix the width previewing checkbutton label changes
        self.frm_comp_days_enable = ttk.Frame(master=self.frm_comp_days)
        self.chk_comp_days_status = ttk.Checkbutton(
            master=self.frm_comp_days_enable, 
            variable=self.var_comp_days_status, 
            textvariable=self.var_comp_days_status,
            onvalue="Personalizzata", offvalue="Come mansione",
            command=self.chkbtn_pressed )
        self.chk_comp_days_status.pack(side="left")
        self.frm_comp_days_enable.grid(row=0, column=0, sticky="w")
        # make that frame with a fixed width, based on maximum checkbox text occupation
        used_font = tkfont.nametofont("TkTextFont")
        chk_maxwidth = used_font.measure(text=self.chk_comp_days_status.cget("onvalue")) \
            if (used_font.measure(text=self.chk_comp_days_status.cget("onvalue")) > used_font.measure(text=self.chk_comp_days_status.cget("offvalue"))) \
            else used_font.measure(text=self.chk_comp_days_status.cget("offvalue"))   # effective maximum space ocupation
        chk_maxwidth += 50  # the effective padding
        self.frm_comp_days_enable.configure(width=chk_maxwidth)
        self.frm_comp_days.columnconfigure(0, minsize=chk_maxwidth)
        # days checkbuttons
        self.chk_comp_days = tuple()
        day_labels = ["L", "M", "M", "G", "V", "S", "D"]
        for i in range(0,7):
            self.chk_comp_days += ( ttk.Checkbutton( master=self.frm_comp_days, \
                text=day_labels[i], variable=self.var_comp_days[i], command=self.chkbtn_pressed ) ,)
            self.chk_comp_days[i].grid(row=0, column=(i+1), sticky="e")
        # apply button
        self.btn_apply_days = ttk.Button( master=self.frm_comp_days, text="Applica", state="disabled", command=self.btn_apply_days_comp_pressed )
        self.btn_apply_days.grid(row=0, column=9, sticky="sw", padx=(25,0))

        # setting default values/conditions
        select_job_index = 0
        if (self.__selected_job_key != None):
            select_job_index = self.__input_helper.getJobKeyIndex_byKey(self.__selected_job_key)
        self.var_cmb_job_selector.set(value=self.cmb_job_selector.cget("values")[select_job_index])
        self.cmb__job_selector_changed()

        # buttons FRAME
        self.btn_cancel = ttk.Button(master=self.frm_buttons, text="Ok", command=self.on_window_close)
        self.btn_cancel.pack(side="right", padx=5)

        # after placing all elements, set the created wundow size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())

        gui.center_window(self)
        self.deiconify()

    
    def populate_compatibility_table(self):
        compatibility_list = self.__input_helper.getSanitizedJobCompatibilityList(self.__selected_job_key)
        # building structures to permit sorting
        self.__current_job_compatibility_keys = list()  # ordered job_key list used to manage table row selection
        job_compatibilities_attributes = dict()
        for compatibility in compatibility_list:
            self.__current_job_compatibility_keys.append(compatibility["job_key"])
            comp_attributes = { "job_name":compatibility["job_name"] , 
                                "days":(str(compatibility["days"]) if ("days" in compatibility) else "") }
            job_compatibilities_attributes.update( { compatibility["job_key"]:comp_attributes } )
        self.__current_job_compatibility_keys.sort()
        for comp_job_key in self.__current_job_compatibility_keys:
            row = ( job_compatibilities_attributes[comp_job_key]["job_name"], job_compatibilities_attributes[comp_job_key]["days"] )
            self.trv_compatibility.insert("", tk.END, values=row)

    
    def reload_compatibility_table(self, event=None):
        self.__input_helper.reload_from_file()
        #self.trv_compatibility.selection_set(tuple())  # clear selection
        for row in self.trv_compatibility.get_children():
            self.trv_compatibility.delete(row)
        self.update()
        self.populate_compatibility_table()

    
    def refresh_add_compatibility_autocompletions(self):
        # refresh the completion values for the add compatibility combobox
        self.__current_add_job_autocompletions = list(set(self.__input_helper.getJobKeyList()).difference(set(self.__current_job_compatibility_keys)))
        self.__current_add_job_autocompletions.sort()
        sanitized_completions = list()
        for jk in self.__current_add_job_autocompletions:
            sanitized_completions.append(self.__input_helper.getFullSanitizedJob(job_key=jk))
        self.cmb_add_comp.configure(completevalues=sanitized_completions)


    
    def cmb__job_selector_changed(self, event=None):
        selected_index = self.cmb_job_selector.current()
        if (selected_index >= 0):
            self.__selected_job_key = self.__input_helper.getJobKey_byIndex(selected_index)
            # using getJobKey_byIndex works because we put the job list in combobox without reordering
            self.lbl_job_days.configure(text=f"({self.__input_helper.getSanitizedJobDays(self.__selected_job_key)})")
            self.reload_compatibility_table()
            self.reload_comp_days_frame()
            self.refresh_add_compatibility_autocompletions()

    
    def getSelectedJobsKeys(self):
        selected_items = self.trv_compatibility.selection()
        selected_jobs = list()
        for s_item in selected_items:
            item_index = self.trv_compatibility.index(s_item)
            selected_jobs.append(self.__current_job_compatibility_keys[item_index])
        return selected_jobs

    def comp_selection_change(self, event=None):
        selected_comps = self.getSelectedJobsKeys()
        # reload the days
        self.reload_comp_days_frame()
        # enable the delete button if there is selection
        if (bool(len(selected_comps)) & (not self.__is_generate_running)):
            self.btn_rm_comp.configure(state="normal")
        else:
            self.btn_rm_comp.configure(state="disabled")


    def reload_comp_days_frame(self):
        ''' enable or disable the days checkboxes based on their variable values '''
        selected_comps = self.getSelectedJobsKeys()     # selected compatibility entries from table
        if (len(selected_comps)<=0):
            # with no selection, reset the days to the default job days
            self.reset_default_job_days_frame()
            # and disable chk_days_status
            self.chk_comp_days_status.configure(state="disabled")
        elif (len(selected_comps)==1):
            # re-enable chk_days_status before proceeding
            self.chk_comp_days_status.configure(state="normal")
            comp_days = self.__input_helper.getJobCompatibleDays(self.__selected_job_key, selected_comps[0])
            if (len(comp_days)==0):
                # if compatibility hasn't days set, set the default job days
                self.reset_default_job_days_frame()
            else:
                # set compatibility days
                self.set_custom_job_days_frame(job_days=comp_days)
        else:
            # multiple compatibility selected; checking for equals days
            # re-enable chk_days_status before proceeding
            self.chk_comp_days_status.configure(state="normal")
            comp_days = list()  # list made of different days lists, (not empty)
            for comp in selected_comps:
                c_d = self.__input_helper.getJobCompatibleDays(self.__selected_job_key, comp)
                if (len(c_d) > 0):
                    c_d.sort()
                if (not c_d in comp_days):
                    comp_days.append(c_d)

            if ((len(comp_days) == 1) & (len(comp_days[0]) == 0)):
                # all selected compatibilities don't have days set: set default job days
                self.reset_default_job_days_frame()
            elif ((len(comp_days) == 1) & (len(comp_days[0]) != 0)):
                # all selected compatibilities have the same days
                self.set_custom_job_days_frame(job_days=comp_days[0])
            else:
                # selected compatibilities have different days: third state
                self.var_comp_days_status.set( value="Mantieni" )
                self.chk_comp_days_status.state(['alternate'])
                for i,varchkbtn in enumerate(self.var_comp_days):
                    varchkbtn.set( value=0 )
                    self.chk_comp_days[i].configure(state="disabled")
                self.__checkbox_days_status = { "status":2, "days":list() }
        # days just loaded, disable apply button
        self.btn_apply_days.configure(state="disabled")
                    
                
    def reset_default_job_days_frame(self):
        job_default_days = self.__input_helper.getJobDays(self.__selected_job_key)  # days of selected job in combobox
        self.var_comp_days_status.set( value=self.chk_comp_days_status.cget("offvalue") )
        for i,varchkbtn in enumerate(self.var_comp_days):
            varchkbtn.set( value= int( (i+input_helper.DAY_OFFSET) in job_default_days ) )
            self.chk_comp_days[i].configure(state="disabled")
        self.__checkbox_days_status = { "status":0, "days":list() }
                
    def set_custom_job_days_frame(self, job_days):
        self.var_comp_days_status.set( value=self.chk_comp_days_status.cget("onvalue") )
        for i,varchkbtn in enumerate(self.var_comp_days):
            varchkbtn.set( value= int( (i+input_helper.DAY_OFFSET) in job_days ) )
            self.chk_comp_days[i].configure(state="enabled")
        self.__checkbox_days_status = { "status":1, "days":job_days }
        
    
    def set_comp_days_input_status(self, enabled:bool):
        ''' if status=1, enable days checkbox '''
        state = "normal" if (enabled) else "disabled"
        for chk_day in self.chk_comp_days:
            chk_day.configure(state=state)


    def chkbtn_pressed(self, event=None):
        # enable/disable days checkbuttons accordingly to what chk_comp_days_status tells
        chk_days_status = (self.var_comp_days_status.get() == self.chk_comp_days_status.cget("onvalue"))
        self.set_comp_days_input_status(enabled=chk_days_status)
        # check for changes to decide if enable or disable the apply button
        if ((not self.__is_generate_running) & self.checkDaysChanges()): 
            self.btn_apply_days.configure(state="normal")
        else:
            self.btn_apply_days.configure(state="disabled")

    def getSelectedDays(self):
        selected_days = list()
        if (self.var_comp_days_status.get() == self.chk_comp_days_status.cget('onvalue')):
            for i, day_chk_var in enumerate(self.var_comp_days):
                if (day_chk_var.get() == 1):
                    selected_days.append( i+input_helper.DAY_OFFSET )
        return selected_days

    def checkDaysChanges(self):
        if ((self.__checkbox_days_status["status"]==0) & (self.var_comp_days_status.get() == self.chk_comp_days_status.cget("offvalue"))):
            # days selection not enabled, nothing to check
            return False
        elif ((self.__checkbox_days_status["status"]==1) & (self.var_comp_days_status.get() == self.chk_comp_days_status.cget("onvalue"))):
            # chk_comp_days_status has not been modified, check every day
            for i,chkbtn in enumerate(self.var_comp_days):
                if ((chkbtn.get()==1) == (not (i+input_helper.DAY_OFFSET) in self.__checkbox_days_status["days"])):
                    return True     # days have changed
            return False    # nothing changed if i reached this point    
        elif ((self.__checkbox_days_status["status"]==2) & (self.var_comp_days_status.get() == self.chk_comp_days_status.instate(['alternate']))):
            # days selection still in third state, nothing to check
            return False
        else:   # if the comp days status chkbutton has changed:
            return True
        

    def checkAddCompatibility(self):
        '''  
        allowed input:
         - full santized job location and name [ "location: extended name" ]
         - sanitized job location and name [ "location: name" ]
         - raw job_key
        all checked with .lower(), to facilitate the user
        '''
        # check validity by step: from the most probable to the less probable; start with full sanitized names
        #full_sanitized_list = self.cmb_add_comp.cget("completelist")
        if (self.cmb_add_comp.current()>=0):   # check if inputted a value from completelist
            return True
        # next step: check sanitized names
        input_field = self.var_cmb_add_comp.get()
        for jk in self.__current_add_job_autocompletions:
            if (input_field.lower() == self.__input_helper.getFullSanitizedJobName(job_key=jk).lower()):
                return True
        # next step: raw keys
        return (input_field in self.__current_add_job_autocompletions)

    
    def validate_add_compatibility(self, name=None, index=None, mode=None):
        ''' track the add compatibility input value, enable the add button if the input is valid '''
        self.trv_compatibility.selection_set(tuple())  # clear treeview selection
        if ((not self.__is_generate_running) & self.checkAddCompatibility()):
            self.btn_add_comp.configure(state="normal")
        else:
            self.btn_add_comp.configure(state="disabled")
        

    def btn_add_comp_pressed(self, event=None):
        input_comp_key = None
        selected_cmb_index = self.cmb_add_comp.current()
        input_field = self.var_cmb_add_comp.get()
        if (selected_cmb_index>=0):
            input_comp_key = self.__current_add_job_autocompletions[selected_cmb_index]
        else:
            if (input_field in self.__current_add_job_autocompletions):
                input_comp_key = input_field
            else:
                for jk in self.__current_add_job_autocompletions:
                    if (input_field.lower() == self.__input_helper.getFullSanitizedJobName(job_key=jk).lower()):
                        input_comp_key = jk
                        break
        if (input_comp_key!=None):
            saved = self.__input_helper.addJobCompatibility(job_key=self.__selected_job_key, comp_job_key=input_comp_key)
            if saved:
                self.var_cmb_add_comp.set("")
            else:
                showerror(parent=self, title="Errore salvataggio", message="Errore durante il salvataggio!")
            self.reload_compatibility_table()
            self.refresh_add_compatibility_autocompletions()
        #else:
        #    showerror(parent=self, title="Errore input", message=f"Errore: input {input_field} non valido")


    def btn_rm_comp_pressed(self, event=None):
        comp_list = self.getSelectedJobsKeys()
        comp_list_sanitized = ""
        for comp in comp_list:
            comp_list_sanitized += ( self.__input_helper.getFullSanitizedJob(comp) + "\n" )
        if (askokcancel( parent=self, title="Rimozione compatibilità", 
                message=f"Conferma rimozione delle seguenti compatibilita:",
                detail = comp_list_sanitized, icon=WARNING )):
            saved = True
            for comp in comp_list:
                saved &= self.__input_helper.deleteJobCompatibility(job_key=self.__selected_job_key, comp_job_key=comp)
            if (not saved):
                showerror(parent=self, title="Errore salvataggio", message="Errore salvataggio durante la rimozione!")
            self.reload_compatibility_table()
            self.refresh_add_compatibility_autocompletions()

    def btn_apply_days_comp_pressed(self, event=None):
        comp_list = self.getSelectedJobsKeys()
        days = self.getSelectedDays() if (self.var_comp_days_status.get() == self.chk_comp_days_status.cget('onvalue')) else None
        saved = True
        for comp in comp_list:
            saved &= self.__input_helper.editJobCompatibility(job_key=self.__selected_job_key, comp_job_key=comp, days=days)
        if (not saved):
            showerror(parent=self, title="Errore salvataggio", message="Errore salvataggio delle modifiche!")
        # the third state management (keep) is not implemented, because in keep mode the apply button is not enabled!
        self.reload_compatibility_table()

    
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
                cur_length = used_font.measure(text=f"({self.__input_helper.sanitize_days(curr_comb)})")
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