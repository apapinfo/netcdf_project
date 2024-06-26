# Importation des bibliothèques




from typing_extensions import Self
import xarray as xr
import pandas as pd
import numpy as np
from datetime import datetime, date, time
import re
import json
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier




# Définition de la classe outilsProcessing




class outilsProcessing:
    
    
    # Initialisation d'un catalogue sous forme d'une liste contenant une liste de noms possibles pour la variable datetime du fichier netCDF et une liste de données temporelles
    datetime_catalog: list[list] = [['datetime', 'date', 'time', 'temps', 'heure', 'hour', 'minute', 'seconde', 'yyyy-mm-ddthh:mm:ss', 'yyyy/mm/ddthh:mm:ss', 'yyyy-mm-dd hh:mm:ss', 'yyyy/mm/dd hh:mm:ss', 'yyyy-mm-dd', 'yyyy/mm/dd', 'dd-mm-yyyy', 'dd/mm/yyyy', 'hh:mm:ss', 'hh:mm:ss.sss']]
    
    
    # Constructeur par défaut
    
    
    def __init__(self: Self, controleurlogs, dataframe: pd.DataFrame, xarray_dataset: xr.Dataset, arrangement_path: str, activation: bool):
        
        self.controleurlogs = controleurlogs
        self.dataframe: pd.DataFrame = dataframe
        self.xarray_dataset: xr.Dataset = xarray_dataset
        self.arrangement_path: str = arrangement_path
        self.activation: bool = activation
    
    
    # Définition des méthodes
    
    
    def create_xarray_dataset_dimension(self: Self, arrangement: dict):
          
        """_summary_
        Création des dimensions du dataset xarray
        """
            
        # Parcours de chaque nom de dimension dans l'agencement
        for dimension_name in arrangement['dimension']:
            # Si la valeur de la dimension est une liste et si elle est vide
            if isinstance(arrangement['dimension'][dimension_name]['values'], list) and len(arrangement['dimension'][dimension_name]['values']) == 0:
                # Ajout de la dimension et de son tableau numpy de valeurs dans le dataset xarray où chaque valeur correspond à un indice de ligne du dataframe
                self.xarray_dataset.coords[dimension_name] = np.arange(0, len(self.dataframe.index))
            # Si la valeur de la dimension est une liste et si elle contient une ou plusieurs valeurs
            elif isinstance(arrangement['dimension'][dimension_name]['values'], list) and len(arrangement['dimension'][dimension_name]['values']) > 0:
                # Ajout de la dimension spécifique et de sa liste de valeurs sous forme de tableau numpy dans le dataset xarray
                self.xarray_dataset.coords[dimension_name] = np.array(arrangement['dimension'][dimension_name]['values'])
        

    def create_xarray_dataset_variable(self: Self, arrangement: dict):
    
        """_summary_
        Création des variables du dataset xarray
        """
    
        # Initialisation d'un dictionnaire dont chacune de ses clés sera le nom d'une variable et dont chacune de ses valeurs sera une liste d'une ou de plusieurs dimensions de la variable si celles-ci contiennent chacune un tableau de valeurs spécifiques
        specific_dimension_variable_dict: dict = {}
    
        # Parcours de chaque nom de variable dans l'agencement
        for variable_name in arrangement['variable']:
            # Initialisation d'une liste de dimensions de la variable contenant les noms des dimensions de la variable
            variable_dimension_list: list = arrangement['variable'][variable_name]['dimension']
            # Si la liste contient 1 dimension
            if len(variable_dimension_list) == 1:
                # Si la dimension de la variable est une liste et si elle est vide
                if isinstance(arrangement['dimension'][variable_dimension_list[0]]['values'], list) and len(arrangement['dimension'][variable_dimension_list[0]]['values']) == 0:
                    # Ajout de la variable et de ses informations dans le dataset xarray
                    self.xarray_dataset[variable_name] = xr.DataArray(np.zeros(len(self.dataframe.index)), dims=variable_dimension_list[0])
                    # Parcours des attributs de la variable
                    for attribute_name, attribute_value in arrangement['variable'][variable_name]['attribute'].items():
                        if attribute_name[0] == ":":
                            # Ajout de l'attribut de la variable et de ses informations dans le dataset xarray
                            self.xarray_dataset[variable_name].attrs[attribute_name[1:]] = attribute_value
                        else:
                            # Ajout de l'attribut de la variable et de ses informations dans le dataset xarray
                            self.xarray_dataset[variable_name].attrs[attribute_name] = attribute_value
                # Si la dimension de la variable est une liste et si elle contient une ou plusieurs valeurs
                elif isinstance(arrangement['dimension'][variable_dimension_list[0]]['values'], list) and len(arrangement['dimension'][variable_dimension_list[0]]['values']) > 0:
                    # Ajout du nom de la seconde dimension à la liste
                    variable_dimension_list.append("index")
                    # Ajout d'un tableau numpy de valeurs dans la liste où chaque valeur correspond à un indice de ligne du dataframe
                    variable_dimension_list.append(np.arange(0, len(self.dataframe.index)))
                    # Initialisation d'une clé de dictionnaire associée à une liste contenant la dimension spécifique
                    specific_dimension_variable_dict[variable_name] = variable_dimension_list
            # Si la liste contient 2 dimensions
            elif len(variable_dimension_list) == 2:
                # Si les deux dimensions de la variable sont des listes et si elles contiennent une ou plusieurs valeurs
                if isinstance(arrangement['dimension'][variable_dimension_list[0]]['values'], list) and isinstance(arrangement['dimension'][variable_dimension_list[1]]['values'], list) and len(arrangement['dimension'][variable_dimension_list[0]]['values']) > 0 and len(arrangement['dimension'][variable_dimension_list[1]]['values']) > 0:
                    # Ajout d'une liste de valeurs sous forme de tableau numpy de la seconde dimension spécifique à la liste
                    variable_dimension_list.append(np.array(arrangement['dimension'][variable_dimension_list[1]]['values']))
                    # Initialisation d'une clé de dictionnaire associée à une liste contenant la dimension spécifique
                    specific_dimension_variable_dict[variable_name] = variable_dimension_list
            
        # Si le dictionnaire des variables de dimension spécifique existe
        if specific_dimension_variable_dict:
            self.insert_bidimensional_variable(specific_dimension_variable_dict, arrangement)


    def insert_bidimensional_variable(self: Self, specific_dimension_variable_dict: dict, arrangement: dict):        
            
        """_summary_
        Insertion des variables bidimensionnelles
        """
            
        # Initialisation d'une liste de listes dont chacune contiendra le nom de la dimension spécifique commune à une ou plusieurs variables, le nom de la seconde dimension spécifique et son tableau numpy de valeurs
        common_dimension_list = []
        # Parcours de chaque clé dans le dictionnaire des variables de dimension spécifique
        for specific_dimension_variable_name in specific_dimension_variable_dict:
            # Initialisation d'une variable qui représentera le nombre de listes parcourues dans la liste des dimensions spécifiques communes à une ou plusieurs variables
            list_checked = 0
            # Si la liste des dimensions spécifiques communes à une ou plusieurs variables est vide
            if common_dimension_list == []:
                # Ajout d'une liste contenant le nom de la dimension spécifique commune, le nom de la seconde dimension spécifique et son tableau numpy de valeurs à la liste
                common_dimension_list.append([specific_dimension_variable_dict[specific_dimension_variable_name][0], specific_dimension_variable_dict[specific_dimension_variable_name][1], specific_dimension_variable_dict[specific_dimension_variable_name][2]])
                # Ajout de la seconde dimension spécifique et de son tableau numpy de valeurs dans le dataset xarray
                self.xarray_dataset.coords[specific_dimension_variable_dict[specific_dimension_variable_name][1]] = specific_dimension_variable_dict[specific_dimension_variable_name][2]
            else:
                # Parcours de chaque liste dans la liste des dimensions spécifiques communes à une ou plusieurs variables
                for common_dimension_element in common_dimension_list:
                    # Si l'ordre des deux dimensions spécifiques est différent entre le dictionnaire et la liste
                    if [specific_dimension_variable_dict[specific_dimension_variable_name][0], specific_dimension_variable_dict[specific_dimension_variable_name][1]] != [common_dimension_element[0], common_dimension_element[1]]:
                        # La liste est parcourue
                        list_checked += 1
                # Si toutes les listes de la liste des dimensions spécifiques communes à une ou plusieurs variables ont été parcourues
                if list_checked == len(list(common_dimension_list)):
                    # Ajout d'une liste contenant le nom de la dimension spécifique commune, le nom de la seconde dimension spécifique et son tableau numpy de valeurs
                    common_dimension_list.append([specific_dimension_variable_dict[specific_dimension_variable_name][0], specific_dimension_variable_dict[specific_dimension_variable_name][1], specific_dimension_variable_dict[specific_dimension_variable_name][2]])
                    # Ajout de la seconde dimension spécifique et de son tableau numpy de valeurs dans le dataset xarray
                    self.xarray_dataset.coords[specific_dimension_variable_dict[specific_dimension_variable_name][1]] = specific_dimension_variable_dict[specific_dimension_variable_name][2]
                    
        # Parcours de chaque liste dans la liste des dimensions spécifiques communes à une ou plusieurs variables
        for common_dimension_element in common_dimension_list:
            # Initialisation d'un dictionnaire dont chacune de ses clés sera le nom de la variable de dimension spécifique et dont chacune de ses valeurs sera son nom filtré (composés uniquement de lettres)
            filtered_variable_name_dict = {}
            # Initialisation d'un dictionnaire dont chacune de ses clés sera le nom commun à un ou plusieurs noms de variable filtrés et dont chacune de ses valeurs sera le nombres d'occurrences du nom commun dans le dictionnaire des noms de variable filtrés et le nom de variable de dimension spécifique
            common_filtered_variable_name_dict = {}
            # Parcours de chaque clé dans le dictionnaire des variables de dimension spécifique
            for specific_dimension_variable_name in specific_dimension_variable_dict:
                # Si les deux dimensions spécifiques du dictionnaire sont dans la liste des dimensions spécifiques communes à une ou plusieurs variables
                if specific_dimension_variable_dict[specific_dimension_variable_name][0] == common_dimension_element[0] and specific_dimension_variable_dict[specific_dimension_variable_name][1] == common_dimension_element[1]:
                    # Initialisation d'un indice
                    i = 0
                    # Initialisation d'une liste
                    variable_name_list = re.split(r'[\d\W\s]+', specific_dimension_variable_name)
                    # Tant que l'indice est inférieur à la longueur de la liste
                    while i < len(variable_name_list):
                        # Si la longueur de l'élément de la liste est supérieure à 2 et si l'élément contient des lettres ou des underscores
                        if len(variable_name_list[i]) > 2 and bool(re.match(r'^[a-zA-Z_]*$', variable_name_list[i])) == True:
                            # Filtration pour ne garder que le mot
                            variable_name_list[0] = variable_name_list[i].strip("_").lower()
                            # Fin de la boucle
                            i = len(variable_name_list)
                        # Sinon
                        else:
                            # Incrémentation de l'indice
                            i += 1
                    # Ajout du premier mot de la liste dans le dictionnaire des noms de variable filtrés
                    filtered_variable_name_dict[specific_dimension_variable_name] = variable_name_list[0]
            
            # Parcours de chaque nom de variable filtré dans le dictionnaire
            for filtered_variable_name in filtered_variable_name_dict:
                # Initialisation d'une variable qui représentera le nombre de clés parcourues dans le dictionnaire des noms communs de variable
                key_checked = 0
                # Si le dictionnaire des noms communs de variable est vide
                if common_filtered_variable_name_dict == {}:
                    # Initialisation de la clé du dictionnaire associée au nombre d'occurrences du nom de la variable filtré dans le dictionnaire et au nom de la variable de dimension spécifique
                    common_filtered_variable_name_dict[filtered_variable_name_dict[filtered_variable_name]] = [list(filtered_variable_name_dict.values()).count(filtered_variable_name_dict[filtered_variable_name]), filtered_variable_name]
                # Sinon
                else:
                    # Parcours de chaque clé du dictionnaire des noms communs de variable
                    for common_filtered_variable_name in common_filtered_variable_name_dict:
                        # Si le nom de variable filtré n'est pas la clé
                        if filtered_variable_name_dict[filtered_variable_name] != common_filtered_variable_name:
                            # La clé est parcourue
                            key_checked += 1
                    # Si toutes les clés du dictionnaire des noms communs de variable ont été parcourues
                    if key_checked == len(list(common_filtered_variable_name_dict.keys())):
                        # Initialisation de la clé du dictionnaire associée au nombre d'occurrences du nom de la variable filtré dans le dictionnaire et au nom de la variable de dimension spécifique
                        common_filtered_variable_name_dict[filtered_variable_name_dict[filtered_variable_name]] = [list(filtered_variable_name_dict.values()).count(filtered_variable_name_dict[filtered_variable_name]), filtered_variable_name]

            # Parcours de chaque clé du dictionnaire des noms communs de variable
            for common_filtered_variable_name in common_filtered_variable_name_dict:
                # Initialisation d'une liste de tableaux numpy de valeurs d'une variable
                variable_array_list = []
                # Si le nombre d'occurrences du nom commun est égal au nombre de valeurs présentes dans la liste de valeurs de la dimension spécifique ou s'il est égal à 1
                if common_filtered_variable_name_dict[common_filtered_variable_name][0] == len(arrangement['dimension'][common_dimension_element[0]]['values']) or common_filtered_variable_name_dict[common_filtered_variable_name][0] == 1:
                    # Parcours du nombre d'occurrences
                    for i in range(0, len(arrangement['dimension'][common_dimension_element[0]]['values'])):
                        # Ajout d'un tableau numpy de zéros de la longueur de la taille du tableau numpy de la deuxième dimension spécifique
                        variable_array_list.append(np.zeros(common_dimension_element[2].shape[0]))
                    # Combinaison de N tableaux numpy de zéros, où N représente le nombre de valeurs dans la liste de valeurs de la dimension spécifique
                    combined_variable_array = np.vstack(variable_array_list)
                    # Ajout de la variable et de ses informations dans le dataset xarray
                    self.xarray_dataset[common_filtered_variable_name + "_" + common_dimension_element[0].lower() + common_dimension_element[1].lower()] = xr.DataArray(combined_variable_array, dims=[common_dimension_element[0], common_dimension_element[1]])
                    # Parcours des attributs de la première variable de dimension spécifique
                    for attribute_name, attribute_value in arrangement['variable'][common_filtered_variable_name_dict[common_filtered_variable_name][1]]['attribute'].items():
                        if attribute_name[0] == ":":
                            # Ajout de l'attribut de la variable et de ses informations dans le dataset xarray
                            self.xarray_dataset[common_filtered_variable_name + "_" + common_dimension_element[0].lower() + common_dimension_element[1].lower()].attrs[attribute_name[1:]] = attribute_value
                        else:
                            # Ajout de l'attribut de la variable et de ses informations dans le dataset xarray
                            self.xarray_dataset[common_filtered_variable_name + "_" + common_dimension_element[0].lower() + common_dimension_element[1].lower()].attrs[attribute_name] = attribute_value


    def create_xarray_dataset_global_attribute(self: Self, arrangement: dict):
    
        """_summary_
        Création des attributs globaux du dataset xarray
        """
    
        # Parcours de chaque nom d'attribut global dans l'agencement
        for global_attribute_name in arrangement['global_attribute']:
            if global_attribute_name[0] == ":":
                # Ajout de l'attribut global et de ses informations dans le dataset xarray
                self.xarray_dataset.attrs[global_attribute_name[1:]] = arrangement['global_attribute'][global_attribute_name]
            else:
                # Ajout de l'attribut global et de ses informations dans le dataset xarray
                self.xarray_dataset.attrs[global_attribute_name] = arrangement['global_attribute'][global_attribute_name]
    
    
    def check_dataframe_integrity(self: Self):
        
        """_summary_
        Vérification de l'intégrité du dataframe
        """
        
        # Si le dataframe est vide
        if self.dataframe.empty:
            if self.controleurlogs != None:
                self.controleurlogs.add_log("Empty dataframe.\n")
                self.controleurlogs.add_colored_log("Empty dataframe.\n", "red")
            self.dataframe = pd.DataFrame()
        # Sinon
        else:
            # Parcours de chaque clé du dataset xarray pour la colonne du dataframe
            for key in list(self.xarray_dataset.data_vars.keys()):
                # Initialisation d'une liste qui contiendra des listes de noms de colonne possibles à chaque nom de colonne du dataframe
                column_name_list = []
                # Initialisation d'une liste qui contiendra les premiers indices des lignes de la colonne de la deuxième dimension de la variable qui contiennent les valeurs de la deuxième dimension
                index_list = []
                # Initialisation d'une variable qui représentera le nombre de listes de noms de colonne possibles vérifiées
                list_checked = 0
                # Parcours de chaque colonne du dataframe
                for column in self.dataframe.columns:
                    # Si le nom de la colonne du dataframe filtré ne commence pas ou ne finit pas par un mot de la première liste du catalogue
                    if [word for word in outilsProcessing.datetime_catalog[0] if not re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(word) and not re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(word)]:
                        # Si les noms de la variable du fichier netCDF sont renseignés
                        if 'long_name' in self.xarray_dataset[key].attrs.keys() and 'standard_name' in self.xarray_dataset[key].attrs.keys() and 'sdn_parameter_name' in self.xarray_dataset[key].attrs.keys():
                            # Si le type des données du fichier netCDF est bien précisé
                            if 'dtype' in self.xarray_dataset[key].attrs.keys() and hasattr(self.dataframe[column], 'dtype'):
                                # Si le tableau de données est de dimension 1 et si un des mots de la liste des noms possibles de la clé est le nom de la colonne du dataframe
                                if self.xarray_dataset[key].values.ndim == 1 and outilsProcessing.check_names([self.xarray_dataset[key].attrs['standard_name'], self.xarray_dataset[key].attrs['long_name'], self.xarray_dataset[key].attrs['sdn_parameter_name'], self.xarray_dataset[key].attrs['column_name']], column) == True:
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
                                                    if self.controleurlogs != None:
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
                                                    if self.controleurlogs != None:
                                                        self.controleurlogs.add_log("Longitude values are not between -180 and 180.\n")
                                                        self.controleurlogs.add_colored_log("Longitude values are not between -180 and 180.\n", "red")
                                            # Sinon la clé est une autre clé
                                            else:
                                                # Ajout des données de la colonne du dataframe dans le tableau de données associé à la clé
                                                self.xarray_dataset[key].values = np.array(self.dataframe[column].iloc[:].tolist())
                                        # Sinon
                                        else:
                                            if self.controleurlogs != None:
                                                self.controleurlogs.add_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n")
                                                self.controleurlogs.add_colored_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n", "red")
                                    # Sinon
                                    else:
                                        if self.controleurlogs != None:
                                            self.controleurlogs.add_log("Data type in column " + column + " : " + str(self.dataframe[column].dtype) + " does not match the type of the variable : " + key + " : " + self.xarray_dataset[key].attrs['dtype'] + " . Data will be not selected.\n")
                                            self.controleurlogs.add_colored_log("Data type in column " + column + " : " + str(self.dataframe[column].dtype) + " does not match the type of the variable : " + key + " : " + self.xarray_dataset[key].attrs['dtype'] + " . Data will be not selected.\n", "red")
                                # Si le tableau de données est de dimension 2, si le nom de la colonne filtré commence ou se termine par la clé
                                elif self.xarray_dataset[key].values.ndim == 2 and (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower())):
                                    # Si la liste de données de la colonne du dataframe contient au minimum 10 données
                                    if len(self.dataframe[column].iloc[:].tolist()) >= 10:
                                        # Si la liste existe
                                        if column_name_list:
                                            # Pour chaque liste de la liste
                                            for part in column_name_list:
                                                # Si le nom de la colonne du dataframe n'est pas dans la liste
                                                if column not in part:
                                                    # La liste est vérifiée
                                                    list_checked += 1
                                            # Si toutes les listes ont été vérifiées
                                            if list_checked == len(column_name_list):
                                                # Réinitialisation de la variable
                                                list_checked = 0
                                                # Si la clé est latitude
                                                if key == 'latitude':
                                                    # Si les données de la colonne du dataframe sont des valeurs de latitude
                                                    if all(self.dataframe[column].between(-90.0, 90.0)):
                                                        # Initialisation de l'indice de la colonne du dataframe
                                                        index: int = outilsProcessing.get_index_as_int(self.dataframe, column)
                                                        # Si la deuxième dimension de la variable n'est pas 'index' et si la longueur est inférieure au nombre de lignes du dataframe
                                                        if self.xarray_dataset[key].dims[1] != "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] < len(self.dataframe.index):
                                                            # Initialisation du nom de la deuxième dimension de la variable
                                                            name = ""
                                                            # Parcours de chaque colonne du dataframe
                                                            for col in self.dataframe.columns:
                                                                # Si le nom de colonne commence ou se termine par la deuxième dimension de la variable
                                                                if (re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().startswith(str(self.xarray_dataset[key].dims[1]).lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().endswith(str(self.xarray_dataset[key].dims[1]).lower())) == True:
                                                                    name = col
                                                                    # Fin de boucle
                                                                    break
                                                            # Si le nom de la deuxième dimension existe
                                                            if name:
                                                                # Parcours de chaque valeur dans la liste des valeurs de la deuxième dimension de la variable
                                                                for value in self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist():
                                                                    # Si la liste contient des éléments
                                                                    if len(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()) > 0:
                                                                        # Ajout du premier indice de la ligne de la colonne de la deuxième dimension de la variable qui vaut l'élément de la liste à la liste
                                                                        index_list.append(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()[0])
                                                        # Si la deuxième dimension de la variable est 'index' et si la longueur est égale au nombre de lignes du dataframe
                                                        elif self.xarray_dataset[key].dims[1] == "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] == len(self.dataframe.index):
                                                            # Initialisation d'une liste d'indices de ligne
                                                            index_list = [i for i in range(0, len(self.dataframe.index))]
                                                        # Si les tableaux numpy sont de même taille et si la longueur de la liste des indices est de la même taille que la longueur du tableau de la deuxième dimension de la variable
                                                        if self.xarray_dataset[key].values.shape == np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]])).shape and len(index_list) == len(self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist()):
                                                            # Ajout des données des colonnes du dataframe dans le tableau de données associé à la clé
                                                            self.xarray_dataset[key].values = np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]]))
                                                        # Si la liste des noms de colonne possibles n'est pas dans la liste
                                                        if [column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))] not in column_name_list:
                                                            # Ajout de la liste
                                                            column_name_list.append([column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))])
                                                    # Sinon
                                                    else:
                                                        if self.controleurlogs != None:
                                                            self.controleurlogs.add_log("Latitude values are not between -90 and 90.\n")
                                                            self.controleurlogs.add_colored_log("Latitude values are not between -90 and 90.\n", "red")
                                                # Si la clé est longitude
                                                elif key == 'longitude':
                                                    # Si les données de la colonne du dataframe sont des valeurs de longitude
                                                    if all(self.dataframe[column].between(-180.0, 180.0)):    
                                                        # Initialisation de l'indice de la colonne du dataframe
                                                        index: int = outilsProcessing.get_index_as_int(self.dataframe, column)
                                                        # Si la deuxième dimension de la variable n'est pas 'index' et si la longueur est inférieure au nombre de lignes du dataframe
                                                        if self.xarray_dataset[key].dims[1] != "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] < len(self.dataframe.index):
                                                            # Initialisation du nom de la deuxième dimension de la variable
                                                            name = ""
                                                            # Parcours de chaque colonne du dataframe
                                                            for col in self.dataframe.columns:
                                                                # Si le nom de colonne commence ou se termine par la deuxième dimension de la variable
                                                                if (re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().startswith(str(self.xarray_dataset[key].dims[1]).lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().endswith(str(self.xarray_dataset[key].dims[1]).lower())) == True:
                                                                    name = col
                                                                    # Fin de boucle
                                                                    break
                                                            # Si le nom de la deuxième dimension existe
                                                            if name:
                                                                # Parcours de chaque valeur dans la liste des valeurs de la deuxième dimension de la variable
                                                                for value in self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist():
                                                                    # Si la liste contient des éléments
                                                                    if len(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()) > 0:
                                                                        # Ajout du premier indice de la ligne de la colonne de la deuxième dimension de la variable qui vaut l'élément de la liste à la liste
                                                                        index_list.append(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()[0])
                                                        # Si la deuxième dimension de la variable est 'index' et si la longueur est égale au nombre de lignes du dataframe
                                                        elif self.xarray_dataset[key].dims[1] == "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] == len(self.dataframe.index):
                                                            # Initialisation d'une liste d'indices de ligne
                                                            index_list = [i for i in range(0, len(self.dataframe.index))]
                                                        # Si les tableaux numpy sont de même taille et si la longueur de la liste des indices est de la même taille que la longueur du tableau de la deuxième dimension de la variable
                                                        if self.xarray_dataset[key].values.shape == np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]])).shape and len(index_list) == len(self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist()):
                                                            # Ajout des données des colonnes du dataframe dans le tableau de données associé à la clé
                                                            self.xarray_dataset[key].values = np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]]))
                                                        # Si la liste des noms de colonne possibles n'est pas dans la liste
                                                        if [column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))] not in column_name_list:
                                                            # Ajout de la liste
                                                            column_name_list.append([column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))])
                                                    # Sinon
                                                    else:
                                                        if self.controleurlogs != None:
                                                            self.controleurlogs.add_log("Longitude values are not between -180 and 180.\n")
                                                            self.controleurlogs.add_colored_log("Longitude values are not between -180 and 180.\n", "red")
                                                # Sinon
                                                else:
                                                    # Initialisation de l'indice de la colonne du dataframe
                                                    index: int = outilsProcessing.get_index_as_int(self.dataframe, column)
                                                    # Si la deuxième dimension de la variable n'est pas 'index' et si la longueur est inférieure au nombre de lignes du dataframe
                                                    if self.xarray_dataset[key].dims[1] != "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] < len(self.dataframe.index):
                                                        # Initialisation du nom de la deuxième dimension de la variable
                                                        name = ""
                                                        # Parcours de chaque colonne du dataframe
                                                        for col in self.dataframe.columns:
                                                            # Si le nom de colonne commence ou se termine par la deuxième dimension de la variable
                                                            if (re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().startswith(str(self.xarray_dataset[key].dims[1]).lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().endswith(str(self.xarray_dataset[key].dims[1]).lower())) == True:
                                                                name = col
                                                                # Fin de boucle
                                                                break
                                                        # Si le nom de la deuxième dimension existe
                                                        if name:
                                                            # Parcours de chaque valeur dans la liste des valeurs de la deuxième dimension de la variable
                                                            for value in self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist():
                                                                # Si la liste contient des éléments
                                                                if len(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()) > 0:
                                                                    # Ajout du premier indice de la ligne de la colonne de la deuxième dimension de la variable qui vaut l'élément de la liste à la liste
                                                                    index_list.append(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()[0])
                                                    # Si la deuxième dimension de la variable est 'index' et si la longueur est égale au nombre de lignes du dataframe
                                                    elif self.xarray_dataset[key].dims[1] == "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] == len(self.dataframe.index):
                                                        # Initialisation d'une liste d'indices de ligne
                                                        index_list = [i for i in range(0, len(self.dataframe.index))]
                                                    # Si les tableaux numpy sont de même taille et si la longueur de la liste des indices est de la même taille que la longueur du tableau de la deuxième dimension de la variable
                                                    if self.xarray_dataset[key].values.shape == np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]])).shape and len(index_list) == len(self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist()):
                                                        # Ajout des données des colonnes du dataframe dans le tableau de données associé à la clé
                                                        self.xarray_dataset[key].values = np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]]))
                                                    # Si la liste des noms de colonne possibles n'est pas dans la liste
                                                    if [column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))] not in column_name_list:
                                                        # Ajout de la liste
                                                        column_name_list.append([column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))])
                                            # Sinon
                                            else:
                                                # Réinitialisation de la variable
                                                list_checked = 0
                                        # Sinon
                                        else:
                                            # Initialisation de l'indice de la colonne du dataframe
                                            index: int = outilsProcessing.get_index_as_int(self.dataframe, column)
                                            # Si la deuxième dimension de la variable n'est pas 'index' et si la longueur est inférieure au nombre de lignes du dataframe
                                            if self.xarray_dataset[key].dims[1] != "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] < len(self.dataframe.index) and key.split("_")[0]:
                                                # Initialisation du nom de la deuxième dimension de la variable
                                                name = ""
                                                # Parcours de chaque colonne du dataframe
                                                for col in self.dataframe.columns:
                                                    # Si le nom de colonne commence ou se termine par la deuxième dimension de la variable
                                                    if (re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().startswith(str(self.xarray_dataset[key].dims[1]).lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', col.split(",")[0].strip("_")).replace(' ','_').lower().endswith(str(self.xarray_dataset[key].dims[1]).lower())) == True:
                                                        name = col
                                                        # Fin de boucle
                                                        break
                                                # Si le nom de la deuxième dimension existe
                                                if name:
                                                    # Parcours de chaque valeur dans la liste des valeurs de la deuxième dimension de la variable
                                                    for value in self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist():
                                                        # Si la liste contient des éléments
                                                        if len(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()) > 0:
                                                            # Ajout du premier indice de la ligne de la colonne de la deuxième dimension de la variable qui vaut l'élément de la liste à la liste
                                                            index_list.append(self.dataframe.index[self.dataframe[name] == type(self.dataframe.iloc[0][name])(value)].tolist()[0])
                                            # Si la deuxième dimension de la variable est 'index' et que la longueur est égale au nombre de lignes du dataframe
                                            elif self.xarray_dataset[key].dims[1] == "index" and self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.shape[0] == len(self.dataframe.index):
                                                # Initialisation d'une liste d'indices de ligne
                                                index_list = [i for i in range(0, len(self.dataframe.index))]
                                            # Si les tableaux numpy sont de même taille et si la longueur de la liste des indices est de la même taille que la longueur du tableau de la deuxième dimension de la variable
                                            if self.xarray_dataset[key].values.shape == np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]])).shape and len(index_list) == len(self.xarray_dataset[self.xarray_dataset[key].dims[1]].values.tolist()):
                                                # Ajout des données des colonnes du dataframe dans le tableau de données associé à la clé
                                                self.xarray_dataset[key].values = np.transpose(np.array(self.dataframe.iloc[index_list, index: index + self.xarray_dataset[key].values.shape[0]]))
                                            # Ajout de la liste
                                            column_name_list.append([column for column in self.dataframe.columns if (re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(key.split('_')[0].lower()) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(key.split('_')[0].lower()))])
                                    # Sinon
                                    else:
                                        if self.controleurlogs != None:
                                            self.controleurlogs.add_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n")
                                            self.controleurlogs.add_colored_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n", "red")
                            # Sinon
                            else:
                                if self.controleurlogs != None:
                                    self.controleurlogs.add_log("Data type in column " + column + " not specified for the variable " + key + " . Data will be not selected.\n")
                                    self.controleurlogs.add_colored_log("Data type in column " + column + " not specified for the variable " + key + " . Data will be not selected.\n", "red")
                        # Sinon
                        else:
                            if self.controleurlogs != None:
                                self.controleurlogs.add_log("Unknown names for the variable " + key + " . Data will be not selected.\n")
                                self.controleurlogs.add_colored_log("Unknown names for the variable " + key + " . Data will be not selected.\n", "red")


    def check_datetime_format(self: Self):
        
        """_summary_
        Reformatage des dates
        """
        
        # Si le dataframe est vide
        if self.dataframe.empty:
            if self.controleurlogs != None:
                self.controleurlogs.add_log("Empty dataframe.\n")
                self.controleurlogs.add_colored_log("Empty dataframe.\n", "red")
            self.dataframe = pd.DataFrame()
        # Sinon
        else:
            # Si le catalogue a une liste de données temporelles
            if len(outilsProcessing.datetime_catalog) > 1:
                # Technique de slicing pour retirer la liste de données temporelles
                outilsProcessing.datetime_catalog = outilsProcessing.datetime_catalog[:-1]
            # Si la variable 'time' est présente dans le dataset xarray
            if 'time' in list(self.xarray_dataset.data_vars.keys()):
                # Parcours de chaque colonne du dataframe
                for column in self.dataframe.columns:
                    # Si le nom de la colonne du dataframe filtré ne commence pas ou ne finit pas par un mot de la première liste du catalogue et si le catalogue ne contient pas plus de 3 listes
                    if [word for word in outilsProcessing.datetime_catalog[0] if re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith(word) or re.sub(r'[^a-zA-Z/:.-_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith(word)] and len(outilsProcessing.datetime_catalog) < 3:
                        # Si la liste de données de la colonne du dataframe contient au minimum 10 données
                        if len(self.dataframe[column].iloc[:].tolist()) >= 10:
                            # Ajout des données de la colonne du dataframe dans le catalogue
                            outilsProcessing.datetime_catalog.append(self.dataframe[column].iloc[:].tolist())
                        # Sinon
                        else:
                            if self.controleurlogs != None:
                                self.controleurlogs.add_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n")
                                self.controleurlogs.add_colored_log("Less than 10 data are present in column " + column + " . Data will be not selected.\n", "red")
                # Si le catalogue contient une liste de noms possibles pour la variable datetime et une liste de données temporelles
                if len(outilsProcessing.datetime_catalog) == 2:
                    # Parcours de la première donnée temporelle jusqu'à la dernière dans la liste
                    for i in range(0, len(outilsProcessing.datetime_catalog[1])):
                        # Si la donnée temporelle est au format timestamp
                        if isinstance(outilsProcessing.datetime_catalog[1][i], pd.Timestamp):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                        # Si la donnée temporelle est au format datetime
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], datetime):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))   
                        # Si la donnée temporelle est au format date
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], date):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                        # Si la donnée temporelle est au format time
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], time):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%H:%M:%S"))    
                        # Si la donnée temporelle est une chaîne de caractères
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], str):
                            # Si la donnée temporelle n'est pas au format 'YYYY-MM-DD HH:MM:SS', 'YYYY-MM-DDTHH:MM:SS', 'YYYY-MM-DD' et 'HH:MM:SS'
                            if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1]) (?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])T(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[1][i])) == False and bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[1][i])) == False:
                                # La donnée temporelle est nulle
                                outilsProcessing.datetime_catalog[1][i] = str('')
                            # Si la donnée temporelle est au format 'YYYY-MM-DD HH:MM:SS.SSS', 'YYYY-MM-DDTHH:MM:SS.SSS' ou 'HH:MM:SS.SSS'
                            elif bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1]) (?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])T(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[1][i])) == True:
                                # Conversion de la donnée temporelle en chaîne de caractères sans les millisecondes
                                outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i][:-4])
                        # Sinon le type de donnée n'est pas correct
                        else:
                            if self.controleurlogs != None:
                                self.controleurlogs.add_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n")
                                self.controleurlogs.add_colored_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n", "red")
                            # La donnée temporelle est nulle
                            outilsProcessing.datetime_catalog[1][i] = str('')
                    # Ajout des données temporelles de la liste dans le tableau de données associé à la clé
                    self.xarray_dataset['time'].values = np.array(outilsProcessing.datetime_catalog[1])
                    # Technique de slicing pour retirer la liste de données temporelles
                    outilsProcessing.datetime_catalog = outilsProcessing.datetime_catalog[:-1]
                # Si le catalogue contient une liste de noms possibles pour la variable datetime et 2 listes de données temporelles
                elif len(outilsProcessing.datetime_catalog) == 3:
                    # Parcours de la première donnée temporelle jusqu'à la dernière dans la liste
                    for i in range(0, len(outilsProcessing.datetime_catalog[1])):
                        # Si la donnée temporelle est au format timestamp
                        if isinstance(outilsProcessing.datetime_catalog[1][i], pd.Timestamp):
                            # Si la donnée temporelle est au format 'HH:MM:SS'
                            if str(outilsProcessing.datetime_catalog[1][i].strftime("%H:%M:%S")) == '00:00:00':
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                                # Si la donnée temporelle de la deuxième liste est au format time
                                if isinstance(outilsProcessing.datetime_catalog[2][i], time):
                                    # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                    outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i].strftime("%H:%M:%S"))
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                # Si la donnée temporelle de la deuxième liste est au format datetime
                                elif isinstance(outilsProcessing.datetime_catalog[2][i], datetime):
                                    # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                    outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%H:%M:%S"))
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                                elif isinstance(outilsProcessing.datetime_catalog[2][i], str):
                                    # Si la donnée temporelle n'est pas au format 'HH:MM:SS'
                                    if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[2][i])) == False:
                                        # La donnée temporelle est nulle
                                        outilsProcessing.datetime_catalog[2][i] = str('')
                                        # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                        outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                    # Si la donnée temporelle est au format 'HH:MM:SS.SSS'
                                    elif bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[2][i])) == True:
                                        # Conversion de la donnée temporelle en chaîne de caractères sans les millisecondes
                                        outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i][:-4])
                                        # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                        outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                # Sinon le type de donnée n'est pas correct
                                else:
                                    if self.controleurlogs != None:
                                        self.controleurlogs.add_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n")
                                        self.controleurlogs.add_colored_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n", "red")
                                    # La donnée temporelle est nulle
                                    outilsProcessing.datetime_catalog[1][i] = str('')
                            # Sinon la donnée temporelle est dans un autre format
                            else:
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                        # Si la donnée temporelle est au format datetime
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], datetime):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d %H:%M:%S"))
                        # Si la donnée temporelle est au format date
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], date):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%Y-%m-%d"))
                            # Si la donnée temporelle de la deuxième liste est au format time
                            if isinstance(outilsProcessing.datetime_catalog[2][i], time):
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i].strftime("%H:%M:%S"))   
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                            # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                            elif isinstance(outilsProcessing.datetime_catalog[2][i], str):
                                # Si la donnée temporelle est au format 'HH:MM:SS'
                                if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[2][i])) == True:
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                # Si la donnée temporelle est au format 'HH:MM:SS.SSS'
                                elif bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[2][i])) == True:
                                    # Conversion de la donnée temporelle en chaîne de caractères sans les millisecondes
                                    outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i][:-4])
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                            # Si la donnée temporelle de la deuxième liste est au format timestamp
                            elif isinstance(outilsProcessing.datetime_catalog[2][i], pd.Timestamp):
                                # Si la donnée temporelle est au format 'HH:MM:SS'
                                if str(outilsProcessing.datetime_catalog[2][i].strftime("%H:%M:%S")) == '00:00:00':
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                        # Si la donnée temporelle est au format time
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], time):
                            # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                            outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i].strftime("%H:%M:%S"))
                            # Si la donnée temporelle de la deuxième liste est au format date
                            if isinstance(outilsProcessing.datetime_catalog[2][i], date):
                                # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i].strftime("%Y-%m-%d"))   
                                # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[2][i] + " " + outilsProcessing.datetime_catalog[1][i]
                            # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                            elif isinstance(outilsProcessing.datetime_catalog[2][i], str):
                                # Si la donnée temporelle est une chaîne de caractères au format 'YYYY-MM-DD', 'YYYY/MM/DD', 'DD-MM-YYYY' ou 'DD/MM/YYYY'
                                if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[2][i])) == True or bool(re.match(r'^(?:\d{4})/(?:0[1-9]|1[0-2])/(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[2][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])-(?:0[1-9]|1[0-2])-(?:\d{4})$', outilsProcessing.datetime_catalog[2][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])/(?:0[1-9]|1[0-2])/(?:\d{4})$', outilsProcessing.datetime_catalog[2][i])) == True:
                                    # Si la donnée temporelle est une chaîne de caractères au format 'YYYY/MM/DD', 'DD-MM-YYYY' ou 'DD/MM/YYYY'
                                    if bool(re.match(r'^(?:\d{4})/(?:0[1-9]|1[0-2])/(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[2][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])-(?:0[1-9]|1[0-2])-(?:\d{4})$', outilsProcessing.datetime_catalog[2][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])/(?:0[1-9]|1[0-2])/(?:\d{4})$', outilsProcessing.datetime_catalog[2][i])) == True:
                                        outilsProcessing.datetime_catalog[2][i] = outilsProcessing.datetime_catalog[2][i].replace('/', '-')
                                        # Conversion de la donnée temporelle en objet datetime
                                        outilsProcessing.datetime_catalog[2][i] = datetime.strptime(outilsProcessing.datetime_catalog[2][i], '%d-%m-%Y')
                                        # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                        outilsProcessing.datetime_catalog[2][i] = outilsProcessing.datetime_catalog[2][i].strftime('%Y-%m-%d')
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[2][i] + " " + outilsProcessing.datetime_catalog[1][i]
                        # Si la donnée temporelle est une chaîne de caractères
                        elif isinstance(outilsProcessing.datetime_catalog[1][i], str):                
                            # Si la donnée temporelle est une chaîne de caractères au format 'YYYY-MM-DD', 'YYYY/MM/DD', 'DD-MM-YYYY' ou 'DD/MM/YYYY'
                            if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:\d{4})/(?:0[1-9]|1[0-2])/(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])-(?:0[1-9]|1[0-2])-(?:\d{4})$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])/(?:0[1-9]|1[0-2])/(?:\d{4})$', outilsProcessing.datetime_catalog[1][i])) == True:
                                # Si la donnée temporelle est une chaîne de caractères au format 'YYYY/MM/DD', 'DD-MM-YYYY' ou 'DD/MM/YYYY'
                                if bool(re.match(r'^(?:\d{4})/(?:0[1-9]|1[0-2])/(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])-(?:0[1-9]|1[0-2])-(?:\d{4})$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:0[1-9]|[1-2][0-9]|3[0-1])/(?:0[1-9]|1[0-2])/(?:\d{4})$', outilsProcessing.datetime_catalog[1][i])) == True:
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i].replace('/', '-')
                                    # Conversion de la donnée temporelle en objet datetime
                                    outilsProcessing.datetime_catalog[1][i] = datetime.strptime(outilsProcessing.datetime_catalog[1][i], '%d-%m-%Y')
                                    # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i].strftime('%Y-%m-%d')
                                # Si la donnée temporelle de la deuxième liste est au format time
                                if isinstance(outilsProcessing.datetime_catalog[2][i], time):
                                    # Conversion de la donnée temporelle en chaîne de caractères au format 'HH:MM:SS'
                                    outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i].strftime("%H:%M:%S"))   
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                                elif isinstance(outilsProcessing.datetime_catalog[2][i], str):
                                    # Si la donnée temporelle de la deuxième liste est une chaîne de caractères au format 'HH:MM:SS'
                                    if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[2][i])) == True:
                                        # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                        outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                                    # Si la donnée temporelle de la deuxième liste est au format 'HH:MM:SS.SSS'
                                    elif bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[2][i])) == True:
                                        # Conversion de la donnée temporelle en chaîne de caractères sans les millisecondes
                                        outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i][:-4])
                                        # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                        outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[1][i] + " " + outilsProcessing.datetime_catalog[2][i]
                            # Si la donnée temporelle est une chaîne de caractères au format 'HH:MM:SS' ou 'HH:MM:SS.SSS'
                            elif bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[1][i])) == True or bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[1][i])) == True:
                                # Si la donnée temporelle est une chaîne de caractères au format 'HH:MM:SS.SSS'
                                if bool(re.match(r'^(?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)\.\d{3}$', outilsProcessing.datetime_catalog[1][i])) == True:
                                    # Conversion de la donnée temporelle en chaîne de caractères sans les millisecondes
                                    outilsProcessing.datetime_catalog[1][i] = str(outilsProcessing.datetime_catalog[1][i][:-4])
                                # Si la donnée temporelle de la deuxième liste est au format date
                                if isinstance(outilsProcessing.datetime_catalog[2][i], date):
                                    # Conversion de la donnée temporelle en chaîne de caractères au format 'YYYY-MM-DD'
                                    outilsProcessing.datetime_catalog[2][i] = str(outilsProcessing.datetime_catalog[2][i].strftime("%Y-%m-%d"))   
                                    # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                    outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[2][i] + " " + outilsProcessing.datetime_catalog[1][i]
                                # Si la donnée temporelle de la deuxième liste est une chaîne de caractères
                                elif isinstance(outilsProcessing.datetime_catalog[2][i], str):
                                    # Si la donnée temporelle de la deuxième liste est une chaîne de caractères au format 'YYYY-MM-DD'
                                    if bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1])$', outilsProcessing.datetime_catalog[2][i])) == True:
                                        # Concaténation pour obtenir une chaîne de caractères au format 'YYYY-MM-DD HH:MM:SS'
                                        outilsProcessing.datetime_catalog[1][i] = outilsProcessing.datetime_catalog[2][i] + " " + outilsProcessing.datetime_catalog[1][i]
                            # Si la donnée temporelle est une chaîne de caractères qui n'est pas au format 'YYYY-MM-DD HH:MM:SS'
                            elif bool(re.match(r'^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[1-2][0-9]|3[0-1]) (?:[01]\d|2[0-3]):(?:[0-5]\d):(?:[0-5]\d)$', outilsProcessing.datetime_catalog[1][i])) == False:
                                if self.controleurlogs != None:
                                    self.controleurlogs.add_log("Date format not recognized for " + str(outilsProcessing.datetime_catalog[1][i]) + " . Data will be cleared.\n")
                                    self.controleurlogs.add_colored_log("Date format not recognized for " + str(outilsProcessing.datetime_catalog[1][i]) + " . Data will be cleared.\n", "red")
                                # La donnée temporelle est nulle
                                outilsProcessing.datetime_catalog[1][i] = str('')
                        # Sinon le type de donnée n'est pas correct
                        else:
                            if self.controleurlogs != None:
                                self.controleurlogs.add_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n")
                                self.controleurlogs.add_colored_log("Incorrect data type for " + str(outilsProcessing.datetime_catalog[1][i]) + " : " + str(type(outilsProcessing.datetime_catalog[1][i])) + " . Data will be cleared.\n", "red")
                            # La donnée temporelle est nulle
                            outilsProcessing.datetime_catalog[1][i] = str('') 
                    # Technique de slicing pour retirer toutes les listes de données temporelles sauf la première liste de données temporelles
                    outilsProcessing.datetime_catalog = outilsProcessing.datetime_catalog[:-(len(outilsProcessing.datetime_catalog)-2)]
                    # Ajout des données temporelles de la liste dans le tableau de données associé à la clé
                    self.xarray_dataset['time'].values = np.array(outilsProcessing.datetime_catalog[1])
            # Sinon la variable 'time' n'existe pas
            else:
                if self.controleurlogs != None:
                    self.controleurlogs.add_log("Please, create 'time' variable with no value to process dates.\n")
                    self.controleurlogs.add_colored_log("Please, create 'time' variable with no value to process dates.\n", "red")


    def adapt_xarray_dataset(self: Self):
        
        """_summary_
        Adaptation du dataset xarray
        """
        
        # Parcours de chaque clé du dataset xarray
        for key in list(self.xarray_dataset.data_vars.keys()):
            if 'column_name' in self.xarray_dataset[key].attrs.keys():
                del self.xarray_dataset[key].attrs['column_name']
            # Si le tableau de données de la clé est vide
            if np.all(self.xarray_dataset[key].values == 0) or np.all(self.xarray_dataset[key].values == None) or np.all(self.xarray_dataset[key].values == "") or np.all(self.xarray_dataset[key].values != self.xarray_dataset[key].values):
                # Suppression des attributs de la variable
                self.xarray_dataset[key].attrs.clear()
                # Suppression de la variable
                del self.xarray_dataset[key]
    

    def create_xarray_dataset(self: Self):
        
        """_summary_
        Création du dataset xarray
        """
        
        self.xarray_dataset = xr.Dataset()
        
        # Chargement du fichier JSON
        with open(self.arrangement_path, "r") as f:
            arrangement = json.load(f)
        
        # Exemple de jeu de données
        dataset = [
            {'data': np.random.normal(loc=20, scale=5, size=100), 'label': 'temperature'},
            {'data': np.random.normal(loc=35, scale=10, size=100), 'label': 'salinity'},
            {'data': np.random.normal(loc=100, scale=50, size=100), 'label': 'depth'},
            {'data': np.random.normal(loc=10, scale=3, size=100), 'label': 'longitude'},
            {'data': np.random.normal(loc=50, scale=20, size=100), 'label': 'latitude'}
        ]

        # Si tous les noms de colonne du dataframe sont des chaînes de caractères
        if all(isinstance(column, str) for column in self.dataframe.columns) == True: 
            # Suppression des colonnes duppliquées du dataframe
            self.dataframe = self.dataframe.drop(columns = self.dataframe.columns[self.dataframe.columns.duplicated()])

        # Si une ou plusieurs colonnes du dataframe pandas sont sans nom
        if self.activation == True:
            # Entraînement du modèle
            model, X, y = outilsProcessing.train_model(dataset)
            # Renommage des colonnes sans titre du dataframe
            self.dataframe = outilsProcessing.rename_dataframe_columns(model, self.dataframe)
        
        self.create_xarray_dataset_dimension(arrangement)

        self.create_xarray_dataset_variable(arrangement)
        
        self.create_xarray_dataset_global_attribute(arrangement)
        
        self.check_dataframe_integrity()
        
        self.check_datetime_format()
        
        self.adapt_xarray_dataset()

    
    def get_xarray_dataset(self: Self):
        
        """_summary_
        Retourne le dataset xarray
        Returns:
            _type_: _description_
        """
        
        self.xarray_dataset = outilsProcessing.check_xarray_dataset(self.xarray_dataset)
        
        return self.xarray_dataset


    def __repr__(self: Self):
        
        print(self.xarray_dataset)
        
    
    # Définition des méthodes statiques
    
    
    @staticmethod
    def get_index_as_int(dataframe: pd.DataFrame, column_name: str):
        
        """_summary_
        Obtenir l'indice entier
        Returns:
            _type_: _description_
        """
        
        index = dataframe.columns.get_loc(column_name)
        if isinstance(index, int):
            return index
        elif isinstance(index, slice):
            return 0
        else:
            return int(index[0])
    

    @staticmethod
    def check_xarray_dataset(xarray_dataset: xr.Dataset):
        
        """_summary_
        Vérifie et adapte le dataset xarray
        Returns:
            _type_: _description_
        """
        
        # Initialisation d'un dictionnaire qui contiendra les clés sans caractères spéciaux
        new_key_dict = {}
        # Parcours de chaque clé du dataset xarray
        for key in xarray_dataset.keys():
            # Si la clé contient des caractères spéciaux
            if re.search(r'[^A-Za-z0-9_]', key):
                # Initialisation d'une variable qui contient des lettres, des chiffres ou des underscore
                new_key = re.sub(r'[^A-Za-z0-9_]', '', key)
                # Initialisation de la clé dans le dictionnaire
                new_key_dict[key] = new_key
            # Sinon
            else:
                # Initialisation de la clé dans le dictionnaire
                new_key_dict[key] = key
        
        return xarray_dataset.rename(new_key_dict)
    
    
    @staticmethod
    def check_names(variable_name_list: list[str], column_name: str):
        
        """_summary_
        Vérification des noms de colonne du dataframe
        Returns:
            _type_: _description_
        """
        
        # Si la liste des noms possibles de la variable existe
        if variable_name_list:
            # Parcours de la liste des noms possibles de la variable sauf column_name
            for i in range(0, len(variable_name_list) - 1):
                # Suppression des espaces blancs
                variable_name_list[i] = variable_name_list[i].replace(' ', '_').lower()
                # Si le nom commence par sea_water
                if variable_name_list[i].startswith("sea_water_"):
                    # Suppression de sea_water du nom
                    variable_name_list[i] = variable_name_list[i][len("sea_water_"):]
        
            # Si column_name est le nom de la colonne du dataframe
            if variable_name_list[3] == column_name:
                # Retourne Vrai
                return True
            # Sinon
            else:
                # Initialisation d'un indice
                i = 0
                # Tant que l'indice est inférieur à la longueur de la liste
                while i < len(variable_name_list):
                    # Si le nom de la colonne du dataframe filtré commence ou se termine par l'un des noms possibles de la variable
                    if re.sub(r'[^a-zA-Z0-9\s_]', '', column_name.split(",")[0].strip("_")).replace(' ','_').lower().startswith(variable_name_list[i]) or re.sub(r'[^a-zA-Z0-9\s_]', '', column_name.split(",")[0].strip("_")).replace(' ','_').lower().endswith(variable_name_list[i]):
                        # Fin de la boucle
                        i = len(variable_name_list)
                        # Retourne Vrai
                        return True
                    # Sinon
                    else:
                        # Incrémentation de l'indice
                        i += 1

        # Retourne Faux
        return False    
        

    @staticmethod
    def extract_features(data_list: list):
        
        """_summary_
        Extraction des caractéristiques statistiques d'un tableau numpy de données sous forme d'un ensemble de données
        Returns:
            _type_: _description_
        """
        
        # Initialisation d'un ensemble de données statistique contenant les caractéristiques statistiques d'une série de données
        dataset = {
            # Moyenne
            'mean': np.mean(data_list),
            # Ecart-type
            'std': np.std(data_list),
            # Minimum
            'min': np.min(data_list),
            # Maximum
            'max': np.max(data_list),
            # Domaine de définition
            'range': np.max(data_list) - np.min(data_list),
            # Médiane
            'median': np.median(data_list),
            # 25ème percentile représente les valeurs en-dessous desquelles se trouvent 25% des données d'un ensemble donné
            '25_percentile': np.percentile(data_list, 25),
            # 75ème percentile représente les valeurs en-dessous desquelles se trouvent 75% des données d'un ensemble donné
            '75_percentile': np.percentile(data_list, 75)
        }
        
        # Retourne l'ensemble de données statistique
        return dataset
    
    
    @staticmethod
    def train_model(dataset: list):
        
        """_summary_
        Entraînement d'un modèle RandomForestClassifier 
        Returns:
            _type_: _description_
        """
        
        # Initialisation d'une variable représentant la liste des caractéristiques
        features = []
        # Initialisation d'une variable représentant la liste des labels
        labels = []
        # Pour chaque clé de l'ensemble de données d'entraînement
        for key in dataset:
            # Ajout de l'ensemble de données statistique associé à la liste de valeurs de l'ensemble de données d'entraînement
            # key['data'] représente la liste de valeurs de l'ensemble de données d'entraînement
            features.append(outilsProcessing.extract_features(key['data']))
            # Ajout du label à la liste des labels associée à chaque liste de valeurs de l'ensemble de données d'entraînement
            labels.append(key['label'])

        # Initialisation d'un dataframe contenant la liste des ensembles de données statistiques de chaque liste de valeurs de l'ensemble de données d'entraînement
        dataframe = pd.DataFrame(features)
        # Ajout de la colonne label contenant la liste des labels associée à chaque liste de valeurs de l'ensemble de données d'entraînement
        dataframe['label'] = labels

        # Initialisation d'un dataframe contenant toutes les colonnes sauf la colonne label
        X = dataframe.drop('label', axis=1)
        # Initialisation d'un dataframe contenant la colonne des labels
        y = dataframe['label']

        # Etape 1 : Mélange des données de l'ensemble X et de l'ensemble y de façon aléatoire (random_state). Une séquence de données mélangées aléatoirement est obtenue pour l'ensemble X et pour l'ensemble y. La valeur de random_state donne une séquence spécifique de données mélangées aléatoirement.
        # Etape 2 : Pour chacune des 2 séquences, une partie des données (80%) est mise de côté pour former l'ensemble d'entraînement, et une autre partie (20%) est mise de côté pour former l'ensemble de test. On obtient donc X_train et X_test pour la séquence de l'ensemble X, et y_train et y_test pour la séquence de l'ensemble y.
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)
        
        # RandomForestClassifier est un algorithme qui classifie les données
        # Initialisation d'une forêt de 100 arbres (n_estimators = 100) sans noeuds définis construit sur une reproductibilité aléatoire (random_state = 42)
        model = RandomForestClassifier(n_estimators = 100, random_state = 42, max_depth = 30)
        
        """
        1. Initialisation d’une forêt contenant 100 arbres sans nœuds.

        2. Pour chaque arbre de la forêt :

	        2.1. Création d’un sous-ensemble aléatoire (appelé sub_X_train) de X_train avec remise (certaines données peuvent être sélectionnées plusieurs fois, tandis que d'autres peuvent ne pas être sélectionnées du tout). De manière générale, chaque arbre possède donc un sous-ensemble différent.

	        2.2. Pour le premier nœud de l’abre :

		        2.2.1. Création d’un sous ensemble aléatoire (appelé sub_X_features) de l’ensemble des caractéristiques de X, puis tirage de la meilleure caractéristique selon un critère de l’algorithme RandomForestClassifier. Ce sous-ensemble ne contient pas de doublons et est de taille racine(p), où p est la taille de l’ensemble des caractéristiques de X.
	
		        2.2.2. Calcul des valeurs seuils candidates en prenant la médiane entre chaque paire de valeurs consécutives dans le sous-ensemble sub_X_train.

		        2.2.3. Choix de la meilleure valeur seuil parmi ces valeurs en utilisant l’indice de Gini.

		        2.2.4. Ajout d’un opérateur (≤ ou ≥) entre cette caractéristique et cette valeur seuil. De manière générale, une condition vient d’être créée pour ce nœud.

		        2.2.5. Création d’une feuille à gauche et d’une feuille à droite à partir de cette condition.

		        2.2.6. Répartition des données du sous-ensemble sub_X_train dans les feuilles gauche et droite suivant cette condition. De manière générale, deux nouveaux sous-ensembles (sub_sub_X_train₁ et sub_sub_X_train₂) viennent d’être créés respectivement pour les deux feuilles.

		        2.2.7. Pour chaque feuille :

			        2.2.7.1. A partir de y_train, comptage du nombre de données de ce nouveau sous-ensemble qui sont de la même catégorie.

			        2.2.7.2. Si toutes ces données ne sont pas de la même catégorie, ou si elles ne sont pas majoraitement de la même catégorie, ou si une 	profondeur maximale (définie ou non à l’étape 1) n’a pas été atteint, la feuille devient un nouveau nœud et il faut répéter les étapes 2.2.7.3 à 2.2.7.3.7.2. Sinon, passer à l’étape 3.

			        2.2.7.3. Pour le nouveau nœud :

				        2.2.7.3.1. Création d’un sous-ensemble aléatoire de l’ensemble des caractéristiques de X, puis tirage de la meilleure caractéristique selon un critère de l’algorithme RandomForestClassifier. Ce sous-ensemble ne contient pas de doublons et est de taille racine(p), où p est la taille de l’ensemble des caractéristiques de X.

				        2.2.7.3.2. Calcul des valeurs seuils candidates en prenant la médiane entre chaque paire de valeurs consécutives dans le sous- ensemble sub_sub_X_traini.

				        2.2.7.3.3. Choix de la meilleure valeur seuil parmi ces valeurs en utilisant l’indice de Gini.

				        2.2.7.3.4. Ajout d’un opérateur (≤ ou ≥) entre cette caractéristique et cette valeur seuil. De manière générale, une condition vient d’être créée pour ce nœud.

				        2.2.7.3.5. Création d’une feuille à gauche et d’une feuille à droite à partir de cette condition.

				        2.2.6.3.6. Répartition des données du sous-ensemble sub_sub_X_traini dans les feuilles gauche et droite suivant cette condition. De manière générale, deux nouveaux sous-ensembles (sub_sub_sub_X_train₁ et sub_sub_sub_X_train₂) viennent d’être créés respectivement pour les deux feuilles.

				        2.2.7.3.7. Pour chaque feuille :

					        2.2.7.3.7.1. A partir de y_train, comptage du nombre de données de ce nouveau sous-ensemble qui sont de la même catégorie.

					        2.2.7.3.7.2. Si toutes ces données ne sont pas de la même catégorie, ou si elles ne sont pas majoritairement de la même catégorie, ou si une profondeur maximale (définie ou non à l’étape 1) n’a pas été atteint, la feuille devient un nouveau nœud et il faut répéter les étapes 2.2.7.3 à 2.2.7.3.7.2. Sinon, passer à l’étape 3.
        """
        model.fit(X_train, y_train)

        # Retourne le modèle et les dataframes
        return model, X, y


    @staticmethod
    def rename_dataframe_columns(model: RandomForestClassifier, dataframe: pd.DataFrame):
        
        """_summary_
        Renommage des colonnes sans nom du dataframe pandas en prédisant la catégorie de données
        Returns:
            _type_: _description_
        """

        # Parcours du dataframe
        for column in dataframe.columns:
            # Si la colonne du dataframe n'existe pas
            if isinstance(column, int) or column == "" or column == None or re.sub(r'[^a-zA-Z0-9\s_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().startswith("unnamed") or re.sub(r'[^a-zA-Z0-9\s_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower().endswith("unnamed"):
                # Si toutes les valeurs de la colonne du dataframe sont des entiers ou des flottants
                if all(isinstance(value, int) for value in dataframe[column]) or all(isinstance(value, float) for value in dataframe[column]):
                    # Extraction des caractéristiques statistiques de la colonne sans nom du dataframe
                    features = outilsProcessing.extract_features(dataframe[column].to_list())
                    # Conversion des caractéristiques statistiques en dataframe pandas
                    features_dataframe = pd.DataFrame([features])
                    """
                    3. Si un nouvel ensemble (appelé new_X) est inséré dans la forêt, pour chaque arbre construit :

	                    3.1. Insertion des données d’un nouvel ensemble (appelé new_X) dans l’arbre. Chaque donnée de l'ensemble new_X suit le chemin à travers l'arbre selon les règles de division définies par les caractéristiques et les valeurs seuils. Elle finit par atteindre une feuille spécifique de l'arbre. 

	                    3.2. Comptage des données de chaque feuille. La feuille avec le plus de données est la 	catégorie majoritaire.

	                    3.3. Si tous les arbres n’ont pas été faits, répéter les étapes 3.1. à 3.3. Sinon, passer à l’étape 4.

                    4. Comptage de la catégorie sortie de chaque arbre. La catégorie majoritaire est la catégorie prédite par la forêt.
                    """
                    # Prédiction de la catégorie de la colonne à partir des caractéristiques statistiques
                    prediction = model.predict(features_dataframe)[0]

                    # Si la prédiction est une chaîne de caractères
                    if isinstance(prediction, str):
                        # Si la colonne sans nom contient une série d'entiers consécutifs
                        if all(value1 == value2 for value1, value2 in zip(dataframe[column].to_list(), list(range(len(dataframe.index) + 1)))):
                            # Suppression de la colonne sans nom
                            dataframe = dataframe.drop(columns = column)
                        # Si la catégorie prédite n'est pas dans la liste des noms de colonne filtrés du dataframe
                        elif not [column for column in dataframe.columns.to_list() if prediction.startswith(re.sub(r'[^a-zA-Z0-9\s_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower()) or prediction.endswith(re.sub(r'[^a-zA-Z0-9\s_]', '', column.split(",")[0].strip("_")).replace(' ','_').lower())]:
                            # Renommage de la colonne sans nom du dataframe
                            dataframe = dataframe.rename(columns={column: prediction})
                        # Sinon
                        else:
                            # Suppression de la colonne sans nom
                            dataframe = dataframe.drop(columns = column)
        
        # Retourne le dataframe actualisé
        return dataframe




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
    
    # Initialisation du chemin
    arrangement_path = './trajectory_catalog.json'

    xarray_dataset = outilsProcessing(None, dataframe, xr.Dataset(), arrangement_path, True)
    xarray_dataset.create_xarray_dataset()
    xarray_dataset.__repr__()
