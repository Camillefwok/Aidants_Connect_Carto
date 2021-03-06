# flake8: noqa

import re
import csv
import time

from django.core.management import BaseCommand

from aidants_connect_carto import constants
from aidants_connect_carto.apps.core import utilities


DEFAULT_SEPARATEUR_DATA_SET = ","
DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES = ","
DEFAULT_QUOTES_CUSTOM_VALUE = "///"
DEFAULT_DATA_SET_EXTENSION = ".csv"


class Command(BaseCommand):
    """
    Usage :
    python manage.py transform_data_set_csv data/hub_abc/hub_abc_import_config.csv
    """

    help = "Transform a dataset using the specified config"

    def add_arguments(self, parser):
        parser.add_argument(
            "config",
            help="Le chemin vers la configuration d'import du jeu de donnée",
            nargs=1,
            type=str,
        )

    def handle(self, *args, **kwargs):
        # init
        data_set_config_file_path = kwargs["config"][0]
        data_set_config = []
        data_set_file_path = ""
        data_set_config_seperateur = DEFAULT_SEPARATEUR_DATA_SET
        temp_place_list = []
        csv_fieldnames = []

        # Open the config file and store the data_set_config as well as the ouput header
        print("Step 1 : reading data_set config file")
        with open(data_set_config_file_path) as f:
            csvreader = csv.DictReader(f)
            data_set_config = [dict(d) for d in csvreader]
            # data_set path
            data_set_file_path = next(
                d["fichier"]
                for d in data_set_config
                if d["modele"] == "_meta_fichier_chemin"
            )
            # data_set separateur
            data_set_config_seperateur = next(
                (
                    d["fichier"]
                    for d in data_set_config
                    if d["modele"] == "_meta_fichier_separateur"
                ),
                DEFAULT_SEPARATEUR_DATA_SET,
            )
            # csv header
            data_set_config_fields = [
                d for d in data_set_config if not d["modele"].startswith("_meta")
            ]
            csv_fieldnames = [d["modele"] for d in data_set_config_fields]

        # Process each line of the data_set
        print("Step 2 : reading input data_set file")
        # encoding='utf-8-sig' ? sometimes the first column starts with "\ufeff"
        with open(data_set_file_path, encoding="utf-8-sig") as f:
            csvreader = csv.DictReader(f, delimiter=data_set_config_seperateur)
            print("... number of rows :", sum(1 for row in csvreader))
            # reset the csvreader, and skip header
            f.seek(0)
            next(f)
            for index, row in enumerate(csvreader):
                if index and (index % 100 == 0):
                    print("..." * int(index / 100), index)
                place_dict = create_place_output_dict(dict(row), data_set_config_fields)
                temp_place_list.append(place_dict)
                time.sleep(0.5)  # to avoid spamming the Address (BAN) API

        # Store the header and the processed lines in a new file
        print("Step 3 : writing output (transformed) data_set file")
        data_set_transformed_file_path = (
            data_set_file_path.split(DEFAULT_DATA_SET_EXTENSION)[0]
            + "_transformed"
            + DEFAULT_DATA_SET_EXTENSION
        )
        with open(data_set_transformed_file_path, "w") as output_file:
            csvwriter = csv.DictWriter(output_file, fieldnames=csv_fieldnames)
            csvwriter.writeheader()
            csvwriter.writerows(temp_place_list)
        print("... file created :", data_set_transformed_file_path)

        print("Done !")


def create_place_output_dict(place_input_dict, data_set_import_config):
    """
    Process each field from the data_set_import_config
    Fields adresse_brut & horaires_ouverture_brut have a special processing, because they update collateral fields
    """
    place_output_dict = {}

    for champ in data_set_import_config:
        # champ example : {'modele': 'contact_telephone', 'fichier': 'telephone', 'commentaire': ''}
        if champ["modele"] not in place_output_dict:
            if re.match(f"^{DEFAULT_QUOTES_CUSTOM_VALUE}.*$", champ["fichier"]):
                place_output_dict[champ["modele"]] = champ["fichier"].split(
                    DEFAULT_QUOTES_CUSTOM_VALUE
                )[1]
            else:
                if champ["modele"] == "type_lieu":
                    if champ["fichier"]:
                        place_output_dict[champ["modele"]] = utilities.process_type(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "statut":
                    if champ["fichier"]:
                        place_output_dict[champ["modele"]] = utilities.process_status(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "nature_juridique":
                    if champ["fichier"]:
                        place_output_dict[
                            champ["modele"]
                        ] = utilities.process_legal_entity_type(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "adresse_brut":
                    place_output_dict = process_place_address(
                        place_output_dict, place_input_dict, champ["fichier"]
                    )
                elif champ["modele"] == "en_ligne":
                    input_field = (
                        place_input_dict[champ["fichier"]] if champ["fichier"] else None
                    )
                    place_output_dict[champ["modele"]] = utilities.process_is_online(
                        input_field, destination="file"
                    )
                elif champ["modele"] == "contact_telephone":
                    if champ["fichier"]:
                        # place_output_dict["contact_phone_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[
                            champ["modele"]
                        ] = utilities.process_phone_number(
                            place_input_dict[champ["fichier"]]
                        )
                elif champ["modele"] == "horaires_ouverture_brut":
                    place_output_dict = process_place_opening_hours(
                        place_output_dict, place_input_dict, champ["fichier"]
                    )
                elif champ["modele"] == "public_cible":
                    if champ["fichier"]:
                        # place_output_dict["target_audience_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[
                            champ["modele"]
                        ] = utilities.process_target_audience(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "modalites_acces":
                    if champ["fichier"]:
                        # place_output_dict["support_access_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[
                            champ["modele"]
                        ] = utilities.process_support_access(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "modalites_accompagnement":
                    if champ["fichier"]:
                        # place_output_dict["support_mode_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[
                            champ["modele"]
                        ] = utilities.process_support_mode(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "labels":
                    if champ["fichier"]:
                        # place_output_dict["labels_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[champ["modele"]] = utilities.process_labels(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                elif champ["modele"] == "services":
                    if champ["fichier"]:
                        # place_output_dict["services_raw"] = place_input_dict[champ["fichier"]]
                        place_output_dict[champ["modele"]] = utilities.process_services(
                            place_input_dict[champ["fichier"]], destination="file"
                        )
                # elif champ["modele"] == "price_details":
                #     place_output_dict["price_details"] = place_input_dict[champ["fichier"]]
                #     place_output_dict["is_free"] = utilities.process_price(place_input_dict[champ["fichier"]])
                # elif place_fields_mapping_boolean
                else:
                    place_output_dict[champ["modele"]] = (
                        place_input_dict[champ["fichier"]] if champ["fichier"] else ""
                    )

    # TODO: to be removed, by updating the utilities
    # Some fields are set as arrays, we need to transform them back to strings
    for champ in place_output_dict:
        if type(place_output_dict[champ]) == list:
            place_output_dict[champ] = DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES.join(
                place_output_dict[champ]
            )

    return place_output_dict


def process_place_address(place_output_dict, place_input_dict, input_field):
    """
    - Exemple avec 1 champ : 
        - input_field = "addresse complète"
        - adresse_brut = "20 Avenue de Ségur 75007 Paris"
    - Exemple avec plusieurs champs : 
        - input_field = "rue,cp,ville"
        - input_field_to_list = ["rue", "cp", "ville"]
        - place_field_to_list = ["15 Place de la République", "69001", "Lyon"]
        - adresse_brut = "15 Place de la République 69001 Lyon"
        - ...
    """
    # set adresse_brut
    if DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES in input_field:
        input_field_to_list = input_field.split(DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES)
        place_field_to_list = [place_input_dict[item] for item in input_field_to_list]
        place_output_dict["adresse_brut"] = " ".join(place_field_to_list).strip()
    else:
        place_output_dict["adresse_brut"] = (
            place_input_dict[input_field].strip() if input_field else ""
        )

    # set adresse_* fields
    if place_output_dict["adresse_brut"]:
        address_api_results_processed = utilities.process_address(
            place_output_dict["adresse_brut"]
        )
        if address_api_results_processed:
            place_output_dict["adresse_numero"] = address_api_results_processed[
                "housenumber"
            ]
            place_output_dict["adresse_rue"] = address_api_results_processed["street"]
            place_output_dict["adresse_code_postal"] = address_api_results_processed[
                "postcode"
            ]
            place_output_dict["adresse_code_insee"] = address_api_results_processed[
                "citycode"
            ]
            place_output_dict["adresse_commune"] = address_api_results_processed["city"]
            # place_output_dict["address_departement_code"] = address_api_results_processed[
            #     "departement_code"
            # ]
            place_output_dict["adresse_departement"] = address_api_results_processed[
                "departement_name"
            ]
            place_output_dict["adresse_region"] = address_api_results_processed[
                "region_name"
            ]
            place_output_dict["latitude"] = address_api_results_processed["latitude"]
            place_output_dict["longitude"] = address_api_results_processed["longitude"]

    return place_output_dict


def process_place_opening_hours(place_output_dict, place_input_dict, input_field):
    """
    - Exemple avec 1 champ : 
        - input_field = "horaires"
        - horaires_ouverture_brut = "du lundi au vendredi de 9h à 18h"
    - Exemple avec plusieurs champs : 
        - input_field = "lundi,mardi"
        - input_field_to_list = ["lundi", "mardi"]
        - place_field_to_list = ["Lundi: 9h-18h", "Mardi: 9h-12h"]
        - horaires_ouverture_brut = "Lundi: 9h-18h, Mardi: 9h-12h"
    """
    OPENSTREETMAP_DAY_SEPERATOR = "; "

    # set horaires_ouverture_brut
    if DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES in input_field:
        input_field_to_list = input_field.split(DEFAULT_SEPARATEUR_CHAMPS_MULTIPLES)
        place_field_to_list = [place_input_dict[item] for item in input_field_to_list]
        place_output_dict["horaires_ouverture_brut"] = OPENSTREETMAP_DAY_SEPERATOR.join(
            place_field_to_list
        )
        # avoid empty "; ; ; " value
        if re.match("^[ ;]*$", place_output_dict["horaires_ouverture_brut"]):
            place_output_dict["horaires_ouverture_brut"] = ""
    else:
        place_output_dict["horaires_ouverture_brut"] = (
            place_input_dict[input_field] if input_field else ""
        )

    # set horaires_ouverture_osm
    if place_output_dict["horaires_ouverture_brut"]:
        place_output_dict[
            "horaires_ouverture_osm"
        ] = utilities.process_opening_hours_to_osm_format(
            place_output_dict["horaires_ouverture_brut"]
        )

    return place_output_dict
