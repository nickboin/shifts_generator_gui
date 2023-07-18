import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import askokcancel, WARNING, showerror
from ttkwidgets import autocomplete
import input_helper

class Seniority(tk.Toplevel):

    __input_helper:input_helper.InputHelper
    __seniority_keys:str 
    __seniority_labels:str 
    __initial_operators_list:tuple

    def __init__(self, parent_window:tk.Widget, inputHelper:input_helper.InputHelper, is_generate_running:bool=False, **kwargs):
        super().__init__(master=parent_window, **kwargs)
        self.withdraw() # stay hidden until window has been centered

        self.title("Seniority")
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind("<Escape>", self.on_window_close)
        self.bind("<F5>", self.refreshLists)
        
        self.__input_helper = inputHelper

        self.__seniority_keys = self.__input_helper.getSeniorityKeys()
        self.__seniority_labels = self.__input_helper.getSanitizedSeniorityLabels()

        # ---- MAIN FRAMES DEFINITIONS ----
        self.configure(pady=10)
        # FRAME for the input/edit elements
        self.frm_cmo= ttk.LabelFrame( master=self, padding=10, text=self.__seniority_labels[0])
        # FRAME for the MAIN job input
        self.frm_sp = ttk.LabelFrame( master=self, padding=10, text=self.__seniority_labels[1])
        # FRAME for the MULTIOPERATOR job input
        self.frm_mfs = ttk.LabelFrame( master=self, padding=10, text=self.__seniority_labels[2])
        # FRAME for the action buttons
        self.frm_buttons = ttk.Frame( master=self)

        frm_seniority = [ self.frm_cmo, self.frm_sp, self.frm_mfs ]

        # widget arrays initialization
        self.btn_add_operator = tuple()
        self.var_new_operator = tuple()
        self.etr_new_operator = tuple()
        self.btn_rm_operator = tuple()
        self.var_list_operators = tuple()
        self.lst_operators = tuple()
        self.scr_lst_operators_scrollbar = tuple()
        self.__initial_operators_list = list()  # useful for checking changes

        for i, frm in enumerate(frm_seniority):
            
            add_command = lambda event=None, frm_idx=i : self.btn_add_operator_pressed(event=event, which_frame=frm_idx)
            self.btn_add_operator += ( ttk.Button( master=frm, text="+", width=2, command=add_command ) ,)
            self.var_new_operator += ( tk.StringVar() ,)
            self.etr_new_operator += ( autocomplete.AutocompleteEntry( master=frm, textvariable=self.var_new_operator[i], completevalues=list() ) ,)
            self.etr_new_operator[i].bind('<Return>', add_command)
            self.etr_new_operator[i].bind('<KP_Enter>', add_command)
            rm_command = lambda event=None, frm_idx=i : self.btn_rm_operator_pressed(event=event, which_frame=frm_idx)
            self.btn_rm_operator += ( ttk.Button( master=frm, text="-", width=2, command=rm_command ) ,)
            #Hovertip(anchor_widget=self.btn_job_rm_operator[i], text="Ctrl/Maiusc per selezione multipla", hover_delay=1000)
            frm.columnconfigure(index=0, weight=1)
            self.etr_new_operator[i].grid(row=0, column=0, columnspan=2, sticky="we")
            self.btn_add_operator[i].grid(row=0, column=2, padx=4, pady=2)
            self.btn_rm_operator[i].grid(row=1, column=2, padx=4, pady=2, sticky="nw")

            self.__initial_operators_list.append(self.__input_helper.getSanitizedSeniorityList(seniority_label=self.__seniority_keys[i]).copy())
            self.var_list_operators += ( tk.Variable( value=self.__initial_operators_list[i] ) ,)
            self.lst_operators += ( tk.Listbox( master=frm, height=8, listvariable=self.var_list_operators[i] ) ,)
            self.lst_operators[i].bind("<Delete>", rm_command)
            self.lst_operators[i].configure( selectmode=tk.EXTENDED )
            self.lst_operators[i].grid( row=1 , column=0, sticky="nwse")
            # listbox scrollbar
            self.scr_lst_operators_scrollbar += ( ttk.Scrollbar(master=frm, orient=tk.VERTICAL, command=self.lst_operators[i].yview) ,)
            self.lst_operators[i].configure( yscrollcommand=self.scr_lst_operators_scrollbar[i].set)
            self.scr_lst_operators_scrollbar[i].grid(row=1, column=1, sticky="ns")
        self.updateAutocompletions()

        # make the initial list immutable
        new_tuple = tuple()
        for lista in self.__initial_operators_list:
            new_tuple += ( tuple(lista) ,)
        self.__initial_operators_list = new_tuple

        # --- FRAME for the buttons ---

        # if not self.frm_buttons.winfo_ismapped(): # this works, but I don't rely on this anymore
        self.btn_submit = ttk.Button(master=self.frm_buttons, text="Salva", command=self.submit_button_pressed)
        self.btn_cancel = ttk.Button(master=self.frm_buttons, text="Annulla", command=self.cancel_button_pressed)
        self.btn_submit.pack(side="right", padx=5)
        self.btn_cancel.pack(side="right", padx=5)
        if (is_generate_running):
            self.btn_submit.configure(state="disabled")
        
        # now BUILDING the main frames GRID
        self.frm_cmo.grid(      row=0, column=0, sticky="nesw", padx=10)
        self.frm_sp.grid(       row=0, column=1, sticky="nesw", padx=5)
        self.frm_mfs.grid(      row=0, column=2, sticky="nesw", padx=10)
        self.frm_buttons.grid(  row=1, column=0, columnspan=3, sticky="ew", padx=5, pady=(10,0))

        # resizability support
        self.rowconfigure(index=0, weight=1)
        for i, frm in enumerate(frm_seniority):
            self.columnconfigure(index=i, weight=1)
            frm.rowconfigure(index=1, weight=1)
            frm.columnconfigure(index=0, weight=1)

        # after placing all elements, set the created window size as minimum size
        self.update()
        self.wm_minsize(width=self.winfo_width(), height=self.winfo_height())

        from gui import center_window
        center_window(self)
        self.deiconify()


    def refreshLists(self, event=None):
        seniority_operators = self.__input_helper.getSanitizedSeniorityDict()
        for i in range(len(self.__seniority_keys)):
            self.var_list_operators[i].set( value = seniority_operators[self.__seniority_keys[i]].copy() )

    def updateAutocompletions(self):
        ''' update autocompletion in every new_operator entry (a list without already in list operators) '''
        all_operators = self.__input_helper.getSanitizedOperatorSet()
        for i in range(len(self.__seniority_keys)):
            operators_in_list = set(self.var_list_operators[i].get())
            self.etr_new_operator[i].configure( completevalues=list(all_operators.difference(operators_in_list)) )


    def chechkForChanges(self):
        ''' check for changes, return the seniority_keys of changed lists '''
        changed = list()
        for i in range(len(self.__seniority_keys)):
            if (set(self.__initial_operators_list[i]) != set(self.var_list_operators[i].get())):
                changed.append(self.__seniority_keys[i])
        return changed


    def btn_add_operator_pressed(self, which_frame:int, event=None):
        input_operator = self.__input_helper.sanitize_operator(self.var_new_operator[which_frame].get())
        operators_list = list(self.var_list_operators[which_frame].get())
        # check if already in list
        if (not input_operator in operators_list):
            # put the new operator on top of the list
            operators_list.insert(0,input_operator)
            self.var_list_operators[which_frame].set( value=operators_list )
        # reset the input field
        self.var_new_operator[which_frame].set(value="")
        # remove the inserted operator from autocompletion
        self.updateAutocompletions()

    def btn_rm_operator_pressed(self, which_frame:int, event=None):
        selected_op_index = list(self.lst_operators[which_frame].curselection())
        # reverse needed, because if i remove elements by index i can cause inconsistency removing from the start, so it's better start from the end
        selected_op_index.reverse()
        operators_list = list(self.var_list_operators[which_frame].get())
        # remove all selected operators from list
        for idx in selected_op_index:
            operators_list.pop(idx)
        self.var_list_operators[which_frame].set( value=operators_list )
        # add the removed operators to the autocompletion
        self.updateAutocompletions()


    def submit_button_pressed(self, event=None):
        # save only changed keys (to not open file too much times; the alternative is to write a funcion that write all seniority dict, that is not bad, but for now ok)
        changed_keys = self.chechkForChanges()
        saved = True
        if bool(len(changed_keys)):
            for i, key in enumerate(self.__seniority_keys):
                if (key in changed_keys):
                    saved &= self.__input_helper.setSeniorityOperatorList(
                        operator_list=self.var_list_operators[i].get(), 
                        is_operator_sanitized=True,
                        seniority_label=key )
        if saved:
            self.destroy()
        else:
            showerror(parent=self, title="Errore salvataggio", message="Errore durante il salvataggio delle modifiche!")
                    
    def cancel_button_pressed(self, event=None):
        self.on_window_close()

    def on_window_close(self, event=None):
        if (self.chechkForChanges()):
            self.focus()
            if (askokcancel(parent=self, title="Modifiche non salvate", icon=WARNING, message="Attenzione, ci sono modifiche non salvate.\nUscire lo stesso?")):
                self.destroy()
        else:
            self.destroy()