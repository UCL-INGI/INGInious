"""
Contains two functions that converts datetime objects in data structures into strings and vice versa.
"""
# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

from datetime import datetime



def dict_data_datetimes_to_str(data):
    """
    :param data: dict or list data to convert
    :return: dict or list with datetime objects converted to strings
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.strftime("%4Y-%m-%d %H:%M:%S")
            else:
                dict_data_datetimes_to_str(value)
    elif isinstance(data, list):
        for item in data:
            dict_data_datetimes_to_str(item)
    return data


def dict_data_str_to_datetimes(data):
    """
    :param data: dict or list data to convert
    :return: dict or list with string dates converted to datetime objects
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                try:
                    if value == "0001-01-01 00:00:00":
                        data[key] = datetime.min
                    elif value == "9999-12-31 23:59:59":
                        data[key] = datetime.max.replace(microsecond=0)
                    else:
                        data[key] = datetime.strptime(value, '%Y-%m-%d %H:%M:%S') if (value != "") else None
                except ValueError:
                    pass  # If it's not a valid date string, continue without converting
            else:
                dict_data_str_to_datetimes(value)
    elif isinstance(data, list):
        for item in data:
            dict_data_str_to_datetimes(item)
    return data
