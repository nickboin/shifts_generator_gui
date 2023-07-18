import os.path as path
import json

# COSTANT: referring input file, while memorizing days:
#   if 0 --> [0=monday, 1=tuesday, 2=wednesday ...]
#   if 1 --> [1=monday, 2=tuesday, 3=wednesday ...]
DAY_OFFSET = 1

INPUT_PATH = path.join(path.dirname(__file__), "input", "input.json")

class InputHelper():

    __JSON_INPUT_FILE_PATH:str

    # working dictionary, imported from the input.json
    __input:dict
    # to correctly recognize seniority
    __seniority_operators_labels:list
    __sanitized_seniority_operators_labels:list
    
    # dictionaries with sanitized input, for the "job_description" key
    __input_jobs_sanitized:dict
    # sanitized seniorty operators list, retrieved from __input
    __seniority_operators_sanitized:dict


    def __init__(self, json_file_path=None):
        # reading the input file
        if (json_file_path != None):
            self.__JSON_INPUT_FILE_PATH = json_file_path
        else:
            self.__JSON_INPUT_FILE_PATH = INPUT_PATH
        self.__input = self.__load_json_input()

        # list of seniority labels to consider as seniority
        self.__seniority_operators_labels = ["chief_medical_officier", "senior_physician", "mfs"]
        self.__sanitized_seniority_operators_labels = [ "Primario", "Senior", "M.F.S." ]
        # MFS = Medical Former Specializand, but using MFS it's ok

        # creating the human readable dict
        self.__build_sanitized_dictionary()


    def __load_json_input(self):
        if path.isfile(self.__JSON_INPUT_FILE_PATH):
            with open(self.__JSON_INPUT_FILE_PATH) as json_input_file:
                return json.load(json_input_file)
        else:
            print("Input non trovati!")
            # TODO gestione errore migliore
        # TODO check structure integrity after loading!

    def __save_json_input(self):
        if not path.isfile(self.__JSON_INPUT_FILE_PATH):
            print(f"'{self.__JSON_INPUT_FILE_PATH}' non trovato, verrà creato nuovo.")
        with open(self.__JSON_INPUT_FILE_PATH, 'w') as json_input_file:
            json.dump(self.__input, json_input_file, indent=4)
        return True

    def reload_from_file(self):
        self.__input = self.__load_json_input()
        self.__build_sanitized_dictionary()
    

    def get_jobs_dict(self):
        return self.__input["job_description"]
    

    def get_job_dict(self, job_key):
        return self.__input["job_description"][job_key]


    def __build_sanitized_dictionary(self):
        self.__input_jobs_sanitized = dict()    # initialization, required on rebuild
        for job_key in self.get_jobs_dict():

            # sanitize dict element to work with, before saving it
            sanitized_element = dict()

            [location, job_name] = job_key.split(",", 1)
            # add a new field for job name, considering the difference on sanitization if has an associated multiple operator task or if it is a multiple operator task
            if(self.isMultipleOperatorTask(job_key)):
                sanitized_element.update({"job_name":self.sanitize_mo_task_other(job_name)})
            elif(self.hasMultipleOperatorTask(job_key)):
                sanitized_element.update({"job_name":self.sanitize_mo_task_primary(job_name)})
            else:
                sanitized_element.update({"job_name":self.sanitize_string(job_name)})
            # add a new field for job location
            sanitized_element.update({"job_location":self.sanitize_string(location)})

            # now cycle through all attributes to sanitize (and preserve unrecognized attributes)
            for job_attribute in self.get_job_dict(job_key):
                if job_attribute == "cathegory":
                    sanitized_category = self.sanitize_string(self.get_job_dict(job_key)["cathegory"])
                    sanitized_element.update({"cathegory":sanitized_category})
                elif job_attribute == "operating_day":
                    sanitized_days = self.sanitize_days(set(self.get_job_dict(job_key)["operating_day"]))
                    sanitized_element.update({"operating_day":sanitized_days})
                elif job_attribute == "operating_time":
                    sanitized_time = self.sanitize_time(self.get_job_dict(job_key)["operating_time"])
                    sanitized_element.update({"operating_time":sanitized_time})
                elif job_attribute == "qualified_physician":
                    sanitized_operator_list = list()
                    operator_list = self.get_job_dict(job_key)["qualified_physician"]
                    sanitized_operator_list = self.sanitize_operators_list(operator_list)
                    sanitized_element.update({"qualified_physician":sanitized_operator_list})
                elif job_attribute == "preference":
                    sanitized_preferences = list()
                    job_preferences = self.get_job_dict(job_key)["preference"]  # it's a list of dict
                    for preference in job_preferences:
                        # again, exploring fields and sanitize only needed, copy others
                        pref_dict = dict()
                        for pref_attrib in preference.keys():
                            sanitized_operators_prefs = list()
                            if pref_attrib == "physician":
                                sanitized_operators_prefs = self.sanitize_operators_list(preference["physician"])
                                pref_dict.update( { "physician":sanitized_operators_prefs } )
                            elif pref_attrib == "day":
                                sanitized_day_pref = self.sanitize_days( set(preference["day"]) )
                                pref_dict.update( { "day":sanitized_day_pref } )
                            else:
                                pref_dict.update( { pref_attrib:preference[pref_attrib] } )
                        sanitized_preferences.append(pref_dict)
                    sanitized_element.update({"preference":sanitized_preferences})
                elif job_attribute == "extra_compatibility":
                    sanitized_extra_comp = dict()
                    for e_c in self.get_job_dict(job_key)["extra_compatibility"]:
                        sanitized_extra_comp.update( { e_c:self.sanitize_days(self.get_job_dict(job_key)["extra_compatibility"][e_c]) } )
                    sanitized_element.update({"extra_compatibility":sanitized_extra_comp})
                else:   # every unknown attribute get copied without modifications
                    sanitized_element.update({job_attribute:self.get_job_dict(job_key)[job_attribute]})
            # finally add the built dict element to the main sanitized dictionary
            self.__input_jobs_sanitized.update({job_key:sanitized_element})
            
            self.__seniority_operators_sanitized = dict()
            for seniority in self.__seniority_operators_labels:
                self.__seniority_operators_sanitized.update( { seniority:self.sanitize_operators_list(self.__input[seniority]) } )
            
    # SANITIZATION methods

    def sanitize_string(self, stringa:str):
        stringa = stringa.replace("_", " ")
        return stringa.title()
    
    def de_sanitize_string(self, stringa:str):
        stringa = stringa.replace(" ", "_")
        return stringa.lower()
    
    def sanitize_string_list(self, de_sanitized_list):
        sanitized_list = list()
        for de_sanitized_string in de_sanitized_list:
            sanitized_list.append(self.sanitize_string(de_sanitized_string))
        return sanitized_list
    
    def de_sanitize_string_list(self, sanitized_list):
        de_sanitized_list = list()
        for sanitized_string in sanitized_list:
            de_sanitized_list.append(self.de_sanitize_string(sanitized_string))
        return de_sanitized_list
    
    # The operators sanitization is a particular case because we have to keep the eventual uppercase char inside words
    
    def sanitize_operator(self, operator:str):
        sanitized_operator = ""
        for word in operator.split("_"):
            sanitized_operator += (word[0:1].upper() + word[1:] + "_")
        return sanitized_operator[0:-1]
    
    def de_sanitize_operator(self, sanitized_operator:str):
        de_sanitized_operator = ""
        for word in sanitized_operator.split(" "):
            de_sanitized_operator += (word[0:1].lower() + word[1:] + "_")
        return de_sanitized_operator[0:-1]
    
    def sanitize_operators_list(self, operator_list):
        sanitized_list = list()
        for operator in operator_list:
            sanitized_list.append(self.sanitize_operator(operator))
        return sanitized_list
    
    def de_sanitize_operators_list(self, sanitized_operator_list):
        de_sanitized_list = list()
        for operator in sanitized_operator_list:
            de_sanitized_list.append(self.de_sanitize_operator(operator))
        return de_sanitized_list
        
    def sanitize_days(self, days_set:set):
        days_set = list(days_set)
        days_set.sort()
        if ( len(days_set) == 7 ):
            return "Tutti i giorni"
        elif ( days_set == [(DAY_OFFSET),(DAY_OFFSET+1),(DAY_OFFSET+2),(DAY_OFFSET+3),(DAY_OFFSET+4)] ):
            return "da Lunedì a Venerdì"
        else:
            # show long labels if there are up to 2 days to show
            if len(days_set) >= 3:
                days_labels = ("Lun, ", "Mar, ", "Mer, ", "Gio, ", "Ven, ", "Sab, ", "Dom, ")
            else:
                days_labels = ("Lunedì, ", "Martedì, ", "Mercoledì, ", "Giovedì, ", "Venerdì, ", "Sabato, ", "Domenica, ")
            for i in range(DAY_OFFSET):     # add initial empty values to correct day_offest
                days_labels = ("",) + days_labels
            sanitized_days_string = ""
            for day in days_set:
                sanitized_days_string += days_labels[day]
            return sanitized_days_string[0:-2]  # remove the 2 final char ", "
        
    def sanitize_time(self, time_tuple):
        if len(time_tuple) == 2:
            return ( "dalle " + str(time_tuple[0]) + ":00 alle " + str(time_tuple[1]) + ":00" )
        else:   # TODO raise format error
            return time_tuple
    
    def sanitize_seniority_key(self, seniority_label:str):
        ''' get the human readable version of the specified seniority key; raise ValueError if not exists '''
        return self.__sanitized_seniority_operators_labels[self.__seniority_operators_labels.index(seniority_label)]
    
    def de_sanitize_seniority_label(self, sanitized_seniority_label:str):
        ''' get the key saved on file version of the specified sanitized seniority key; raise ValueError if not exists '''
        return self.__seniority_operators_labels[self.__sanitized_seniority_operators_labels.index(sanitized_seniority_label)]
    
    def sanitize_mo_task_primary(self, job_name_primary):
        '''
            job_name should ends with "1)"
            case 1) name_(index,1)
            case 2) name_(1)
        '''
        last_part = job_name_primary[-3:]
        first_part = job_name_primary[0:-3]
        if last_part == ",1)":
            return self.sanitize_string( ( first_part + "): Principale" ) )
        elif last_part == "(1)":
            if (first_part[-1:] == "_"):
                first_part = first_part[0:-1]
            return self.sanitize_string( ( first_part + ": Principale" ) )
        else:
            return self.sanitize_string( job_name_primary )
    
    def de_sanitize_mo_task_primary(self, sanitized_job_name_primary):
        '''
            sanitized_job_name_primary should ends with ": Principale"
        '''
        last_part = str(sanitized_job_name_primary[-12:]).lower()
        first_part = sanitized_job_name_primary[0:-12]
        if last_part == ": principale":
            return self.sanitize_string( ( first_part + "(1)" ) )
        else:
            return self.sanitize_string( sanitized_job_name_primary )
    
    def sanitize_mo_task_other(self, job_name_other):
        '''
            job_name should ends with "other)"
            case 1) name_(index,other)
            case 2) name_(other)
        '''
        last_part = job_name_other[-7:]
        first_part = job_name_other[0:-7]
        if (last_part == ",other)"):
            return self.sanitize_string( ( first_part + "): Multioperatore" ) )
        elif (last_part == "(other)"):
            if (first_part[-1:] == "_"):
                first_part = first_part[0:-1]
            return self.sanitize_string( ( first_part + ": Multioperatore" ) )
        else:
            return self.sanitize_string( job_name_other )

    def de_sanitize_mo_task_other(self, sanitized_job_name_other):
        '''
            job_name should ends with ": Multioperatore"
        '''
        last_part = str(sanitized_job_name_other[-12:]).lower()
        first_part = sanitized_job_name_other[0:-12]
        if (last_part == ": multioperatore"):
            return self.sanitize_string( ( first_part + "(other)" ) )
        else:
            return self.sanitize_string( sanitized_job_name_other )


    '''
     transform the key, that ends with "..,1)" or "(1)" to the corresponding 
     that ends with "..,other)" or "(other)" to match the corresponding multiple_operator_task key
    ----- WATCH OUT: the key returned MAY NOT EXIST -----
     This only transform the key following the given pattern to make multiple operator task key
    '''
    def fromPrimaryJob_toOther(self, primary_job_key):
        ''' Transformation recap:
        name(index,1) --> name(index,other)
              name(1) -->       name(other)
        '''
        # so, respecting the patter, the transformation has to be done on the last 2 characters
        first_part = primary_job_key[0:-2]
        #last_part = primary_job_key[-2:]    # the last part should be "1)"
        return first_part + "other)"
    
    '''
     transform the key, that ends with "..,other)" or "(other)" to the corresponding 
     that ends with "..,1)" or "(1)" to match the multiple_operator_task key
    ----- WATCH OUT: the key returned MAY NOT EXIST -----
     This only transform the key following the given pattern from the multiple operator task key
    '''
    def fromOtherJob_toPrimary(self, other_job_key):
        ''' Transformation recap:
        name(index,other) --> name(index,1)
              name(other) -->       name(1)
        '''
        # so, respecting the patter, the transformation has to be done on the last 6 characters
        first_part = other_job_key[0:-6]
        #last_part = other_job_key[-6:]    # the last part should be "other)"
        return first_part + "1)"
        
    def min(self, lista):
        curmin = lista[0]
        for x in lista:
            if isinstance(x, int):
                if x < curmin:
                    curmin = x
            else:
                raise TypeError("List element '"+str(x)+"' is not an integer!")
        return curmin
    
    def max(self, lista):
        curmax = lista[0]
        for x in lista:
            if isinstance(x, int):
                if x > curmax:
                    curmax = x
            else:
                raise TypeError("List element '"+str(x)+"' is not an integer!")
        return curmax
    
    ## GETTER

    def existsJobKey(self, job_key):
        return ( job_key in self.get_jobs_dict() )
    
    def getJobCount(self):
        return len(self.get_jobs_dict().keys())

    # Getter: lists output

    def getJobKeyList(self):
        return list(self.get_jobs_dict().keys())
    
    def getJobLocationList(self):
        location_list = list()
        for key in self.get_jobs_dict():
            location_list.append(key.split(",",1)[0])
        return location_list
    
    def getJobNameList(self):
        names_list = list()
        for key in self.get_jobs_dict():
            names_list.append(key.split(",",1)[1])
        return names_list
    
    def getJobCategoryList(self):
        categories_list = list()
        for key in self.get_jobs_dict():
            categories_list.append(self.get_job_dict(key)["cathegory"])
        return categories_list
    
    def getJobDaysList(self):
        days_list = list()
        for key in self.get_jobs_dict():
            days_list.append(self.get_job_dict(key)["operating_day"])
        return days_list
    
    def getJobTimeList(self):
        time_list = list()
        for key in self.get_jobs_dict():
            time_list.append(self.get_job_dict(key)["operating_time"])
        return time_list
    
    def getMultipleOperatorTaskList(self):
        return list(self.__input["multiple_operator_task"])
    
    # Getter: sanitized lists output

    def getSanitizedJobList(self):
        ''' return the sanitized jobs list, with sanitized original names '''
        job_list = list()
        for key in self.__input_jobs_sanitized:
            [location, name] = self.sanitize_string(key.split(",",1))
            job_list.append((location + ": " + name))
        return job_list

    def getFullSanitizedJobList(self):
        ''' return the sanitized jobs list, with full sanitized names '''
        job_list = list()
        for key in self.__input_jobs_sanitized:
            name = self.__input_jobs_sanitized[key].get("job_name")
            location = self.getSanitizedJobLocation(key)
            job_list.append((location + ": " + name))
        return job_list
    
    def getSanitizedJobNameList(self):
        names_list = list()
        for key in self.__input_jobs_sanitized:
            name = self.sanitize_string(key.split(",",1)[1])
            names_list.append(name)
        return names_list
    
    def getFullSanitizedJobNameList(self):
        names_list = list()
        for key in self.__input_jobs_sanitized:
            names_list.append(self.__input_jobs_sanitized[key]["job_name"])
        return names_list
    
    def getSanitizedJobLocationList(self):
        location_list = list()
        for key in self.__input_jobs_sanitized:
            location_list.append(self.__input_jobs_sanitized[key]["job_location"])
        return location_list
    
    def getSanitizedJobCategoriesList(self):
        categories_list = list()
        for key in self.__input_jobs_sanitized:
            categories_list.append(self.__input_jobs_sanitized[key]["cathegory"])
        return categories_list
    
    def getSanitizedJobDayList(self):
        days_list = list()
        for key in self.__input_jobs_sanitized:
            days_list.append(self.__input_jobs_sanitized[key]["operating_day"])
        return days_list
    
    def getSanitizedJobTimeList(self):
        time_list = list()
        for key in self.__input_jobs_sanitized:
            time_list.append(self.__input_jobs_sanitized[key]["operating_time"])
        return time_list

    # Getter: single field output

    def getJobKeyIndex_byKey(self, job_jey):
        if ( self.existsJobKey(job_jey)):
            return list(self.get_jobs_dict().keys()).index(job_jey)
        else:
            return ""
            # TODO raise error

    def getJobKey_byIndex(self, index):
        if ( index>=0 & index<self.getJobCount()):
            return list(self.get_jobs_dict().keys())[index]
        else:
            return ""
            # TODO raise error

    def getJobName(self, job_key):
        if job_key in self.get_jobs_dict():
            return job_key.split(",", 1)[1]
        else:
            return ""
            # TODO raise error

    def getJobLocation(self, job_key):

        if job_key in self.get_jobs_dict():
            return job_key.split(",", 1)[0]
        else:
            return ""
            # TODO raise error
    
    def getJobCategory(self, job_key):
        if job_key in self.get_jobs_dict():
            return self.get_job_dict(job_key).get("cathegory")
        else:
            return ""
            # TODO raise error
        
    
    def getJobDays(self, job_key):
        if job_key in self.get_jobs_dict():
            return list(self.get_job_dict(job_key).get("operating_day"))
        else:
            return ""
            # TODO raise error
    
    def getJobTime(self, job_key):
        if job_key in self.get_jobs_dict():
            return tuple(self.get_job_dict(job_key).get("operating_time"))
        else:
            return ""
            # TODO raise error
    
    def getJobOperatorsList(self, job_key):
        if job_key in self.get_jobs_dict():
            return list(self.get_job_dict(job_key).get("qualified_physician"))
        else:
            return ""
            # TODO raise error

    # return True if it's in "multiple_operator_task"
    def isMultipleOperatorTask(self, job_key):
        return ( job_key in self.__input["multiple_operator_task"] )
    
    # return True if it's the primary job of a multiple operator task
    def hasMultipleOperatorTask(self, job_key):
        return self.isMultipleOperatorTask(self.fromPrimaryJob_toOther(job_key))

    # Getter: sanitized field output

    def getSanitizedJobName(self, job_key):
        ''' return the job location & name in format "Name"(only letters capitalizations) '''
        if job_key in self.__input_jobs_sanitized.keys():
            return self.sanitize_string(job_key.split(",",1)[1])
        else:
            return ""
            # TODO raise error

    def getFullSanitizedJobName(self, job_key):
        ''' return the job location & name in format "Name"(multi-operator names sanitization) '''
        if job_key in self.__input_jobs_sanitized.keys():
            return self.__input_jobs_sanitized[job_key]["job_name"]
        else:
            return ""
            # TODO raise error

    def getFullSanitizedJob(self, job_key):
        ''' return the job location & name in format "Location: Name"(multi-operator names sanitization) '''
        if job_key in self.__input_jobs_sanitized.keys():
            return ( self.getSanitizedJobLocation(job_key) + ": " + self.__input_jobs_sanitized[job_key]["job_name"])
        else:
            return ""
            # TODO raise error

    def getSanitizedJobLocation(self, job_key):
        if job_key in self.__input_jobs_sanitized.keys():
            return self.__input_jobs_sanitized[job_key]["job_location"]
        else:
            return ""
            # TODO raise error
    
    def getSanitizedJobCategory(self, job_key):
        if job_key in self.__input_jobs_sanitized.keys():
            return self.__input_jobs_sanitized[job_key].get("cathegory")
        else:
            return ""
            # TODO raise error
        
    
    def getSanitizedJobDays(self, job_key):
        if job_key in self.__input_jobs_sanitized.keys():
            return self.__input_jobs_sanitized[job_key].get("operating_day")
        else:
            return ""
            # TODO raise error
    
    def getSanitizedJobTime(self, job_key):
        if job_key in self.__input_jobs_sanitized.keys():
            return self.__input_jobs_sanitized[job_key].get("operating_time")
        else:
            return ""
            # TODO raise error
    
    def getSanitizedJobOperatorsList(self, job_key):
        if job_key in self.__input_jobs_sanitized.keys():
            return list(self.__input_jobs_sanitized[job_key].get("qualified_physician"))
        else:
            return ""
            # TODO raise error

    # Getter: Compatibility

    def __getJobCompatibilityList(self, job_key:str, wants_sanitized_output:bool=False):
        ''' return a list of dict, which keys are { "job_key", "job_name"(for sanitized output), "days"(if present) }, with job_key compatibilities '''
        compatibilities = list()
        compatibilities_keys = list()   # keep track of keys to not make duplicates
        if(self.existsJobKey(job_key)):
            # compatibilities for specified days
            if ("extra_compatibility" in self.get_job_dict(job_key)):
                for comp_job in self.get_job_dict(job_key)["extra_compatibility"].keys():
                    days = self.get_job_dict(job_key)["extra_compatibility"][comp_job]
                    if wants_sanitized_output:
                        compatibilities.append( 
                            { "job_key": str(comp_job), 
                              "job_name": self.getFullSanitizedJob(comp_job), 
                              "days": self.sanitize_days(days) } 
                        )
                    else:
                        compatibilities.append( { "job_key":str(comp_job), "days":days } )
                    compatibilities_keys.append(str(comp_job))
            # regular compatibilities
            if ("compatibility" in self.get_job_dict(job_key)):
                for comp_job in self.get_job_dict(job_key)["compatibility"]:
                    if (not comp_job in compatibilities_keys):  # to not make duplicates
                        if wants_sanitized_output:
                            compatibilities.append( 
                                { "job_key": str(comp_job), 
                                  "job_name": self.getFullSanitizedJob(comp_job) }
                            )
                        else:
                            compatibilities.append( { "job_key":str(comp_job) } )
                        compatibilities_keys.append(str(comp_job))

            # work here is not finished; we have to reverse check
            for revchk_job_key in self.getJobKeyList():
                if (revchk_job_key == job_key):
                    pass    # current job
                else:
                    # compatibilities for specified days
                    if ("extra_compatibility" in self.get_job_dict(revchk_job_key)):
                        if job_key in self.get_job_dict(revchk_job_key)["extra_compatibility"].keys():
                            # found a compatibility in reverse check
                            if (revchk_job_key in compatibilities_keys):
                                # uh oh, the compatibility is already in list; 2 things can happen now:
                                # - i can overwrite with the last one
                                # - i can keep the previous one, which was specified in that job (the chosen way)
                                # The logic of the program SHOULD NOT make the presence of duplicates in reverse check
                                # or if they exist, they are specularly the same (no different comp_days)
                                pass
                            else:
                                days = self.get_job_dict(revchk_job_key)["extra_compatibility"][job_key]
                                if wants_sanitized_output:
                                    compatibilities.append( 
                                        { "job_key": str(revchk_job_key), 
                                          "job_name": self.getFullSanitizedJob(revchk_job_key), 
                                          "days": self.sanitize_days(days) } 
                                    )
                                else:
                                    compatibilities.append( { "job_key":str(revchk_job_key), "days":days } )
                                compatibilities_keys.append(str(revchk_job_key))
                    # regular compatibilities
                    if ("compatibility" in self.get_job_dict(revchk_job_key)):
                        if job_key in self.get_job_dict(revchk_job_key)["compatibility"]:
                            if (revchk_job_key in compatibilities_keys):
                                # uh oh, the compatibility is already in list;
                                # see the comment written like 15 lines before
                                pass
                            else:
                                if wants_sanitized_output:
                                    compatibilities.append( 
                                        { "job_key": str(revchk_job_key), 
                                          "job_name": self.getFullSanitizedJob(revchk_job_key) }
                                    )
                                else:
                                    compatibilities.append( { "job_key":str(revchk_job_key) } )
                                compatibilities_keys.append(str(revchk_job_key))
            # compatibilities list ready
            return compatibilities
        else:
            raise ValueError(f"Error: job_key '{job_key}' not found!")
        
    def getJobCompatibilityList(self, job_key:str):
        ''' return a list of dict, which keys are { "job_key", "days"(if present) }, with job_key compatibilities '''
        return self.__getJobCompatibilityList(job_key=job_key, wants_sanitized_output=False)
        
    def getSanitizedJobCompatibilityList(self, job_key:str):
        ''' 
        return a list of dict, which keys are { "job_key", "job_name"(sanitized), "days"(if present, sanitized) }, 
        with job_key sanitized compatibilities 
        '''
        return self.__getJobCompatibilityList(job_key=job_key, wants_sanitized_output=True)
    
    def areJobsCompatible(self, job_key_1:str, job_key_2:str):
        if (self.existsJobKey(job_key_1) & self.existsJobKey(job_key_2)):
            if ("compatibility" in self.get_job_dict(job_key_1)):
                if (job_key_2 in self.get_job_dict(job_key_1)["compatibility"]):
                    return True
            if ("extra_compatibility" in self.get_job_dict(job_key_1)):
                if (job_key_2 in self.get_job_dict(job_key_1)["extra_compatibility"].keys()):
                    return True
            # if not found, try reverse checking
            if ("compatibility" in self.get_job_dict(job_key_2)):
                if (job_key_1 in self.get_job_dict(job_key_2)["compatibility"]):
                    return True
            if ("extra_compatibility" in self.get_job_dict(job_key_2)):
                if (job_key_1 in self.get_job_dict(job_key_2)["extra_compatibility"].keys()):
                    return True
            return False
        else:
            raise ValueError("Error! job_key '{job_key_1}' or '{job_key_2}' not found!")
    
    def haveJobCompatibleDays(self, job_key_1:str, job_key_2:str):
        ''' if job_key_1 and job_key_2 are compatible, return True if they have compatible days set, false if simply compatible without days or not compatible '''
        if (self.existsJobKey(job_key_1) & self.existsJobKey(job_key_2)):
            if ("extra_compatibility" in self.get_job_dict(job_key_1)):
                if (job_key_2 in self.get_job_dict(job_key_1)["extra_compatibility"].keys()):
                    return bool(len(self.get_job_dict(job_key_1)["extra_compatibility"][job_key_2]))
            # if not found, try reverse checking
            if ("extra_compatibility" in self.get_job_dict(job_key_2)):
                if (job_key_1 in self.get_job_dict(job_key_2)["extra_compatibility"].keys()):
                    return bool(len(self.get_job_dict(job_key_2)["extra_compatibility"][job_key_1]))
            return False
        else:
            raise ValueError("Error! job_key '{job_key_1}' or '{job_key_2}' not found!")
    
    def getJobCompatibleDays(self, job_key_1:str, job_key_2:str):
        ''' if job_key_1 and job_key_2 are compatible, get compatibility day list; if none, return empty list '''
        if (self.existsJobKey(job_key_1) & self.existsJobKey(job_key_2)):
            if ("extra_compatibility" in self.get_job_dict(job_key_1)):
                if (job_key_2 in self.get_job_dict(job_key_1)["extra_compatibility"].keys()):
                    return self.get_job_dict(job_key_1)["extra_compatibility"][job_key_2]
            # if not found, try reverse checking
            if ("extra_compatibility" in self.get_job_dict(job_key_2)):
                if (job_key_1 in self.get_job_dict(job_key_2)["extra_compatibility"].keys()):
                    return self.get_job_dict(job_key_2)["extra_compatibility"][job_key_1]
            return list()
        else:
            raise ValueError("Error! job_key '{job_key_1}' or '{job_key_2}' not found!")
        
    def getSanitizedJobCompatibleDays(self, job_key_1:str, job_key_2:str):
        return self.sanitize_days(self.getJobCompatibleDays())
    
    # Getter: operators list
    
    def getOperatorSet(self):
        operators_list = set()
        for key in self.get_jobs_dict():
            operators_list.update(set(self.get_job_dict(key)["qualified_physician"]))
        return operators_list
    
    def getSanitizedOperatorSet(self):
        sanitized_operators_list = set()
        for key in self.__input_jobs_sanitized:
            sanitized_operators_list.update(set(self.__input_jobs_sanitized[key]["qualified_physician"]))
        return sanitized_operators_list

    def getSanitizedOperator(self, operator):
        if operator in self.getOperatorSet():
            return self.sanitize_operator(operator)
        else:
            return ""
            # TODO raise error

    def existsOperator(self, operator, sanitized_operator:bool=False):
        ''' set sanitized_operator=True if the operator parameter is sanitized '''
        if sanitized_operator:
            return ( operator in self.getSanitizedOperatorSet() )
        else:
            return ( operator in self.getOperatorSet() )
    
    def hasOperator(self, job_key, operator, sanitized_operator:bool=False):
        ''' 
        check if job_key has operator in its qualified_physician 
        set sanitized_operator=True if the operator parameter is sanitized 
        '''
        if self.existsJobKey(job_key):
            if sanitized_operator:
                return ( operator in self.__input_jobs_sanitized[job_key]["qualified_physician"] )
            else:
                return ( operator in self.get_job_dict(job_key)["qualified_physician"] )
        else:
            raise ValueError(f"job_key '{job_key}' not found!")
        
    # GETTER: seniority

    def getSeniorityKeys(self):
        return self.__seniority_operators_labels

    def getSanitizedSeniorityLabels(self):
        return self.__sanitized_seniority_operators_labels

    def getSeniorityDict(self):
        seniority_dict = dict()
        for key in self.__seniority_operators_labels:
            if (key in self.__input):
                seniority_dict.update( {key:self.__input[key]} )
            else:
                seniority_dict.update( {key:list()} )
        return seniority_dict
    
    def getSanitizedSeniorityDict(self):
        return self.__seniority_operators_sanitized
    
    def getSeniorityList(self, seniority_label:str, is_seniority_label_sanitized:bool=False):
        if is_seniority_label_sanitized:
            seniority_label = self.de_sanitize_seniority_label(seniority_label)
        if (seniority_label in self.__input):
            return self.__input[seniority_label]
        else:
            return list()
    
    def getSeniorityList_CMO(self):
        return self.getSeniorityList("chief_medical_officier")
    
    def getSeniorityList_SP(self):
        return self.getSeniorityList("senior_physician")
    
    def getSeniorityList_MFS(self):
        return self.getSeniorityList("mfs")
        
    def getSanitizedSeniorityList(self, seniority_label:str, is_seniority_label_sanitized:bool=False):
        if is_seniority_label_sanitized:
            seniority_label = self.de_sanitize_seniority_label(seniority_label)
        if (seniority_label in self.__seniority_operators_sanitized):
            return self.__seniority_operators_sanitized[seniority_label]
        else:
            return list()
    
    def getSanitizedSeniorityList_CMO(self):
        return self.getSanitizedSeniorityList("chief_medical_officier")
    
    def getSanitizedSeniorityList_SP(self):
        return self.getSanitizedSeniorityList("senior_physician")
    
    def getSanitizedSeniorityList_MFS(self):
        return self.getSanitizedSeniorityList("mfs")
        
    # TODO return a list, not a single match!
    def getOperatorSeniority(self, operator:str, sanitized_operator:bool=False):
        ''' return the seniority label (key) of the specified operator, empyty string if not in list '''
        for s_label in self.__seniority_operators_labels:
            if ((sanitized_operator) & (operator in self.__seniority_operators_sanitized[s_label])):
                return s_label
            elif ((not sanitized_operator) & (operator in self.__input[s_label])):
                return s_label
        else:
            return ""
    
    def getSanitizedOperatorSeniority(self, operator:str, sanitized_operator:bool=False):
        ''' return the seniority label (human readable) of the specified operator, empyty string if not in list '''
        s_label = self.getOperatorSeniority(operator, sanitized_operator)
        return (s_label if (s_label == "") else self.__sanitized_seniority_operators_labels[self.__seniority_operators_labels.index(s_label)])
    
    def isSeniorityOperator(self, operator:str, seniority_label:str, is_operator_sanitized:bool=False, is_seniority_label_sanitized:bool=False):
        ''' check if the specified operator is in the specified seniority list; if the specified seniority_label isn't found, raise ValueError '''
        if (is_seniority_label_sanitized):
            if (is_operator_sanitized):
                return (operator in self.__seniority_operators_sanitized[self.de_sanitize_seniority_label(seniority_label)])
            else:
                return (operator in self.__input[self.de_sanitize_seniority_label(seniority_label)])
        else:
            if (seniority_label in self.__seniority_operators_labels):
                if (is_operator_sanitized):
                    return (operator in self.__seniority_operators_sanitized[seniority_label])
                else:
                    return (operator in self.__input[seniority_label])
            else:
                raise ValueError(f"Error: seniority label key '{seniority_label}' not found!")
        
    # GETTER: preferences

    def hasJobOperatorPreference(self, job_key, operator, sanitized_operator:bool=False):
        ''' check if in job_key the operator has a preference set '''
        if self.hasOperator(job_key, operator, sanitized_operator=sanitized_operator):
            curr_job_dict = self.__input_jobs_sanitized[job_key] if sanitized_operator else self.get_job_dict(job_key)
            if "preference" in curr_job_dict:
                for preference_dict in curr_job_dict["preference"]:
                    if operator in preference_dict["physician"]:
                        return True
        return False

    def getJobOperatorPreference(self, job_key, operator, sanitized_operator:bool=False):
        ''' 
        return a dict {"preference":bool, "penality":int, "day":list(int)} with preferences of specified operator;
        if it haven't preferences, return {"preference":False, "penality":0, "day":[]}. 
        Anyway always return a dict with those 3 keys.
        '''
        if self.hasOperator(job_key, operator, sanitized_operator=sanitized_operator):
            operator_preferences = { "preference":False, "penality":0, "day":list() }      #default
            #if self.hasJobOperatorPreference(job_key, operator, sanitized_operator=sanitized_operator): # not needed, i have to check the list anyway
            if sanitized_operator:
                operator = self.de_sanitize_operator(operator)
            
            if "preference" in self.get_job_dict(job_key):
                for preference_dict in self.get_job_dict(job_key)["preference"]:
                    if operator in preference_dict["physician"]:
                        operator_preferences["preference"] = True
                        if ("penality" in preference_dict):     # teorically this must always be
                            operator_preferences["penality"] = preference_dict["penality"]
                        if ("day" in preference_dict):
                            operator_preferences["day"] = preference_dict["day"]
            return operator_preferences
        else:
            raise ValueError(f"'{operator}' not found in '{job_key}'!")

    def getSanitizedJobOperatorPreference(self, job_key, operator, sanitized_operator:bool=False):
        ''' 
        return a LIST of strings (responding format [preference, penality, days]) ["Sì"/"No", "int", "elenco_giorni"] 
        with sanitized preferences of specified operator, ready to put in a table row; 
        if it haven't preferences, return ["No", "", ""] 
        '''
        if self.hasOperator(job_key, operator, sanitized_operator=sanitized_operator):
            operator_preferences = [ "No", "", "" ]     #default
            #if self.hasJobOperatorPreference(job_key, operator, sanitized_operator=sanitized_operator): # not needed, i have to check the list anyway
            if not sanitized_operator:
                operator = self.sanitize_operator(operator)
            
            if "preference" in self.__input_jobs_sanitized[job_key]:
                for preference_dict in self.__input_jobs_sanitized[job_key]["preference"]:
                    if operator in preference_dict["physician"]:
                        operator_preferences[0] = "Sì"
                        if ("penality" in preference_dict):     # teorically this must always be
                            operator_preferences[1] = str(preference_dict["penality"])
                        if ("day" in preference_dict):
                            operator_preferences[2] = preference_dict["day"]
            return operator_preferences
        else:
            raise ValueError(f"'{operator}' not found in '{job_key}'!")
        
    def getJobOperatorPreferenceList(self, job_key):
        '''
        get the preference list that have been set in job_key;
        return a list of dict, element keys are: {"physician", "penality", "day"}
        '''
        # WATCH OUT, in case of duplicate operator in job_key preferences, only the last read will be reported;
        # this is because duplicate preferences for the same operator should not exist!
        if self.existsJobKey(job_key):
            if "preference" in self.get_job_dict(job_key):
                operators_preference = list()       # list of dictionary with operator and relative preference attributes
                for preference_dict in self.get_job_dict(job_key)["preference"]:
                    for operator in preference_dict["physician"]:
                        operator_pref = dict()
                        operator_pref.update({"physician":operator})
                        if ("penality" in preference_dict):     # teorically this must always be
                            operator_pref.update({"penality":preference_dict["penality"]})
                        if ("day" in preference_dict):
                            operator_pref.update({"day":preference_dict["day"]})
                        operators_preference.append(operator_pref)
                return operators_preference
            else:
                return list()
        else:
            raise ValueError(f"Job '{job_key}' not found while trying to list operators preference!")
        
    def getSanitizedJobOperatorPreferenceList(self, job_key):
        '''
        get the sanitized preference list that have been set in job_key;
        return a list of dict, element keys are: {"physician", "penality", "day"}
        '''
        # WATCH OUT, in case of duplicate operator in job_key preferences, only the last read will be reported;
        # this is because duplicate preferences for the same operator should not exist!
        if self.existsJobKey(job_key):
            if "preference" in self.__input_jobs_sanitized[job_key]:
                operators_preference = list()       # list of dictionary with operator and relative preference attributes
                for preference_dict in self.__input_jobs_sanitized[job_key]["preference"]:
                    for operator in preference_dict["physician"]:
                        operator_pref = dict()
                        operator_pref.update({"physician":operator})
                        if ("penality" in preference_dict):     # teorically this must always be
                            operator_pref.update({"penality":preference_dict["penality"]})
                        if ("day" in preference_dict):
                            operator_pref.update({"day":preference_dict["day"]})
                        operators_preference.append(operator_pref)
                return operators_preference
            else:
                return list()
        else:
            raise ValueError(f"Job '{job_key}' not found while trying to list operators preference!")
        
    def hasJobOperatorTheSamePreference(self, job_key, operators_list:list, sanitized_operators:bool=False):
        ''' check if the operators have identical preferences '''
        # checking that means that simply are in the same preference physician list, or none of them have preference

        # if list length is 0 or 1 (nonsense) do nothing
        if (len(operators_list)<=1):
            return True
        
        # check operations on 2+ elements list; using "and" and "or" series (so using only 2 variables instead of a proportional list)
        have_pref_and = True   # if it remains True then ALL operators have a preference set
        have_pref_or = False   # if it remains False then ALL operators DON'T have a preference set
        for op in operators_list:
            pref = self.hasJobOperatorPreference(job_key=job_key, operator=op, sanitized_operator=sanitized_operators)
            have_pref_and &= pref
            have_pref_or |= pref
        if have_pref_and:  # all operators have preference set: perform further checking
            working_job_prefs = self.__input_jobs_sanitized[job_key]["preference"] if sanitized_operators else self.get_job_dict(job_key)["preference"]
            # now searching the first operator in list through preferences
            for preference in working_job_prefs:
                if (operators_list[0] in preference["physician"]):
                    # alright, found op in this preference, now checking for others or return false
                    for op_index in range(1, len(operators_list)):   # re-using op, i won't do any other loop in outer for cycle
                        if (not operators_list[op_index] in preference["physician"]):
                            return False
                    # alright, looped all operators without returning False, so they are in the same list, returning true
                    return True
            # if I reach this point it means i don't found the first operator of the list in preferences, this should not happens because of "have_pref_and" check
            return False
        else:    # someone or nobody have preference set
            return (not have_pref_or)   #   so, if have_pref_or=False nobody have preference set, so they have the same pref; 
                                        #   if it's True someone have pref and someone not, so they don't have the same pref

    def getJobOperatorEqualPreferences(self, job_key, operators_list, sanitized_operators):
        ''' 
        return a dict with the equal preferences attributes and corresponding values 
        (can be {"preference", "penality", "day"}) between all the operators in operators_list 
        '''
        if sanitized_operators:
            operators_list = self.de_sanitize_operators_list(operators_list)
        
        if (len(operators_list)>1):
            pref_set = set()
            pref_penality_set = set()
            pref_day_set = set()
            for op in operators_list:
                op_preference = self.getJobOperatorPreference(job_key=job_key, operator=op)
                pref_set.add(op_preference["preference"])
                pref_penality_set.add(op_preference["penality"])
                op_preference["day"].sort()     # ensure it get matched correctly if equals
                pref_day_set.add(str(op_preference["day"])) # need to convert into string because a list/set is not hashable, cannot put in a set
            common_prefs = dict()
            if (len(pref_set)==1):
                common_prefs.update( { "preference":list(pref_set)[0] } )
            if (len(pref_penality_set)==1):
                common_prefs.update( {"penality":list(pref_penality_set)[0]} )
            if (len(pref_day_set)==1):
                day_list = json.loads(list(pref_day_set)[0])
                common_prefs.update({"day":day_list})
            return common_prefs
        elif (len(operators_list)==1):
            return self.getJobOperatorPreference(job_key=job_key, operator=operators_list[0])
        else: # (len(operators_list)<1)
            return { "preference":False, "penality":0, "day":list() }

    
    # GETTER : particular queries
    def getOperatorJobKeysList(self, operator, sanitized_operator:bool=False):
        ''' return jobs of a specified operators '''
        job_keys_list = list()
        if sanitized_operator:
            for job in self.__input_jobs_sanitized:
                if operator in self.__input_jobs_sanitized[job]["qualified_physician"]:
                    job_keys_list.append(job)
        else:
            for job in self.get_jobs_dict():
                if operator in self.get_job_dict(job)["qualified_physician"]:
                    job_keys_list.append(job)
        return job_keys_list
    
    
    # SETTER : add / update
    
    # add a new job specifying the new key; to update an existing job, use the updateJob method
    # job_key, job_category, job_days, job_time are REQUIRED fields
    # the job_operator field is OPTIONAL
    #
    # also it doesn't handle the multi_operator task case, because it's given by key
    def __addNewJob_byKey(self, job_key, job_category, job_days, job_time, job_operators=None):
        if ( job_key in self.get_jobs_dict().keys() ):
            raise ValueError("Job Key already present!")
        else:
            # build the new dict element
            job_element = dict()

            job_element.update({"cathegory":job_category})
            
            if ( ( isinstance(job_days, list) | isinstance(job_days, set) | isinstance(job_days, tuple) ) & 
                len(job_days)<=7 & 
                self.min(job_days) >= ( 0 + DAY_OFFSET ) & 
                self.max(job_days) <= ( 6 + DAY_OFFSET ) ):
                job_days = list(job_days)
                job_days.sort()
                job_element.update({"operating_day":job_days})
            else:
                raise ValueError(f"Error in '{job_key}' saving: {job_days} is not a valid operating_day")
            
            if ( ( isinstance(job_time, list) | isinstance(job_time, tuple) ) & 
                    (len(job_time)==2) & 
                    (isinstance(job_time[0],int)) & (isinstance(job_time[1],int)) & 
                    (self.min(job_time)>=0) & (self.max(job_time)<=23) ):
                job_element.update({"operating_time":job_time})
            else:
                raise ValueError(f"Error in '{job_key}' saving: {job_time} is not a valid operating_time")
            
            if ( job_operators != None ):
                if ( isinstance(job_operators, list) | isinstance(job_operators, tuple) | isinstance(job_operators, set) ) :
                    job_element.update({"qualified_physician":list(set(job_operators))})    # job_operators should be already uniques, but just to be sure...
                else:
                    raise ValueError(f"Error in '{job_key}' saving: qualified_operators is not a list")
            else:
                job_element.update({"qualified_physician":list()})

            # add job self-compatibility, required!
            job_element.update({"compatibility":[job_key,]})

            # finally add the new element
            self.__input["job_description"].update({job_key:job_element})
            # rebuild the sanitized dictionary
            self.__build_sanitized_dictionary()
            # return success of input
            return self.existsJobKey(job_key)

        
    def addNewJob(self, job_name, job_location, job_category, job_days, job_time, job_operators=None, 
                  multiple_operator_task=False, sanitized_input=False):
        ''' add a new job; to update an existing job, use the updateJob method
        job_name, job_location, job_category, job_days, job_time are REQUIRED fields
        the job_operator field is OPTIONAL, multiple_operator_task is defaulted to False
        IF MULTIPLE_OPERATOR_TASK IS TRUE, then job_days, job_time and job_operators HAVE TO BE BI-DIMENSIONAL LISTS, 
        one for the main task and the other for the multiple_operator task
        sanitized_input (default=False) specifies if name, location, category and operators are sanitized '''
        
        # de_sanitize input before proceeding
        if (sanitized_input):
            # these are single fields in any multiple_operator_task case
            job_name = self.de_sanitize_string(job_name)
            job_location = self.de_sanitize_string(job_location)
            job_category = self.de_sanitize_string(job_category)
            # sanitizing job_operators, considering multiple_operator_task to determine if list or matrix
            if (job_operators!=None):
                if multiple_operator_task:
                    # operators list is a 2xN matrix
                    job_operators_desanitized = list()
                    for operators in job_operators:
                        if (operators!=None):
                            job_operators_desanitized.append(self.de_sanitize_operators_list(operators))
                        else:
                            job_operators_desanitized.append(None)
                    # now replace the original parameter with desanitized matrix
                    job_operators = job_operators_desanitized
                else:
                    job_operators = self.de_sanitize_operators_list(job_operators)
            # nothing else to desanitize (days and time have to be numbers)
        # NOW I'm sure all parameters are not sanitized

        # NOW convertng the time list/matrix to int, to be sure
        int_job_time = list()
        if multiple_operator_task:
            # converting the 2x2 time to int
            for i in range(len(job_time)):
                int_job_time.append(list())
                for time_ in job_time[i]:
                    int_job_time[i].append(int(time_))
        else:
            for time_ in job_time:
                int_job_time.append(int(time_))
        # replacing the original parameter with the converted int time
        job_time = int_job_time

        # NOW the job can be added
        # creating the new key (existence check is done by __addNewJob_byKey())
        job_key = job_location + "," + job_name

        if multiple_operator_task:
            # we have to create 2 job, with a predefined key format and add the "other" one to multiple operator task set
            job_key_main = job_key + "(1)"
            job_key_other = job_key + "(other)"
            # main job creation
            success = self.__addNewJob_byKey(job_key=job_key_main, 
                                job_category=job_category, 
                                job_days=job_days[0], 
                                job_time=job_time[0], 
                                job_operators=job_operators[0])
            # multiple_operator job creation
            success = success & self.__addNewJob_byKey(job_key=job_key_other, 
                                    job_category=job_category, 
                                    job_days=job_days[1], 
                                    job_time=job_time[1], 
                                    job_operators=job_operators[1])
            # adding it to the multiple_operator_job list
            success = success & self.add_multipleOperatorTask(job_key_other)
            # now save changes on the file
            return (success & self.__save_json_input())
        else:
            # normal job creation
            success = self.__addNewJob_byKey(job_key=job_key, 
                        job_category=job_category, 
                        job_days=job_days, 
                        job_time=job_time, 
                        job_operators=job_operators)
            # now save changes on the file
            return (success & self.__save_json_input())


    # this method is intended for internal use, and it don't deals with sanitized dictionary
    def __renameJobKey(self, new_key, old_key):
        '''
        The following line:
        self.__input_jobs["job_description"][new_key] = self.__input_jobs().pop(old_key) 
        could easily resolve the problem (delete the old element and re-push it with the new key value) 
        but it place the modified element on the bottom of the dict.
        I don't know if it is necessary to preserve the order, or if it will be in the future, 
        so to avoid problems with that I rebuild the entire dictionary in order to "rename" the key 
        but preserving the order.
        '''
        new__input = dict()
        for element_key in self.__input:
            if (element_key == "job_description"):
                new__input.update({"job_description":dict()})
                for job_key in self.get_jobs_dict():
                    if job_key == old_key:      # key to "rename"
                        new__input["job_description"].update({new_key:self.get_job_dict(old_key)})
                    else:                           # the other elements will be copied as is
                        new__input["job_description"].update({job_key:self.get_job_dict(job_key)})
            else:                           # the other elements will be copied as is
                new__input.update({element_key:self.__input[element_key]})
        # now replace the old dict with the newly created
        self.__input = new__input
        # replace also in multiple operator task list
        if(self.isMultipleOperatorTask(old_key)):
            self.remove_multipleOperatorTask(old_key)
            self.add_multipleOperatorTask(new_key)
        # TODO: replace everywhere else it appears
        return self.existsJobKey(new_key)

    def updateJob( self, job_key, new_name=None, new_location=None, new_category=None, 
                    new_days=None, new_time=None, new_operators=None, sanitized_input=False ):
        ''' Update job fields. Can update also only single fields
        N.B.: The fields to update will be overwritten!
        tized_input (default=False) specifies if name, location, category and operators are sanitized '''
        
        # de-sanitize data
        if sanitized_input:
            new_name = None if (new_name==None) else self.de_sanitize_string(new_name)
            new_location = None if (new_location==None) else self.de_sanitize_string(new_location)
            new_category = None if (new_category==None) else self.de_sanitize_string(new_category)
            # Assuming new_days and new_data in correct format
            new_operators = None if (new_operators==None) else self.de_sanitize_operators_list(new_operators)
        
        if (job_key in self.get_jobs_dict()):
            # firtst case: a new key need to be built:
            if ((new_name!=None) | (new_location!=None)):
                # rebuild key then update
                job_name = new_name if new_name!=None else self.getJobName(job_key)
                job_location = new_location if new_location!=None else self.getJobLocation(job_key)
                new_job_key = job_location + "," + job_name
                # check if is a useless key update
                if (job_key != new_job_key):
                    if (self.existsJobKey(new_job_key)):
                        raise KeyError(f"Error: the new generated key '{new_job_key}' is already present!")
                    else:
                        if (self.__renameJobKey(new_key=new_job_key, old_key=job_key)):
                            # from now we work on the new key, so:
                            job_key = new_job_key
                        else:
                            raise KeyError(f"Error while renaming '{job_key}' to '{new_job_key}'")
                else:
                    pass    # useless key update, do nothing...
            # check if need to update other fields
            if new_category!=None:
                self.__input["job_description"][job_key].update({"cathegory":new_category})
            
            if new_days!=None:
                if ( ( isinstance(new_days, list) | isinstance(new_days, set) | isinstance(new_days, tuple) ) & 
                    len(new_days)<=7 & 
                    self.min(new_days) >= ( 0 + DAY_OFFSET ) & 
                    self.max(new_days) <= ( 6 + DAY_OFFSET ) ):
                    new_days = list(new_days)
                    new_days.sort()
                    self.__input["job_description"][job_key].update({"operating_day":new_days})
                else:
                    raise ValueError(f"Error updating '{job_key}': {new_days} is not a valid operating_day")
        
            if new_time!=None:
                if ( ( isinstance(new_time, list) | isinstance(new_time, tuple) ) & 
                        (len(new_time)==2) & 
                        (isinstance(new_time[0],int)) & (isinstance(new_time[1],int)) & 
                        (self.min(new_time)>=0) & (self.max(new_time)<=23) ):
                    self.__input["job_description"][job_key].update({"operating_time":new_time})
                else:
                    raise ValueError(f"Error updating '{job_key}': {new_time} is not a valid operating_time")
            
            if new_operators!=None:
                if ( isinstance(new_operators, list) | isinstance(new_operators, tuple) | isinstance(new_operators, set) ) :
                    self.__input["job_description"][job_key].update({"qualified_physician":list(set(new_operators))})    # job_operators should be already uniques, but just to be sure...
                else:
                    raise ValueError(f"Error updating '{job_key}': qualified_operators is not a list")
            # the update process is finished, saving changes
            self.__save_json_input()
            # update the sanitized dictionary
            self.__build_sanitized_dictionary()
            # return the updated job key (if the name or location is changed, the key change)
            return job_key
        else:
            raise KeyError(f"Error: job key {job_key} not found while updating!")
        
    # Setter : Compatibility

    def addJobCompatibility(self, job_key:str, comp_job_key:str, days:list=None):
        ''' add comp_job_key to job_key compatibility (and vice-versa). If already compatible, do nothing '''
        if (self.existsJobKey(job_key) & self.existsJobKey(comp_job_key)):
            if(self.areJobsCompatible(job_key_1=job_key, job_key_2=comp_job_key)):
                return True     # already compatible, do nothing
            else:               # adding
                days_valid = (days!=None)
                if days_valid:
                    days_valid = (len(days)>0)
                if days_valid:      # add as extra_compatibility
                    # add comp_job_key to job_key
                    if ("extra_compatibility" in self.get_job_dict(job_key)):
                        self.__input["job_description"][job_key]["extra_compatibility"].update( { comp_job_key:days } )
                    else:
                        self.__input["job_description"][job_key].update( { "extra_compatibility":{ comp_job_key:days } } )
                    # add job_key to comp_job_key
                    if ("extra_compatibility" in self.get_job_dict(comp_job_key)):
                        self.__input["job_description"][comp_job_key]["extra_compatibility"].update( { job_key:days } )
                    else:
                        self.__input["job_description"][comp_job_key].update( { "extra_compatibility":{ job_key:days } } )
                else:               # add as regular compatibility
                    # add comp_job_key to job_key
                    if ("compatibility" in self.get_job_dict(job_key)):
                        if (not comp_job_key in self.get_job_dict(job_key)["compatibility"]):
                            self.__input["job_description"][job_key]["compatibility"].append(comp_job_key)
                    else:
                        self.__input["job_description"][job_key].update( { "compatibility":[comp_job_key, ] } )
                    # add job_key to comp_job_key
                    if ("compatibility" in self.get_job_dict(comp_job_key)):
                        if (not job_key in self.get_job_dict(comp_job_key)["compatibility"]):
                            self.__input["job_description"][comp_job_key]["compatibility"].append(job_key)
                    else:
                        self.__input["job_description"][comp_job_key].update( { "compatibility":[job_key, ] } )
                # saving changes
                saved = self.__save_json_input()
                # rebuild sanitized dict (pretty useless, compatibility part in that dict is not used)
                self.__build_sanitized_dictionary()
                return saved
        else:
            raise ValueError(f"Error: job key '{job_key}' od '{comp_job_key}' not found!")

    def deleteJobCompatibility(self, job_key:str, comp_job_key:str):
        ''' remove comp_job_key from job_key compatibility (and vice-versa). If already not compatible, do nothing '''
        if (self.existsJobKey(job_key) & self.existsJobKey(comp_job_key)):
            if(self.areJobsCompatible(job_key_1=job_key, job_key_2=comp_job_key)):  # there is the compatibility, proceeding to remove
                # searching now in job_key
                if ("compatibility" in self.get_job_dict(job_key)):
                    if comp_job_key in self.get_job_dict(job_key)["compatibility"]:
                        # found, removing
                        self.__input["job_description"][job_key]["compatibility"].remove(comp_job_key)
                        if (len(self.get_job_dict(job_key)["compatibility"])==0):   # removing the eventual empty list
                            self.__input["job_description"][job_key].pop("compatibility")
                if ("extra_compatibility" in self.get_job_dict(job_key)):
                    if comp_job_key in self.get_job_dict(job_key)["extra_compatibility"]:
                        # found, removing
                        self.__input["job_description"][job_key]["extra_compatibility"].pop(comp_job_key)
                        if (len(self.get_job_dict(job_key)["extra_compatibility"].keys())==0):   # removing the eventual empty dict
                            self.__input["job_description"][job_key].pop("extra_compatibility")
                # searching now in comp_job_key
                if ("compatibility" in self.get_job_dict(comp_job_key)):
                    if job_key in self.get_job_dict(comp_job_key)["compatibility"]:
                        # found, removing
                        self.__input["job_description"][comp_job_key]["compatibility"].remove(job_key)
                        if (len(self.get_job_dict(comp_job_key)["compatibility"])==0):  # removing the eventual empty list
                            self.__input["job_description"][comp_job_key].pop("compatibility")
                if ("extra_compatibility" in self.get_job_dict(comp_job_key)):
                    if job_key in self.get_job_dict(comp_job_key)["extra_compatibility"]:
                        # found, removing
                        self.__input["job_description"][comp_job_key]["extra_compatibility"].pop(job_key)
                        if (len(self.get_job_dict(comp_job_key)["extra_compatibility"].keys())==0): # removing the eventual empty dict
                            self.__input["job_description"][comp_job_key].pop("extra_compatibility")
                # saving changes
                saved = self.__save_json_input()
                # rebuild sanitized dict (pretty useless, compatibility part in that dict is not used)
                self.__build_sanitized_dictionary()
                return saved
            else:
                return True # already not present, do nothing
        else:
            raise ValueError(f"Error: job key '{job_key}' od '{comp_job_key}' not found!")
        
    def editJobCompatibility(self, job_key:str, comp_job_key:str, days:list=None):
        ''' edit comp_job_key in job_key compatibility (and vice-versa). If just overwrite current compatibility '''
        # this work can be done manually, checking if there's or not day set, and put the day if given ;
        # this means moving the compatibility to extra_compatibility or vice-versa.
        # Instead of doing all this, i simply delete and re-add the compatibility
        if (self.existsJobKey(job_key) & self.existsJobKey(comp_job_key)):
            saved = True
            if(self.areJobsCompatible(job_key_1=job_key, job_key_2=comp_job_key)):
                saved &= self.deleteJobCompatibility(job_key=job_key, comp_job_key=comp_job_key)
            saved &= self.addJobCompatibility(job_key=job_key, comp_job_key=comp_job_key, days=days)
            return saved
        else:
            raise ValueError(f"Error: job key '{job_key}' od '{comp_job_key}' not found!")

    # Setter : seniority    
    
    def addSeniorityOperator(self, operator:str, seniority_label:str, is_operator_sanitized:bool=False, is_seniority_label_sanitized:bool=False):
        ''' add the operator to the specified seniority label; raise a ValueError if the key is not found '''
        if is_operator_sanitized:
            operator = self.de_sanitize_operator(operator)
        if is_seniority_label_sanitized:
            seniority_label = self.de_sanitize_seniority_label(seniority_label)
        if (seniority_label in self.__seniority_operators_labels):
            if (operator in self.__input[seniority_label]):
                return True     # operator is already in that seniority, do nothing
            else:   # in this way we can eventually add an operator to multiple seniorities
                # adding to the list
                self.__input[seniority_label].append(operator)
                # saving files
                saved = self.__save_json_input()
                # adding to the sanitized list (without rebuilding the whole sanitized input dict)
                self.__seniority_operators_sanitized[seniority_label].append(operator)
                # return the status
                return saved
        else:
            raise ValueError(f"Error: seniority label key '{seniority_label}' not found!")
    
    def deleteSeniorityOperator(self, operator:str, seniority_label:str, is_operator_sanitized:bool=False, is_seniority_label_sanitized:bool=False):
        ''' 
        delete the operator from the specified seniority label; 
        raise a ValueError if the seniority label is not found; 
        if the operator is not found in that seniority, do nothing
        '''
        if is_operator_sanitized:
            operator = self.de_sanitize_operator(operator)
        if is_seniority_label_sanitized:
            seniority_label = self.de_sanitize_seniority_label(seniority_label)
        if (seniority_label in self.__seniority_operators_labels):
            if (operator in self.__input[seniority_label]):
                # operator found, removing it
                self.__input[seniority_label].remove(operator)
                # saving
                saved = self.__save_json_input()
                # removing from the sanitized list (without rebuilding the whole sanitized input dict)
                self.__seniority_operators_sanitized[seniority_label].remove(self.sanitize_operator(operator))
                # return the status
                return saved
            else:   # already not present, do nothing
                return True
        else:
            raise ValueError(f"Error: seniority label key '{seniority_label}' not found!")
        
    
    def setSeniorityOperatorList(self, operator_list, seniority_label:str, is_operator_sanitized:bool=False, is_seniority_label_sanitized:bool=False):
        ''' set (overwrite/replace) the list of operators for the seniority label; raise a ValueError if the key is not found '''
        if isinstance(operator_list, list):
            pass
        elif (isinstance(operator_list, tuple) | isinstance(operator_list, set)):
            operator_list = list(operator_list)
        else:
            raise ValueError("Error: operator_list is not a list!")
        
        if is_operator_sanitized:
            operator_list = self.de_sanitize_operators_list(operator_list)

        if is_seniority_label_sanitized:
            seniority_label = self.de_sanitize_seniority_label(seniority_label)

        if (seniority_label in self.__seniority_operators_labels):
            # replacing list
            self.__input[seniority_label] = operator_list.copy()
            # saving files
            saved = self.__save_json_input()
            # rebuilding sanitized dict (without rebuilding the whole sanitized input dict)
            self.__seniority_operators_sanitized[seniority_label].clear()
            self.__seniority_operators_sanitized[seniority_label] = self.sanitize_operators_list(operator_list)
            # return the status
            return saved
        else:
            raise ValueError(f"Error: seniority label key '{seniority_label}' not found!")

    
    def addJobOperator(self, job_key, operator, sanitized_operator:bool=False):
        ''' add the specified operator to the job_key '''
        if (self.existsJobKey(job_key)):
            # check if already operator in that job and return doing nothing
            if self.hasOperator(job_key=job_key, operator=operator, sanitized_operator=sanitized_operator):
                return True
            else:
                # desanitization
                if sanitized_operator:
                    operator = self.de_sanitize_operator(operator)
                # add operator to list
                self.__input["job_description"][job_key]["qualified_physician"].append(operator)
                # rebuild sanitized dictionary
                self.__build_sanitized_dictionary()
                # self save changes on file
                success = self.__save_json_input()
                return ( success & self.hasOperator(job_key=job_key, operator=operator ) )
        else:
            raise ValueError(f"job_key '{job_key}' not found while adding operator!")
        
    
    def setJobOperatorPreference(self, job_key, operator, pref_penality:int, pref_day:list=None, sanitized_operator:bool=False):
        '''
        add or update a preference for an operator in job_key;
        if operator isn't in that job, adds it and then set the preference
        '''
        if sanitized_operator:
            operator = self.de_sanitize_operator(operator)
        # ensuring pref_days list is a valid list or None
        if (pref_day!=None):
            if ( isinstance(pref_day, list) | isinstance(pref_day, tuple) | isinstance(pref_day, set) ):
                if (len(pref_day)==0):
                    pref_day = None
                else:
                    if (not isinstance(pref_day, list)):
                        pref_day = list(pref_day)
                    pref_day.sort()
            else:
                pref_day = None
        # input checking: adding preference with penality 0 (and no day set) has not to be added, ii's like have no preference
        if ((pref_penality==0) & (pref_day==None)):
            if (self.hasJobOperatorPreference(job_key, operator)):
                # removing it and return
                return self.deleteJobOperatorPreference(job_key, operator)
            else:
                # already have no preference, do nothing and return
                return True
            

        # now calling addJobOperator is safe, because if it already exists it does nothing
        # job_key existence is also done by this function
        if (self.addJobOperator(job_key, operator)):
            # checking if already have a preference (update action)
            deleted_success = True
            if (self.hasJobOperatorPreference(job_key, operator)):
                # removing it before re-adding
                deleted_success = self.deleteJobOperatorPreference(job_key, operator)
            to_add_as_new = True
            if deleted_success:
                if "preference" in self.get_job_dict(job_key):
                    # check if a dict with the same preference attributes exist
                    for curr_pref_dict_index, curr_pref_dict in enumerate(self.get_job_dict(job_key)["preference"]):
                        if ( ("penality" in curr_pref_dict) & (curr_pref_dict["penality"] == pref_penality)):
                            if ( ("day" in curr_pref_dict) & (pref_day!=None) ):
                                if ( set(pref_day) == set(curr_pref_dict["day"]) ):
                                    # alright there, it exists; simply adding it to the existing preference dict
                                    self.__input["job_description"][job_key]["preference"][curr_pref_dict_index]["physician"].append(operator)
                                    self.__input["job_description"][job_key]["preference"][curr_pref_dict_index]["physician"].sort()
                                    to_add_as_new = False
                            elif ( (not "day" in curr_pref_dict) & (pref_day==None) ):
                                # alright there, it exists (without day); simply adding it to the existing preference dict
                                self.__input["job_description"][job_key]["preference"][curr_pref_dict_index]["physician"].append(operator)
                                self.__input["job_description"][job_key]["preference"][curr_pref_dict_index]["physician"].sort()
                                to_add_as_new = False
                # if it was not added to an existing preference dict, create it as new
                if to_add_as_new:
                    preference = {  "physician":[operator,],
                                    "penality":pref_penality }
                    if (pref_day!=None):
                        preference.update( { "day":pref_day } )
                    # then adding the preference
                    if not "preference" in self.get_job_dict(job_key):
                        self.__input["job_description"][job_key].update( {"preference":list()} )
                    self.__input["job_description"][job_key]["preference"].append(preference)
                # rebuilding sanitized dict
                self.__build_sanitized_dictionary()
                # done, saving
                return self.__save_json_input()
            else:
                return False
        else:
            raise ValueError(f"Error: '{operator}' not present in '{job_key}'!")


    def deleteJobOperatorPreference(self, job_key, operator, sanitized_operator:bool=False):
        '''
        remove an operator preference in job_key;
        if operator already isn't in preference, do nothing
        '''
        if sanitized_operator:
            operator = self.de_sanitize_operator(operator)
        if self.existsJobKey(job_key):
            if "preference" in self.get_job_dict(job_key):
                for preference_dict_index, preference_dict in enumerate(self.get_job_dict(job_key)["preference"]):
                    if operator in preference_dict["physician"]:
                        # found! removing...
                        self.__input["job_description"][job_key]["preference"][preference_dict_index]["physician"].remove(operator)
                        # checking, saving and returning
                        if (self.hasJobOperatorPreference(job_key, operator)):
                            # operator preference still present, something went wrong
                            return False
                        else:
                            # deletion successful
                            # now check if that deletion generated an empty physician preference list
                            if (len(self.get_job_dict(job_key)["preference"][preference_dict_index]["physician"])==0):
                                # remove the dict with empty physicians list
                                self.__input["job_description"][job_key]["preference"].pop(preference_dict_index)
                                # checking also if this deletion generated an empty preference list
                                if (len(self.get_job_dict(job_key)["preference"])==0):
                                    # remove the empty preferences list
                                    del self.__input["job_description"][job_key]["preference"]
                            # saving and returning
                            self.__build_sanitized_dictionary()
                            return self.__save_json_input()
                # exiting "for" loop without returning means that operator has not been found on preferences, so do nothing and return
                return True
        else:
            raise ValueError(f"Error: job_key '{job_key}' not found while removing '{operator}' preference!")

    
    # TODO (IMPORTANT): remove all occurrences! (like in preferences, seniority, and so on)
    def deleteJob(self, job_key):
        if self.existsJobKey(job_key):
            if self.isMultipleOperatorTask(job_key):
                self.remove_multipleOperatorTask(job_key)
            self.__input["job_description"].pop(job_key)
            # save the file
            self.__save_json_input()
            return (not self.existsJobKey(job_key))
        else:
            raise KeyError(f"Error: job key {job_key} not found while deleting!")
        # techincally there is no need to rebuild the sanitized dictionary
        # since after the deletion the input_helper instance will be destroyed
        # (and having a the deleted key in the sanitized dictionary don't cause any problem)

    
    def deleteJobOperator(self, job_key, operator, sanitized_operator:bool=False):
        ''' delete the specified operator from the job_key '''
        if (self.existsJobKey(job_key)):
            # check if operator isn't in that job and, if so, return doing nothing
            if ( not self.hasOperator(job_key=job_key, operator=operator, sanitized_operator=sanitized_operator) ):
                return True
            else:
                # desanitization
                if sanitized_operator:
                    operator = self.de_sanitize_operator(operator)
                # first we have also to remove a preference, if it had one
                if (self.hasJobOperatorPreference(job_key, operator)):
                    self.deleteJobOperatorPreference(job_key, operator)
                # now remove operator from list
                self.__input["job_description"][job_key]["qualified_physician"].remove(operator)
                # rebuild sanitized dictionary
                self.__build_sanitized_dictionary()
                # self save changes on file
                success = self.__save_json_input()
                return ( success & (not self.hasOperator(job_key=job_key, operator=operator)) )
        else:
            raise ValueError(f"job_key '{job_key}' not found while adding operator!")

    # Setter: multiple_operator_task

    def  add_multipleOperatorTask(self, job_key):
        # the multiple_operator task have to end with ",other)" or "(other)"
        if (not self.isMultipleOperatorTask(job_key)):
            #if (job_key[-6:] == "other)"):
            self.__input["multiple_operator_task"].append(job_key)
            return ("multiple_operator_task" in self.__input)
            #else:
            #    raise ValueError("Error: cannot add to multiple_operator_task, the job_key does not match the required format")
        else:
            raise KeyError(f"Error: '{job_key}' is already a multiple_operator_task!")
    
    
    def remove_multipleOperatorTask(self, job_key):
        ''' Delete the multiple_operator_task from the list and keep it in the job_description '''
        self.__input["multiple_operator_task"].remove(job_key)
        return (not "multiple_operator_task" in self.__input)
        # TODO: rename the job keys (to remove the "1)" anf "other)" endings)
    
    def editMultipleOperatorTask(self, old_job_key, new_job_key):
        success = self.remove_multipleOperatorTask(old_job_key)
        return (success & self.add_multipleOperatorTask(new_job_key))
