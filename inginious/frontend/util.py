# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from datetime import datetime



def dict_data_datetimes_to_str(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.strftime("%Y-%m-%d %H:%M:%S")
            else:
                dict_data_datetimes_to_str(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            dict_data_datetimes_to_str(item)
    return data


def dict_data_str_to_datetimes(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    if value == "1-01-01 00:00:00":
                        data[key] = datetime.min
                    elif value == "9999-12-31 23:59:59":
                        data[key] = datetime.max
                    else:
                        data[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if (value != "") else None
                except ValueError:
                    pass  # If it's not a valid date string, continue without converting
            else:
                dict_data_str_to_datetimes(value)
    elif isinstance(data, list):
        for index, item in enumerate(data):
            dict_data_str_to_datetimes(item)
    return data


def change_access_structure(access_data, needs_soft_end=False):
    """
    Transforms old access structure (course access and registration, task access) into new structure.
    ex: "accessible" can be a boolean or a concatenation of start and end dates ("start/end").
        It will be transformed to have this structure:
            "accessible": {"start": ..., "end": ...}
            "registration": {"start": ..., "end": ...}
            "accessibility": {"start": ...,"soft_end": ..., "end": ...}
        When one of the dates is not given in a custom access or always/never accessible, it will be set to a max or min date.
        examples:
            "registration": {"start": "2023-11-24 16:44:56", "end": "2023-11-24 16:44:56"}
            "accessible": {"start": "2023-11-24 16:44:56", "end": "2023-11-24 16:44:56"}
    :param access_data: dict, old access structure
    :param needs_soft_end: bool, True if the new structure needs a soft_end date in the structure
    :return: dict, new access structure
    """

    new_access_data = {"start": None, "end": None}

    if isinstance(access_data, bool):
        new_access_data["end"] = "9999-12-31 23:59:59"
        if needs_soft_end:
            new_access_data["soft_end"] = "9999-12-31 23:59:59"
        if access_data:
            new_access_data["start"] = "0001-01-01 00:00:00"
        else:
            new_access_data["start"] = "9999-12-31 23:59:59"


    elif isinstance(access_data, str) and access_data != "":
        dates = access_data.split("/")
        if needs_soft_end:
            new_access_data["start"] = dates[0]
            new_access_data["soft_end"] = dates[1]
            new_access_data["end"] = dates[2]
        else:
            new_access_data["start"] = dates[0]
            new_access_data["end"] = dates[1]

    return new_access_data