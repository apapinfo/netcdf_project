# Importation des bibliothèques




from typing_extensions import Self
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, date, time
import re
import json




# Définition de la classe modeleNetcdf




class modeleNetcdf:
    
    
    # Initialisation d'un catalogue sous forme d'une liste contenant une liste de noms possibles pour la variable datetime du fichier netCDF et une liste de données temporelles
    datetime_catalog: list[list] = [['datetime', 'date', 'time', 'temps', 'heure', 'hour', 'minute', 'min', 'seconde', 'sec', 'YYYY/MM/DD', 'DD/MM/YYYY', 'HH:MM:SS']]
    
    
    # Constructeur par défaut
    
    
    def __init__(self: Self, controleurlogs, dataframe: pd.DataFrame, xarray_dataset: xr.Dataset):
        
        self.controleurlogs = controleurlogs
        self.dataframe: pd.DataFrame = dataframe
        self.xarray_dataset: xr.Dataset = xarray_dataset
    
    
    # Définition des méthodes
    
    
    def check_dataframe_integrity(self: Self):
        
        # Si le dataframe est vide
        if self.dataframe.empty:
            self.controleurlogs.add_log("Empty dataframe.\n")
            self.controleurlogs.add_colored_log("Empty dataframe.\n", "red")
            self.dataframe = pd.DataFrame()
        # Sinon
        else:
            # Parcours de chaque colonne du dataframe
            for column in self.dataframe.columns:
                # Si le nom de la colonne du dataframe en minuscule sans espace blanc n'est pas dans la première liste du catalogue
                if column.replace(' ', '').lower() not in modeleNetcdf.datetime_catalog[0]:
                    # Parcours de chaque clé du dataset xarray pour la colonne du dataframe
                    for key in list(self.xarray_dataset.data_vars.keys()):
                        # Si les noms de la variable du fichier netCDF sont renseignés
                        if 'long_name' in self.xarray_dataset[key].attrs.keys() and 'standard_name' in self.xarray_dataset[key].attrs.keys(): 
                            # Si un des mots de la liste des noms possibles de la clé est le nom de la colonne du dataframe
                            if modeleNetcdf.check_names([self.xarray_dataset[key].attrs['long_name'], self.xarray_dataset[key].attrs['standard_name']], column) == True:
                                # Si le type des données du fichier netCDF est bien précisé
                                if 'dtype' in self.xarray_dataset[key].attrs.keys():
                                    # Si les données de la colonne du dataframe sont du même type que celui des données du fichier netCDF ou si une colonne du dataframe est vide
                                    if self.dataframe[column].dtype == self.xarray_dataset[key].attrs['dtype'] or self.dataframe[column].isna().all() == True:
                                        # Si la liste de données de la colonne du dataframe contient au minimum 10 données
                                        if len(self.dataframe[column].iloc[:].tolist()) >= 10:
                                            # Si la clé est latitude
                                            if key == 'latitude':
                                                # Si les données de la colonne du dataframe sont des valeurs de latitude
                                                if all(self.dataframe[column].between(-90.0, 90.0)):
                                                    # Ajout des données de la colonne du dataframe dans le tableau de données associé à la clé
                                                    self.xarray_dataset[key].values = np.array(self.dataframe[column].iloc[:].tolist())
                                                # Sinon les données de la colonne du dataframe ne sont pas des valeurs de latitude
                                                else:
                                                    self.controleurlogs.add_log("Latitude values are not between -90 and 90.\n")
                                                    self.controleurlogs.add_colored_log("Latitude values are not between -90 and 90.\n", "red")
                                            # Si la clé est longitude
                                            elif key == 'longitude':
                                                # Si les données de la colonne du dataframe sont des valeurs de longitude
                                                if all(self.dataframe[column].between(-180.0, 180.0)):
                                                    # Ajout des données de la colonne du dataframe dans le tableau de données associé à la clé
                                                    self.xarray_dataset[key].values = np.array(self.dataframe[column].iloc[:].tolist())
                                                # Sinon les données de la colonne du dataframe ne sont pas des valeurs de longitude
                                                else:
                                                    self.controleurlogs.add_log("Longitude values are not between -180 and 180.\n")
                                                    self.controleurlogs.add_colored_log("Longitude values are not between -180 and 180.\n", "red")
                                            # Sinon la clé est une autre clé
                                            else:
                                                # Ajout des données de la colonne du dataframe dans le tableau de données associé à la clé
                                                self.xarray_dataset[key].values = np.array(self.dataframe[column].iloc[:].tolist())
                                        # Sinon
                                        else:
                                            self.controleurlogs.add_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n")
                                            self.controleurlogs.add_colored_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n", "red")
                                    # Sinon
                                    else:
                                        self.controleurlogs.add_log("Data type in column " + column + " : " + str(self.dataframe[column].dtype) + " does not match the type of the variable : " + key + " : " + self.xarray_dataset[key].attrs['dtype'] + " . Data will be not selected.\n")
                                        self.controleurlogs.add_colored_log("Data type in column " + column + " : " + str(self.dataframe[column].dtype) + " does not match the type of the variable : " + key + " : " + self.xarray_dataset[key].attrs['dtype'] + " . Data will be not selected.\n", "red")
                                # Sinon
                                else:
                                    self.controleurlogs.add_log("Data type in column " + column + " not specified for the variable " + key + " . Data will be not selected.\n")
                                    self.controleurlogs.add_colored_log("Data type in column " + column + " not specified for the variable " + key + " . Data will be not selected.\n", "red")
                        # Sinon
                        else:
                            self.controleurlogs.add_log("Unknown names for the variable " + key + " . Data will be not selected.\n")
                            self.controleurlogs.add_colored_log("Unknown names for the variable " + key + " . Data will be not selected.\n", "red")


    def check_datetime_format(self: Self):
        
        # Si le dataframe est vide
        if self.dataframe.empty:
            self.controleurlogs.add_log("Empty dataframe.\n")
            self.controleurlogs.add_colored_log("Empty dataframe.\n", "red")
            self.dataframe = pd.DataFrame()
        # Sinon
        else:
            # Parcours de chaque colonne du dataframe
            for column in self.dataframe.columns:
                # Parcours de chaque élément de la première liste du catalogue
                for element in modeleNetcdf.datetime_catalog[0]:
                    # Si l'élément du catalogue est contenu dans le nom de la colonne du dataframe en minuscule sans espace blanc et si le catalogue ne contient pas plus de 3 listes
                    if element in column.replace(' ', '').lower() and len(modeleNetcdf.datetime_catalog) < 3:
                        # Si la liste de données de la colonne du dataframe contient au minimum 10 données
                        if len(self.dataframe[column].iloc[:].tolist()) >= 10:
                            # Ajout des données de la colonne du dataframe dans le catalogue
                            modeleNetcdf.datetime_catalog.append(self.dataframe[column].iloc[:].tolist())
                        # Sinon
                        else:
                            self.controleurlogs.add_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n")
                            self.controleurlogs.add_colored_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n", "red")
            # Si le catalogue contient une liste de noms possibles pour la variable datetime et une liste de données temporelles
            if len(modeleNetcdf.datetime_catalog) == 2:
                # Parcours de la première donnée temporelle jusqu'à la dernière dans la liste
                for i in range(0, len(modeleNetcdf.datetime_catalog[1])):
                    # Si la donnée temporelle est au format timestamp
                    if isinstance(modeleNetcdf.datetime_catalog[1][i], pd.Timestamp):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                    # Si la donnée temporelle est au format datetime
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], datetime):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))   
                    # Si la donnée temporelle est au format date
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], date):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                    # Si la donnée temporelle est au format time
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], time):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%H:%M:%S"))    
                    # Si la donnée temporelle est une chaîne de caractères
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], str):
                        # Si la donnée temporelle n'est pas au format 'YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DDTHH:MM:SS', 'YYYY-MM-DD' et 'HH:MM:SS'
                        if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1]) (?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])T(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', modeleNetcdf.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == False:
                            # La donnée temporelle est nulle
                            modeleNetcdf.datetime_catalog[1][i] = str('')
                    # Sinon le type de donnée n'est pas correct
                    else:
                        self.controleurlogs.add_log("Incorrect data type for " + str(modeleNetcdf.datetime_catalog[1][i]) + " : " + str(type(modeleNetcdf.datetime_catalog[1][i])) + " . Data will be cleared.\n")
                        self.controleurlogs.add_colored_log("Incorrect data type for " + str(modeleNetcdf.datetime_catalog[1][i]) + " : " + str(type(modeleNetcdf.datetime_catalog[1][i])) + " . Data will be cleared.\n", "red")
                        # La donnée temporelle est nulle
                        modeleNetcdf.datetime_catalog[1][i] = str('')
                # Parcours de chaque clé du dataset xarray
                for key in list(self.xarray_dataset.data_vars.keys()):
                    # Si la clé du dataset xarray en minuscule est un des éléments de la première liste du catalogue
                    if key.lower() in modeleNetcdf.datetime_catalog[0]:
                        # Ajout des données temporelles de la liste dans le tableau de données associé à la clé
                        self.xarray_dataset[key].values = np.array(modeleNetcdf.datetime_catalog[1])
                        # Sortie de boucle
                        break
                # Technique de slicing pour retirer la liste de données temporelles
                modeleNetcdf.datetime_catalog = modeleNetcdf.datetime_catalog[:-1]
            # Si le catalogue contient une liste de noms possibles pour la variable datetime et 2 listes de données temporelles
            elif len(modeleNetcdf.datetime_catalog) == 3:
                # Parcours de la première donnée temporelle jusqu'à la dernière dans la liste
                for i in range(0, len(modeleNetcdf.datetime_catalog[1])):
                    # Si la donnée temporelle est au format timestamp
                    if isinstance(modeleNetcdf.datetime_catalog[1][i], pd.Timestamp):
                        # Si la donnée temporelle est au format 'YYYY-MM-DD'
                        if str(modeleNetcdf.datetime_catalog[1][i].strftime("%H:%M:%S")) == '00:00:00':
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                            modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                            # Si la donnée temporelle de la deuxième liste est au format time
                            if isinstance(modeleNetcdf.datetime_catalog[2][i], time):
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                modeleNetcdf.datetime_catalog[2][i] = str(modeleNetcdf.datetime_catalog[2][i].strftime("%H:%M:%S"))   
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                            # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                            elif isinstance(modeleNetcdf.datetime_catalog[2][i], str):
                                # Si la donnée temporelle est au format 'HH:MM:SS'
                                if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[2][i])) == True:
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                        # Sinon la donnée temporelle est au format 'YYYY-MM-DD HH:MM:SS'
                        else:
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                    # Si la donnée temporelle est au format datetime
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], datetime):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                    # Si la donnée temporelle est au format date
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], date):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                        # Si la donnée temporelle de la deuxième liste est au format time
                        if isinstance(modeleNetcdf.datetime_catalog[2][i], time):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                            modeleNetcdf.datetime_catalog[2][i] = str(modeleNetcdf.datetime_catalog[2][i].strftime("%H:%M:%S"))   
                            # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                        # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                        elif isinstance(modeleNetcdf.datetime_catalog[2][i], str):
                            # Si la donnée temporelle est au format 'HH:MM:SS'
                            if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[2][i])) == True:
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                    # Si la donnée temporelle est au format time
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], time):
                        # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                        modeleNetcdf.datetime_catalog[1][i] = str(modeleNetcdf.datetime_catalog[1][i].strftime("%H:%M:%S"))
                        # Si la donnée temporelle de la deuxième liste est au format date
                        if isinstance(modeleNetcdf.datetime_catalog[2][i], date):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                            modeleNetcdf.datetime_catalog[2][i] = str(modeleNetcdf.datetime_catalog[2][i].strftime("%Y-%m-%d"))   
                            # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[2][i] + " " + modeleNetcdf.datetime_catalog[1][i]
                        # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                        elif isinstance(modeleNetcdf.datetime_catalog[2][i], str):
                            # Si la donnée temporelle est au format 'YYYY-MM-DD'
                            if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', modeleNetcdf.datetime_catalog[2][i])) == True:
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[2][i] + " " + modeleNetcdf.datetime_catalog[1][i]
                    # Si la donnée temporelle est une chaîne de caractères
                    elif isinstance(modeleNetcdf.datetime_catalog[1][i], str):                
                        # Si la donnée temporelle est une chaîne de caractères au format 'YYYY-MM-DD'    
                        if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', modeleNetcdf.datetime_catalog[1][i])) == True:
                            # Si la donnée temporelle de la deuxième liste est au format time
                            if isinstance(modeleNetcdf.datetime_catalog[2][i], time):
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                modeleNetcdf.datetime_catalog[2][i] = str(modeleNetcdf.datetime_catalog[2][i].strftime("%H:%M:%S"))   
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                            # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                            elif isinstance(modeleNetcdf.datetime_catalog[2][i], str):
                                # Si la donnée temporelle de la deuxième liste est une chaîne de caractères au format 'HH:MM:SS'
                                if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[2][i])) == True:
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[1][i] + " " + modeleNetcdf.datetime_catalog[2][i]
                        # Si la donnée temporelle est une chaîne de caractères au format 'HH:MM:SS'    
                        elif bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == True:
                            # Si la donnée temporelle de la deuxième liste est au format date
                            if isinstance(modeleNetcdf.datetime_catalog[2][i], date):
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                modeleNetcdf.datetime_catalog[2][i] = str(modeleNetcdf.datetime_catalog[2][i].strftime("%Y-%m-%d"))   
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[2][i] + " " + modeleNetcdf.datetime_catalog[1][i]
                            # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                            elif isinstance(modeleNetcdf.datetime_catalog[2][i], str):
                                # Si la donnée temporelle de la deuxième liste est une chaîne de caractères au format 'YYYY-MM-DD'
                                if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', modeleNetcdf.datetime_catalog[2][i])) == True:
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    modeleNetcdf.datetime_catalog[1][i] = modeleNetcdf.datetime_catalog[2][i] + " " + modeleNetcdf.datetime_catalog[1][i]
                        # Si la donnée temporelle est une chaîne de caractères qui n'est pas au format 'YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DD' ou 'HH:MM:SS'
                        elif bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1]) (?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', modeleNetcdf.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', modeleNetcdf.datetime_catalog[1][i])) == False:
                            self.controleurlogs.add_log("Date format not recognized for " + str(modeleNetcdf.datetime_catalog[1][i]) + " . Data will be cleared.\n")
                            self.controleurlogs.add_colored_log("Date format not recognized for " + str(modeleNetcdf.datetime_catalog[1][i]) + " . Data will be cleared.\n", "red")
                            # La donnée temporelle est nulle
                            modeleNetcdf.datetime_catalog[1][i] = str('')
                    # Sinon le type de donnée n'est pas correct
                    else:
                        self.controleurlogs.add_log("Incorrect data type for " + str(modeleNetcdf.datetime_catalog[1][i]) + " : " + str(type(modeleNetcdf.datetime_catalog[1][i])) + " . Data will be cleared.\n")
                        self.controleurlogs.add_colored_log("Incorrect data type for " + str(modeleNetcdf.datetime_catalog[1][i]) + " : " + str(type(modeleNetcdf.datetime_catalog[1][i])) + " . Data will be cleared.\n", "red")
                        # La donnée temporelle est nulle
                        modeleNetcdf.datetime_catalog[1][i] = str('') 
                # Technique de slicing pour retirer toutes les listes de données temporelles sauf la première liste de données temporelles
                modeleNetcdf.datetime_catalog = modeleNetcdf.datetime_catalog[:-(len(modeleNetcdf.datetime_catalog)-2)]
                # Parcours de chaque clé du dataset xarray
                for key in list(self.xarray_dataset.data_vars.keys()):
                    # Si la clé du dataset xarray en minuscule est un des éléments de la première liste du catalogue
                    if key.lower() in modeleNetcdf.datetime_catalog[0]:
                        # Ajout des données temporelles de la liste dans le tableau de données associé à la clé
                        self.xarray_dataset[key].values = np.array(modeleNetcdf.datetime_catalog[1])
                        # Sortie de boucle
                        break
                # Technique de slicing pour retirer la liste de données temporelles
                modeleNetcdf.datetime_catalog = modeleNetcdf.datetime_catalog[:-1]


    def adapt_xarray_dataset(self: Self):
        
        # Parcours de chaque clé du dataset xarray
        for key in list(self.xarray_dataset.data_vars.keys()):
            # Si le tableau de données de la clé est vide
            if np.all(self.xarray_dataset[key].values == 0) or np.all(self.xarray_dataset[key].values != self.xarray_dataset[key].values):
                # Suppression des attributs de la variable
                self.xarray_dataset[key].attrs.clear()
                # Suppression de la variable
                del self.xarray_dataset[key]


    def get_xarray_dataset(self: Self):
        
        return self.xarray_dataset


    def __repr__(self: Self):
        
        print(self.xarray_dataset)
        
    
    # Définition des méthodes statiques
    
    
    @staticmethod
    def check_names(name_list: list[str], name: str):
    
        # Modification du nom de la colonne du dataframe en modifiant les caractères spéciaux, les espaces blancs et en le mettant en minuscule
        name = re.sub(r'[^a-zA-Z0-9\s_]', '', name).replace(' ', '_').lower()
        # Initialisation d'un indice
        i = 0
        # Tant que l'indice est inférieur à la longueur de la liste des noms possibles d'une clé du dataset xarray
        while i < len(name_list):
            # Si l'élément de la liste en minuscule est contenu dans le nom de la colonne du dataframe
            if name_list[i].lower() in name:
                # Fin de la boucle
                i = len(name_list)
                # Retourne Vrai
                return True
            # Sinon
            else:
                # Incrémentation de l'indice
                i += 1
        # Retourne Faux
        return False
    
    
    @staticmethod
    def create_xarray_dataset(dataframe: pd.DataFrame, catalog_path: str):
        
        # Initialisation du dataset xarray
        xarray_dataset = xr.Dataset()
        
        # Chargement le fichier JSON
        with open(catalog_path, "r") as f:
            catalog = json.load(f)
            
        # Accès à chaque valeur de chaque attribut du catalogue
        variable_catalog = catalog['variable']
        dimension_catalog = catalog['dimension']
        global_attribute_catalog = catalog['global_attribute']
        
        for dimension in dimension_catalog:
            xarray_dataset.coords[dimension] = np.arange(0, dataframe.shape[0])
        
        for variable_name, variable_data in variable_catalog.items():
            xarray_dataset[variable_name] = xr.DataArray(np.zeros(dataframe.shape[0]), dims=variable_data['dimension'])
            for attribute_name, attribute_value in variable_data['attribute'].items():
                xarray_dataset[variable_name].attrs[attribute_name] = attribute_value
        
        for global_attribute_name, global_attribute_value in global_attribute_catalog.items():
            xarray_dataset.attrs[global_attribute_name] = global_attribute_value
    
        return xarray_dataset




# Programme principal




if __name__ == '__main__':
    
    from vueMainwindow import vueMainwindow
    from vueLogs import vueLogs
    from controleurLogs import controleurLogs
    from controleurToolbar import controleurToolbar
    from vueToolbar import vueToolbar
    import sys
    from PyQt6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    vuemainwindow = vueMainwindow()
    
    vuelogs = vueLogs(vuemainwindow)
    controleurlogs = controleurLogs(vuelogs)
    
    vuetoolbar = vueToolbar(vuemainwindow)
    controleurtoolbar = controleurToolbar(vuetoolbar)
    controleurtoolbar.import_file_option()
    
    # Initialisation du dataframe
    dataframe = controleurtoolbar.dataframe_list[0]
    
    # Initialisation du dataset xarray
    xarray_dataset = modeleNetcdf.create_xarray_dataset(dataframe, './profil_catalog.json')
    
    modelenetcdf = modeleNetcdf(controleurlogs, dataframe, xarray_dataset)
    modelenetcdf.check_dataframe_integrity()
    modelenetcdf.check_datetime_format()
    modelenetcdf.adapt_xarray_dataset()
    modelenetcdf.__repr__()
