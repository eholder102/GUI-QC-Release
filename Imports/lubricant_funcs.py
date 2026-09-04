#functions that make the process run more smoothly and modularly
#cmd line interface
import os.path
import os
import subprocess

#misc
from datetime import datetime
from time import time

#file management
import io
import shutil

def compact_label_name(name):
    newname = ""
    for character in name:
        if character == ",":
            break
        else: newname += character
    return newname
def yes_no_to_bool(value):
    if value.upper() == "YES":
        return True
    else:
        return False

def strip_date_zeros(date):
   newdate = ""
   i = -1
   for digit in date:
       i+=1
       if digit == "0" and (i == 0 or i == 3):
           continue
       else: 
           newdate += str(digit)

   return newdate

def convert_between_date_formats(date):
   newdate = ""
   i = 0
   for digit in date:
       if digit == '-':
           newdate += '/'
       else: newdate += str(digit)
   return newdate

def skip_value_by_column(column):
    test_columns = [6,9,13,18]
    if column > 18 or (column > 5 and column not in test_columns):
        return True
    if column in test_columns or column < 5:
        return False
    
def todays_date():
    return datetime.today().strftime('%m-%d-%Y')

def generate_first_four_digits_batch_id(type="R"):
   today = str(todays_date())
   year_digit = today[9]
   month_num = today[0] + today[1]
   first_four_digits = type + year_digit + month_num
   return first_four_digits


def convert_date_to_month_year(date):
   months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
   month_num = int(date[1])
   month = months[month_num-1]
   year = date[6:10]
   date_string = month + " " + year
   return date_string.upper()

def month_from_batchID(batchID):
    first_four_digits = batchID[0:4]
    year = "202" + first_four_digits[1]
    month = first_four_digits[2] + first_four_digits[3]
    day = "01"
    date = month + "-" + day + "-" + year
    return convert_date_to_month_year(date)   