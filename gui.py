import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror
import tkcalendar as tkcal
import datetime
import tkinter.messagebox as msgbox
import os.path as path
import time
import subprocess
from numpy import floor, ceil

import input_helper as i_help

class GUI(tk.Tk):

    __is_generate_running = False
    __INPUT_PATH = path.join(path.dirname(__file__), "input", "input.json")
    __generate_process:subprocess.Popen

    def close_window(self):
        self.withdraw()

    def __init__(self):
        super().__init__()
        self.withdraw() # stay hidden until window has been centered
        self.title("Gestione turni")
        self.resizable(False, False)

        self.protocol("WM_DELETE_WINDOW", self.on_window_close)
        self.bind_all('<Control-c>', self.ctrl_c_handler)
        
        # ---- DEFINIZIONE FRAMES PRINCIPALI ----
        # FRAME per i bottoni alle funzioni del programma
        self.frm_actions = ttk.Frame(master=self, padding=10)
        self.frm_actions.grid(row=0)
        # Separatore
        #ttk.Separator(master=self, orient="horizontal").grid(row=1, sticky="ew")
        # FRAME per i controlli del programma generatore turni
        self.frm_calculate = ttk.LabelFrame(master=self, text="Controlli programma generatore turni")
        self.frm_calculate.grid(row=1, pady=5, padx=5)
        # FRAME con progressbar e label per l'avanzamento del tempo, istanziato pronto per essere poi mostrato
        self.frm_elapsed_time = ttk.Frame( master=self )

        # MENU
        self.menubar = tk.Menu(master=self)
        self.menu_file = tk.Menu(master=self.menubar, tearoff=0)
        #self.menu_file.add_command(label="Impostazioni")
        self.menu_file.add_command(label="Exit", command=self.on_window_close)
        self.menu_jobs = tk.Menu(master=self.menubar, tearoff=0)
        self.menu_jobs.add_command(label="Mansionario", command=self.mansionario_button_pressed)
        self.menu_jobs.add_command(label="Mansioni", command=self.mansioni_button_pressed)
        self.menu_jobs.add_command(label="Compatibilità", command=self.compatibility_menu)
        self.menu_medic = tk.Menu(master=self.menubar, tearoff=0)
        self.menu_medic.add_command(label="Preferenze", command=self.preferenze_menu)
        self.menu_medic.add_command(label="Seniority", command=self.seniority_menu)
        #self.menu_shifts = tk.Menu(master=self.menubar, tearoff=0)
        #self.menu_shifts.add_command(label="Assenze")
        #self.menu_shifts.add_command(label="Monte ore")
        self.menu_help = tk.Menu(master=self.menubar, tearoff=0)
        self.menu_help.add_command(label="Manuale", command=self.manual_menu)

        self.menubar.add_cascade(label="File", menu=self.menu_file, underline=0)
        self.menubar.add_cascade(label="Mansioni", menu=self.menu_jobs, underline=0)
        self.menubar.add_cascade(label="Medici", menu=self.menu_medic, underline=0)
        #self.menubar.add_cascade(label="Turni", menu=self.menu_shifts, underline=0)
        self.menubar.add_cascade(label="?", menu=self.menu_help, underline=0)
        self.configure(menu=self.menubar)



        # FRAME per i bottoni alle funzioni del programma

        ttk.Button( master=self.frm_actions, text="Mansioni", command=self.mansioni_button_pressed).grid(row=1, column=1, padx=5)
        ttk.Button( master=self.frm_actions, text="Mansionario", command=self.mansionario_button_pressed).grid(row=1, column=2, padx=10)
        ttk.Button( master=self.frm_actions, text="Compatibilità", command=self.compatibility_menu).grid(row=1, column=3, padx=5)

        
        # FRAME per i controlli del programma generatore turni

        # ----- DEFINIZIONE SOTTO-FRAME -----
        # FRAME che contiene i bottoni start/stop calcolo
        self.frm_calculate_buttons = ttk.Frame( master=self.frm_calculate )
        self.frm_calculate_buttons.grid(row=0, column=0, 
                                        padx=20, pady=10)
        # FRAME per l'input del timeout di calcolo
        self.frm_calculate_timeout = ttk.Frame( master=self.frm_calculate )
        self.frm_calculate_timeout.grid(row=0, column=1, 
                                        padx=20, pady=10)
        # FRAME per input settimana di riferimento per il calcolo
        self.frm_calculate_week = ttk.Frame(master=self.frm_calculate)
        self.frm_calculate_week.grid(row=1, column=0, 
                                     padx=20, pady=10)
        # FRAME per input mesi da calcolare
        self.frm_calculate_months = ttk.Frame(master=self.frm_calculate)
        self.frm_calculate_months.grid(row=1, column=1, 
                                     padx=20, pady=10)
        

        # FRAME  start/stop calcolo
        # bottone di start calcolo
        self.btn_start_calculate = ttk.Button( master=self.frm_calculate_buttons,
            text="START", 
            command=self.start_button_pressed)
        self.btn_start_calculate.pack(side="left", padx=5)
        # bottone di stop calcolo
        self.btn_stop_calculate = ttk.Button(master=self.frm_calculate_buttons,
            text="STOP", 
            command=self.stop_button_pressed, 
            state="disabled" )
        self.btn_stop_calculate.pack(side="right", padx=5)

        # FRAME per l'input del timeout di calcolo
        self.var_min_timeout = tk.StringVar( value="1" )
        self.validate_min_timeout = self.register(self.validate_spinbox_min)
        self.var_sec_timeout = tk.StringVar( value="00" )
        self.validate_sec_timeout = self.register(self.validate_spinbox_sec)
        # label "Timeout calcolo"
        ttk.Label(master=self.frm_calculate_timeout, text="Timeout calcolo:").grid(row=1, column=1, columnspan=4, sticky="sw")
        # spinbox per l'input dei minuti del timeout di calcolo per il programma
        self.spn_min_timeout = ttk.Spinbox( master=self.frm_calculate_timeout,
            from_=0, to=(60*24), wrap=False, width=5, 
            textvariable=self.var_min_timeout,
            validate="key", validatecommand=(self.validate_min_timeout, "%P") )
        self.spn_min_timeout.grid(row=2, column=1, sticky="ne")
        # label "min"
        ttk.Label(master=self.frm_calculate_timeout, text="min").grid(row=2, column=2, sticky="nw")
        # spinbox per l'input dei secondi del timeout di calcolo per il programma
        self.spn_sec_timeout = ttk.Spinbox( master=self.frm_calculate_timeout,
            from_=0, to=59, wrap=False, format="%02.0f", width=2, 
            textvariable=self.var_sec_timeout,
            validate="key", validatecommand=(self.validate_sec_timeout, "%P") )
        self.spn_sec_timeout.grid(row=2, column=3, sticky="nw")
        #label "sec"
        ttk.Label(master=self.frm_calculate_timeout,
            text="sec").grid(row=2, column=4, sticky="nw")

        # FRAME per input settimana di riferimento per il calcolo
        ttk.Label(master=self.frm_calculate_week, text="Settimana riferimento:").pack(anchor="nw")
        self.var_calculate_week = tk.StringVar()
        self.cal_calculate_week = tkcal.DateEntry( master=self.frm_calculate_week,
            width=10,
            textvariable=self.var_calculate_week,
            locale="it_IT",
            date_pattern="dd/mm/yyyy" )
        self.cal_calculate_week.bind("<<DateEntrySelected>>", self.date_week_selected)
        self.date_week_selected()   # setta subito il lunedì della settimana corrente
        self.cal_calculate_week.pack(anchor="sw")


        # FRAME per l'input di mesi di calcolo
        self.var_calculate_month_num = tk.StringVar( value="1" )
        self.validate_month_num = self.register(self.validate_spinbox_month)
        # label "Timeout calcolo"
        ttk.Label(master=self.frm_calculate_months, text="Mesi da calcolare:").grid(row=1, column=1, columnspan=4, sticky="sw")
        # spinbox per l'input dei minuti del timeout di calcolo per il programma
        self.spn_calculate_month_num = ttk.Spinbox( master=self.frm_calculate_months,
            from_=1, to=(20*12), wrap=False, width=3, 
            textvariable=self.var_calculate_month_num,
            validate="key", validatecommand=(self.validate_month_num, "%P") )
        self.spn_calculate_month_num.grid(row=2, column=1, sticky="ne")
        # label "mesi"
        ttk.Label(master=self.frm_calculate_months, text="mesi").grid(row=2, column=2, sticky="nw")

        # FRAME progressbar e label avanzamento del tempo
        self.progress_bar = ttk.Progressbar(master=self.frm_elapsed_time, orient="horizontal", mode="determinate")
        self.progress_bar.pack(side="top", fill=tk.X)
        ttk.Label( master=self.frm_elapsed_time, text="Tempo trascorso: " ).pack(side="left")
        self.lbl_elapsed_time = ttk.Label(master=self.frm_elapsed_time, text="00:00" )
        self.lbl_elapsed_time.pack(side="left")
        # da chiamare con lo start, mentre con lo stop: "grid_forget"
        #self.frm_elapsed_time.grid(row=3, column=1, columnspan=3, sticky="w", padx=20, pady=10)

    def validate_spinbox_sec(self, u_input):
        if u_input == "":
            return True
        elif ( len(u_input)<=2 ) & ( u_input.isdigit() ):
            return ( int(u_input) in range(0,60) )
        else:
            return False

    def validate_spinbox_min(self, u_input):
        if u_input == "":
            return True
        elif u_input.isdigit():
            return ( int(u_input) in range(0,int(self.spn_min_timeout.config("to")[4])+1) )
        else:
            return False

    def validate_spinbox_month(self, u_input):
        if u_input == "":
            return True
        elif u_input.isdigit():
            return ( int(u_input) in range(1,int(self.spn_calculate_month_num.config("to")[4])+1) )
        else:
            return False
    
    # get value from elements and pops up a dialog on error before start calculating
    def checkGenerateInput(self):
        timeout_min = self.var_min_timeout.get()
        timeout_sec = self.var_sec_timeout.get()
        str_date = self.var_calculate_week.get()
        month_number = self.var_calculate_month_num.get()
        
        if timeout_min == "":
            if ( timeout_sec != "" ) & ( int(timeout_sec)>0 ):
                self.var_min_timeout.set(value="0")
                timeout_min = "0"
            else:
                self.var_min_timeout.set(value="1")
                timeout_min = "1"
        if timeout_sec == "":
            self.var_sec_timeout.set(value="00")
            timeout_sec = "0"

        if ( (int(timeout_min)+int(timeout_sec)) == 0 ):
            return False
        
        try:
            datetime.datetime.strptime(str_date, "%d/%m/%Y")
        except ValueError:
            showerror(title="Data errata", message=f"Attenzione, '{str_date}' non è una data valida.")
            return False
        
        if month_number == "":
            self.var_calculate_month_num.set(value="1")
            month_number = "1"
        
        return True

    def date_week_selected(self, event=None):
        ''' imposta automaticamente la data al lunedì della settimana selezionata '''
        selected_date = datetime.datetime.strptime(self.var_calculate_week.get(), "%d/%m/%Y")
        monday_date = selected_date - datetime.timedelta(days=selected_date.weekday() % 7)
        self.var_calculate_week.set(monday_date.strftime("%d/%m/%Y"))

    def getWeekToCalculate(self):

        input_month = 1
        try:
            input_month = int(self.var_calculate_month_num.get())
        except ValueError:
            pass
        
        selected_date = datetime.datetime.strptime(self.var_calculate_week.get(), "%d/%m/%Y")
        # now get input_month months forward from selected_date, on first day so i can subtract 1 day to get the last day of previous month
        forward_month_date = datetime.datetime(selected_date.year, (selected_date.month + input_month), 1) \
                            if ((selected_date.month + input_month) <= 12) \
                            else datetime.datetime((selected_date.year + 1), ((selected_date.month + input_month) % 12), 1)

        return (forward_month_date - selected_date).days


    # Cronometra il tempo trascorso dallo start
    def cronometer(self):
        [stop_min, stop_sec] = [ int(self.var_min_timeout.get()), int(self.var_sec_timeout.get()) ]
        [min, sec] = [ 0, -1 ]

        while ( ( ( min < stop_min ) | ( ( min == stop_min ) & ( sec < stop_sec ) ) ) & self.__is_generate_running ):
            if ( sec >= 59 ):
                sec = 0
                min += 1
            else:
                sec += 1
            # print in label, a 2 cifre
            [min_str, sec_str] = [ str(min), str(sec) ]
            if( len(min_str) < 2 ):
                min_str = "0" + min_str
            if( len(sec_str) < 2 ):
                sec_str = "0" + sec_str
            self.lbl_elapsed_time.configure( text=( min_str + ":" + sec_str ) )

            # TODO: controllare se il processo genera_turni è effettivamente ancora vivo

            time.sleep(1)
        
        # if this point is reached, the cronometer gone to 0 without external setting of self.__is_generate_running to False, so:
        if self.__is_generate_running:
            self.generate_run(False)
    
    # set the state variable and enable/disable widgets accordingly
    def generate_run(self, is_generate_running):
        self.__is_generate_running = is_generate_running    # this stops the Thread because it reads this value to continue running
        if is_generate_running:
            # disabilita input settaggi parametri
            self.btn_start_calculate.configure( state="disabled" )
            self.spn_min_timeout.configure( state="readonly" )
            self.spn_sec_timeout.configure( state="readonly" )
            self.cal_calculate_week.configure( state="readonly" )
            self.spn_calculate_month_num.configure( state="readonly" )

            self.btn_stop_calculate.configure( state="enabled" )

            # determine seconds per weeks from inputted seconds
            calc_weeks = int(ceil(self.getWeekToCalculate()/7))
            total_seconds = (int(self.var_min_timeout.get())*60) + int(self.var_sec_timeout.get())
            
            seconds_per_week = int(floor(total_seconds / calc_weeks))
            calculate_months = int(self.var_calculate_month_num.get())
            ref_date = self.var_calculate_week.get()  # stringa nel formato "dd/mm/yyyy"

             # DEBUG prints
            print("<AVVIARE PROCESSO QUI>. Parametri:")
            print(f"Secondi tot: {total_seconds}, data rif:{ref_date}, num mesi:{calculate_months}, Effettive week:{calc_weeks}, Secondi per week:{seconds_per_week}")

            ref_date = datetime.datetime.strptime(ref_date, "%d/%m/%Y")

            # start set_day_pointer
            cmd = ['python', 
                   path.join(path.dirname(__file__), 'materiale', 'generatore_turni_ospedale_project', 'set_day_pointer.py'),
                   f"{ref_date.year}", f"{ref_date.month}", f"{ref_date.day}" ]
            process = subprocess.Popen(cmd)
            process.wait()

            # now start calculus
            cmd = ['python', 
                   path.join(path.dirname(__file__), 'materiale', 'generatore_turni_ospedale_project', 'genera_turni_long_term.py'),
                   f"{calculate_months}", f"-o", f"time-limit={seconds_per_week}" ]
            __generate_process = subprocess.Popen(cmd)

           # start progress-bar with its native time-based method
            update_interval = floor( ( ( total_seconds + 1 ) / 99 ) * 1000 )   # msec
            self.progress_bar.start(interval=int(update_interval))
        else:
            # riabilita tutti i settaggi dei parametri
            self.btn_stop_calculate.configure( state="disabled" )

            self.spn_min_timeout.configure( state="enabled" )
            self.spn_sec_timeout.configure( state="enabled" )
            self.cal_calculate_week.configure( state="enabled" )
            self.spn_calculate_month_num.configure( state="enabled" )

            # stop process
            if (__generate_process.poll()!=None):
                __generate_process.terminate()
            

            # stop progress-bar and set it to full
            self.progress_bar.stop()
            self.progress_bar.configure(value=100)

            # delay (1sec) the start button re-enabling to ensure thread is dead
            self.after(1000, lambda: self.btn_start_calculate.configure(state="enabled") )

    def on_window_close(self):
        if self.__is_generate_running:
            # popup
            if (msgbox.askokcancel( title='Generatore turni attivo', icon=msgbox.WARNING, 
                message='Attenzione, la generazione turni è in corso. Fermare?')):
                self.stop_button_pressed()  # this sets __is_generate_running to False (and stops the process)
                self.withdraw() # hide istantly the window, the program will effectively exit with destroy max 1 sec later
                self.cron_thread.join() # this wait for the thread to finish (max 1 sec)
                self.destroy() # this effectively close the window
        else:
            self.destroy()
    
    def start_button_pressed(self, event=None):
        if self.checkGenerateInput():
            import threading
            # mostra le label col tempo trascorso
            self.frm_elapsed_time.grid(row=3, sticky="ew", padx=8, pady=8)
            # avvia il cronometro del tempo trascorso
            self.generate_run(True)
            self.cron_thread = threading.Thread( target=self.cronometer )
            self.cron_thread.start()


    def stop_button_pressed(self, event=None):
        # nascondi le label col tempo trascorso
        self.frm_elapsed_time.grid_forget()
        # ferma il cronometro del tempo trascorso
        self.generate_run(False)

    def ctrl_c_handler(self, event=None):
        if self.__is_generate_running:
            self.stop_button_pressed()

    def preferenze_menu(self, event=None):
        import preferenze
        try:
            preferenze.Preferenze(parent_window=self, input_file_path=i_help.INPUT_PATH, is_generate_running=self.__is_generate_running)
            if not self.__is_generate_running:
                self.close_window()
        except FileNotFoundError as exc:
            showerror(title="Errore", message=str(exc))

    def seniority_menu(self, event=None):
        import seniority
        try:
            # TODO temporary instance here, the idea is to instance when starting GUI
            seniority.Seniority(parent_window=self, inputHelper=i_help.InputHelper(), is_generate_running=self.__is_generate_running)
        except FileNotFoundError as exc:
            showerror(title="Errore", message=str(exc))

    def mansioni_button_pressed(self, event=None):
        import mansioni
        try:
            mansioni.Mansioni(parent_window=self, input_file_path=i_help.INPUT_PATH, is_generate_running=self.__is_generate_running)
            if not self.__is_generate_running:
                self.close_window()
        except FileNotFoundError as exc:
            showerror(title="Errore", message=str(exc))

    def mansionario_button_pressed(self, event=None):
        import mansionario
        try:
            mansionario.Mansionario(parent_window=self, input_file_path=self.__INPUT_PATH, is_generate_running=self.__is_generate_running)
            if not self.__is_generate_running:
                self.close_window()
        except FileNotFoundError as exc:
            showerror(title="Errore", message=str(exc))

    def compatibility_menu(self, event=None):
        import compatibility
        try:
            # TODO temporary instance here, the idea is to instance when starting GUI
            compatibility.Compatibility(parent_window=self, inputHelper=i_help.InputHelper(), is_generate_running=self.__is_generate_running)
            if not self.__is_generate_running:
                self.close_window()
        except FileNotFoundError as exc:
            showerror(title="Errore", message=str(exc))


    def manual_menu(self, event=None):
        self.open_file(path.join(path.dirname(__file__), "manuale.pdf"))
    
    def open_file(self, file_path:str):
        # thanks to Nick: https://stackoverflow.com/a/435669
        import subprocess, os, platform
        if platform.system() == 'Darwin':       # macOS
            subprocess.call(('open', file_path))
        elif platform.system() == 'Windows':    # Windows
            os.startfile(file_path)
        else:                                   # linux variants
            subprocess.call(('xdg-open', file_path))

     

def center_window(window:tk.Tk):
    '''  (https://stackoverflow.com/a/10018670)
    centers a tkinter window
    :param window: the main window or Toplevel window to center
    '''
    window.update_idletasks()
    width = window.winfo_width()
    frm_width = window.winfo_rootx() - window.winfo_x()
    win_width = width + 2 * frm_width
    height = window.winfo_height()
    titlebar_height = window.winfo_rooty() - window.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = window.winfo_screenwidth() // 2 - win_width // 2
    y = window.winfo_screenheight() // 2 - win_height // 2
    # this fix window size (have to manual change size if add new element dinamically), i don't want that
    # window.geometry(f"{width}x{height}+{x}+{y}")
    window.geometry(f"+{x}+{y}")
    window.deiconify()


if __name__ == "__main__":
    application = GUI()
    center_window(application)
    application.deiconify()
    application.mainloop()
