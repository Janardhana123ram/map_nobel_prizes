import argparse
import logging
import requests

import pandas as pd

class Parse:
    """Map information from URLs and write to CSV
    """

    def __init__(self):
        parser = argparse.ArgumentParser()
        parser = self.define_args(parser)
        self.args = parser.parse_args()
        self.log = logging.getLogger("parse_file")
        self.csv_file = open(self.args.csv_file, "w")

    def define_args(self, parser):
        parser.add_argument("--url1", required=True, help="It contains nobel prize winners list")
        parser.add_argument("--url2", required=True, help="It contains country codes with name")
        parser.add_argument("--csv-file", required=True, help="Output csv file to store")
        return parser

    def get_data(self, URL):
        """
        :param URL: Make get request to given URL
        :return dict: returns dict object if request successful
        """

        try:
            data = requests.get(URL).json()
            return data
        except Exception as err:
            self.log.error(msg=str(err))

    def get_name(self, info):
        """Merge firstname and surname

        :param info: It contains nobel info
        :return str: Return append firstname and surname if they exists
        """

        if not info.get("surname"):
            return info.get("firstname")
        name = info.get("firstname")+" "+ info.get("surname")
        return name.strip()

    def get_unique(self, prizes, key):
        """Get unique values from prizes key

        :param prizes: This contains list of prizes recieved for person
        :param key: This contains field name
        :return str: Returns unique elements separated by colon (:)
        """

        values = []
        for prize in prizes:
            if prize.get(key) and prize[key] not in values:
                values.append(prize[key])
        return ":".join(values)

    def map_info(self, nobel_info):
        """Consolidate the nobel info into required schema

        :param nobel_info: this information about nobel prize winner
        :return dict: Returns mapped dict
        """

        f_dict = {}
        f_dict["id"] = nobel_info["id"]
        f_dict["name"] = self.get_name(nobel_info)
        f_dict["dob"] = nobel_info.get("born") or ""
        f_dict["unique_prize_years"] = self.get_unique(nobel_info["prizes"], "year")
        f_dict["unique_prize_categories"] = self.get_unique(nobel_info["prizes"], "category")
        f_dict["gender"] = nobel_info.get("gender") or ""

        return f_dict

    def get_county(self, code):
        """Get country name from countries list

        :param code: This holds nodel prize winner born county code
        :return str: Return first country from the list else return empty string
        """

        if not code:
            return
        try:
            c_names = [country["name"] for country in self.country_codes if country.get("code")==code]
            return c_names[0]
        except IndexError as err:
            return ""

    def write_csv(self, mapped_info):
        """Write mapped info to the CSV file"""

        data = pd.json_normalize(mapped_info)
        data.to_csv(self.csv_file, index=False, header=False)

    def run(self):
        self.log.info("Started mapping..")
        nobel_prizes = self.get_data(self.args.url1)

        if nobel_prizes:
            self.country_codes = self.get_data(self.args.url2)["countries"]
            if nobel_prizes.get("laureates"):
                for nobel_info in nobel_prizes["laureates"]:
                    mapped_info = self.map_info(nobel_info)
                    mapped_info["countries"] = self.get_county(nobel_info.get("bornCountryCode"))
                    self.write_csv(mapped_info)
        self.csv_file.close()


Parse().run()
