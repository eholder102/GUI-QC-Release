import sys
import math
from time import time as t
import time as tt
import re
import os
import subprocess
import json

#GUI
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMessageBox, QPushButton, QInputDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal, QObject,QTimer
from qcrelease import Ui_QCRelease

#graceful handling
import configparser
import logging

#TODO:  implement SSF generation(get test and specs also allow deletion from testing table), check for more errors, scroll properly,fix resize lag issue, FIX SKIP VALUE DETERMINATION
#TODO: create master sheet of ingredients w/ tests run and price
#imports
from Imports.material_data import material_data as raw_material_data
from Imports.material_data import run_report
from Imports.material_data import list_form_to_class_form
from Imports.googleAPI_functions import *

#pdf generation
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from pypdf import PdfReader, PdfWriter
import pyperclip

from pathlib import Path

APP_VERSION = "1.0.3"
APP_DIR = Path(__file__).resolve().parent
#my_path_to_label_opener = "C:/Program Files/Google/Chrome/Application/chrome.exe"
def create_config():
    config = configparser.ConfigParser()
    # Add sections and key-value pairs
    config['General'] = {
        'initials': 'EH',
        'temp_test_sheet':'temp_test_sheet.pdf',
        'annotated_temp_test_sheet': 'annotated_temp_test_sheet.pdf',
        'path_to_label_opener':'Default',

    }
    config['Google_IDs'] = {
        'RM_check_in_sheet_ID': '1EAEebDpJOGWZIe2bwn-qrQbPUS3r3rAs8tPrc7xFhC0',
        'component_check_in_sheet_ID': '1tYN6ZdOwAArKyEYd9wQ9lMBGtd0YyVgMv_PkTDalw10',
        'label_check_in_sheet_ID':'1IlMSsYDdCt9wU2oM08FMLpykfB7Y6aZzHGDIIj3LufM',
        'ssf_sheet_ID':'1omkvbp9uCnwgLqeaQ1Bx-09M7o9a09nNtjsFYU9szHQ',
        'test_request_sheet_ID':'1_mhtkm_WtaOGVH5H4-FQYV1_4656AiXUKec8m7KSKy0',
        'testing_log_sheet_ID':'1259PcgexoY4Ufqo3yBjoQTF7p_M230a2AF8O7VspkIQ',
        'google_drive_ID':'0AItqRy9P8sAQUk9PVA',
        'skip_log_ID':'1_mhtkm_WtaOGVH5H4-FQYV1_4656AiXUKec8m7KSKy0'
    }
    # Write the configuration to a file
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def read_config():
    config = configparser.ConfigParser()

    # Read the configuration file
    try:
        with open(APP_DIR / 'config.ini') as f:
            config.read_file(f)
    except Exception as e:
       logger.error(e)
       logger.error("Creating New config.ini")
       create_config()
       return read_config()
    # Access values from the configuration file
    initials = config.get('General', 'initials')
    RM_check_in_sheet_ID = config.get('Google_IDs', 'RM_check_in_sheet_ID')
    Component_check_in_sheet_ID = config.get('Google_IDs', 'component_check_in_sheet_ID')
    google_drive_ID = config.get('Google_IDs', 'google_drive_ID')
    temp_test_sheet = config.get('General', 'temp_test_sheet')
    annotated_temp_test_sheet = config.get('General', 'annotated_temp_test_sheet')
    path_to_label_opener = config.get('General', 'path_to_label_opener')
    ssf_sheet_ID = config.get('Google_IDs', 'ssf_sheet_ID')
    test_request_sheet_ID = config.get('Google_IDs', 'test_request_sheet_ID')
    testing_log_sheet_ID = config.get('Google_IDs', 'testing_log_sheet_ID')
    label_check_in_sheet_ID = config.get('Google_IDs', 'label_check_in_sheet_ID')
    skip_log_ID = config.get('Google_IDs', 'skip_log_ID')
    

    # Store retrieved values in a dictionary
    config_values = {
        'initials': initials,
        'RM_check_in_sheet_ID': RM_check_in_sheet_ID,
        'component_check_in_sheet_ID': Component_check_in_sheet_ID,
        'google_drive_ID':google_drive_ID,
        'temp_test_sheet': temp_test_sheet,
        'annotated_temp_test_sheet': annotated_temp_test_sheet,
        'path_to_label_opener': path_to_label_opener,
        'ssf_sheet_ID':ssf_sheet_ID,
        'test_request_sheet_ID':test_request_sheet_ID,
        'testing_log_sheet_ID':testing_log_sheet_ID,
        'label_check_in_sheet_ID':label_check_in_sheet_ID,
        'skip_log_ID':skip_log_ID
    }

    return config_values
def check_for_updates():
    try:
        subprocess.Popen(
            [
                str(APP_DIR / "Python" / "pythonw.exe"),
                str(APP_DIR / "update.py"),
                APP_VERSION,
                str(os.getpid())
            ],
            cwd=str(APP_DIR)
        )

        logger.info("Started update checker")

    except Exception:
        logger.exception("Could not start update checker")
def start_update_install(version, zip_path, temp_dir):
    try:
        logger.info(
            "Starting installation of update %s",
            version
        )

        subprocess.Popen(
            [
                str(APP_DIR / "Python" / "pythonw.exe"),
                str(APP_DIR / "update.py"),
                APP_VERSION,
                "--install",
                str(zip_path),
                str(temp_dir),
                str(os.getpid())
            ],
            cwd=str(APP_DIR)
        )

        logger.info("Update installer process started")

        return True

    except Exception:
        logger.exception(
            "Could not start update installer"
        )

        return False
class search_sheet_worker(QObject):
   progress = pyqtSignal(int)
   complete = pyqtSignal(int,str,str)
   error = pyqtSignal(str)
   configs  = None
   most_recent_request = None
   selected_request = None
   annotate = False
   

   def annotate_test_data_sheet(self,given_batch_data):
     if isinstance(given_batch_data,list):
        batch_data = list_form_to_class_form(given_batch_data)
     else: batch_data = given_batch_data
     try:
        reader = PdfReader("temp_test_sheet.pdf")
     except:
        return
     first_page = reader.pages[0]
     page_width = float(first_page.mediabox.width)
     page_height = float(first_page.mediabox.height)

    # Create a text overlay sized to the source page.
     buffer = io.BytesIO()
     c = Canvas(buffer, pagesize=(page_width, page_height))
     c.setFont("Helvetica", 10)
     c.drawString(450, page_height - 105, batch_data.batchID) #fill lot num
     c.drawString(190, page_height - 190, str(datetime.time(datetime.now()))[0:5]) #fill time
     c.drawString(273, page_height - 190, todays_date()) #fill top date
     c.drawString(115, page_height - 208, batch_data.vendor) #fill vendor
     c.drawString(390, page_height - 208, batch_data.vendor_lot_num)
     c.drawString(325, page_height - 700, todays_date()) #fill bottom date
     c.save()
     buffer.seek(0)

    # Merge overlay onto the first page.
     overlay_reader = PdfReader(buffer)
     writer = PdfWriter()

     first_page.merge_page(overlay_reader.pages[0])
     writer.add_page(first_page)

    # Copy remaining pages unchanged.
     for page in reader.pages[1:]:
         writer.add_page(page)

     with open(APP_DIR / "annotated_temp_test_sheet.pdf", "wb") as f:
         writer.write(f)
     open_test_data_sheet(self.configs['annotated_temp_test_sheet'])
     self.progress.emit(100)
     self.complete.emit(1,batch_data.ingredientID,"FOUND AND ANNOTATED TEST SHEET")
     return 
   def find_test_data_sheet(self):
        found = 0
        if not self.selected_request: requested = self.most_recent_request
        else: requested = self.selected_request
        if not self.selected_request:
           try:
            requested = self.most_recent_request.list_form()
           except Exception as e:
              logger.error(e)
              self.error.emit(str(e))
              self.complete.emit(1,"NONE", "FAILED TO FIND TEST SHEET")
        else: requested = self.selected_request
        if requested == None or isinstance(requested,int) or requested[0] in (0,1):
            logger.error("NO BATCH ID PROVIDED")
            self.error.emit("NO BATCH ID PROVIDED")
            self.complete.emit(1,"NONE", "FAILED TO FIND TEST SHEET")
            return 0
        ingredientID = requested[1]
        ingredientID = ingredientID.strip()
        self.progress.emit(0)
        creds = None
        
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(APP_DIR / "drivetoken.json"):
            creds = Credentials.from_authorized_user_file("drivetoken.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
             creds.refresh(Request())
            else:
             flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
             creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(APP_DIR / "drivetoken.json", "w") as token:
             token.write(creds.to_json())
             self.progress.emit(10)
        try:
         os.remove(self.configs['temp_test_sheet'])
         os.remove(self.configs['annotated_temp_test_sheet'])
        except:
         pass
        self.progress.emit(15)
        try:
            service = build("drive", "v3", credentials=creds)
            page_token = None
            items = []
            # Call the Drive v3 API
            self.progress.emit(20)
            progress = 20
            logger.info("ingredientID:" + ingredientID)
            
            query = (
            f"name contains '{ingredientID}'"
            "and mimeType = 'application/pdf' "
            "and trashed = false"
            )  

            while True:
                results = (
                    service.files() #TODO:figure out how to efficiently find the files
                    .list(q=query,
                        spaces="drive",
                        driveId = self.configs['google_drive_ID'],
                        fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
                        pageToken=page_token,
                        includeItemsFromAllDrives="True",
                        corpora="drive",
                        supportsAllDrives="True",
                        orderBy="modifiedTime desc")
                    .execute()
                )
                
                items.append(results.get("files", []))
                page_token = results.get('nextPageToken', None)
                progress += 1
                if progress < 60: self.progress.emit(progress)
                if not page_token:
                    break
                
            
            for item in items[0]:
                
                progress += 1
                if progress < 90: self.progress.emit(progress)
                if item: #get only populated entries
                    
                    
                    if requested[0][1] not in "0123456789": #labels will never match this
                        prefix = f"[{ingredientID[:3]}]"

                        
                        if not item['name'].strip().startswith(prefix):
                            
                            continue
                    else:
                        pattern = rf"^{re.escape(ingredientID)}(?:\.pdf|\s*-\s*\d+\.pdf)$" #stolen regex hope it works
                        if not re.match(pattern, item['name'], re.IGNORECASE):
                         logger.info("Not an exact match: " + item['name'])
                         continue
                    try:
                # create drive api client
                
                        
                        file_id = item['id']
                        
                        # pylint: disable=maybe-no-member
                        request = service.files().get_media(fileId=file_id)
                        file = io.BytesIO()
                        downloader = MediaIoBaseDownload(file, request)
                        done = False
                        while done is False:
                            status, done = downloader.next_chunk()
                            print(status)
                            progress += 1
                            if progress < 90: self.progress.emit(progress)
                    
                        file.seek(0)
                        
                        with open(APP_DIR / self.configs['temp_test_sheet'],'wb') as f:
                            shutil.copyfileobj(file, f)
                        found = 1
                        if self.annotate:
                            self.annotate_test_data_sheet(requested)
                            return 1
                        else:
                            open_test_data_sheet(self.configs['temp_test_sheet'])
                            self.progress.emit(100)
                            self.complete.emit(1,ingredientID,"FOUND TEST SHEET")
                            return 1
                            
                    except HttpError as e:
                        logger.error(f"An error occurred: {str(e)}")
                        self.error.emit(str(e)) 
                        self.complete.emit(1,"NONE", "FAILED TO FIND TEST SHEET")
                        file = None
                
                    
        except HttpError as e:
            # TODO(developer) - Handle errors from drive API.
            logger.error(f"An error occurred: {str(e)}")
            self.error.emit(str(e))
            self.complete.emit(1,"NONE", "FAILED TO FIND TEST SHEET")
        if not found: 
            self.progress.emit(0)
            self.error.emit("COULD NOT FIND TEST SHEET")
            logger.error("COULD NOT FIND TEST SHEET")
            self.complete.emit(1,"NONE", "FAILED TO FIND TEST SHEET")
            return
        

class labels_thread(QThread):
    result_ready = pyqtSignal(int)
    
    
    def __init__(self):
        super().__init__()
        

    def run(self):
        try:
            label_path = APP_DIR / self.filename
            logger.info("Attempting to open label: %s", label_path)
            logger.info("Label exists: %s", label_path.exists())
            if self.configs["path_to_label_opener"] == "Default":
                os.startfile(str(label_path))
            else:
                subprocess.run(
                    [
                        self.configs["path_to_label_opener"],
                        str(label_path)
                    ],
                    shell=True
                )

        except Exception:
            logger.exception("ERROR IN LABELS THREAD")

class MyApp(QMainWindow, Ui_QCRelease):

    most_recent_request = None
    selected_request = 0  
    cached_RM_check_in_values = {}
    cached_component_check_in_values = {}
    cached_label_check_in_values = {}
    cached_test_values = []
    cached_skip_values = []
    recent_requests = []
    to_be_tested = []
    annotate = False
    timestamp = False
    configs = {}

    #run report variables
    starttime = 0
    endtime = 0
    batches_released = []
    labels_created = []
    batches_searched = []
    test_sheets_searched = []
    tests_requested = []
    total_price_of_tests = 0
    heavy_metals_price = 114
    routine_micros_price = 55


    def __init__(self):
        super().__init__()
        self.starttime = t()
        # Set up the UI generated by Qt Designer
        self.setupUi(self)
        self.progressBar.setValue(0)
        self.testsheetprogressbar.setValue(0)
        self.tustinbar.setValue(0)
        
        # Connect GUI
        self.displaydatabutton.clicked.connect(self.display_clicked) #connect display data button
        self.annotatesheetbox.stateChanged.connect(self.annotate_state_change)
        self.searchtestsheetbutton.clicked.connect(self.search_sheet_clicked)
        self.createlabelsbutton.clicked.connect(self.create_labels_clicked)
        self.timestampbox.stateChanged.connect(self.timestamp_state_change)
        self.batchdatatable.cellClicked.connect(self.get_selected_cell_batch_data)
        self.testingtable.cellClicked.connect(self.get_selected_cell_batch_data)
        self.releaseButton.clicked.connect(self.release_clicked)
        self.batchIDinput.returnPressed.connect(self.release_clicked)
        self.tustinbutton.clicked.connect(self.tustinbuttonclicked)
        self.labelsthread = labels_thread()

    def check_update_ready(self):
        update_file = APP_DIR / "update_ready.json"

        if not update_file.exists():
            return

        try:
            with open(
                update_file,
                "r",
                encoding="utf-8"
            ) as file:
                update_info = json.load(file)

            version = update_info["version"]
            zip_path = update_info["zip_path"]
            temp_dir = update_info["temp_dir"]

            logger.info(
                "Update ready to install: %s",
                version
            )

            reply = QMessageBox.question(
                self,
                "QC Release Update",
                f"Version {version} is available.\n\n"
                "Would you like to update now?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply == QMessageBox.Yes:

                if start_update_install(
                    version,
                    zip_path,
                    temp_dir
                ):

                    logger.info(
                        "User accepted update %s",
                        version
                    )

                    # Remove the notification file so it
                    # isn't detected again.
                    try:
                        update_file.unlink()
                    except Exception:
                        logger.exception(
                            "Could not remove update_ready.json"
                        )

                    # This triggers your normal closeEvent().
                    QApplication.quit()

            else:

                logger.info(
                    "User declined update %s",
                    version
                )

                try:
                    update_file.unlink()
                except Exception:
                    logger.exception(
                        "Could not remove update_ready.json"
                    )

        except Exception:
            logger.exception(
                "Error processing available update"
            )
        
        
    def closeEvent(self, a0):
        logger.info("GENERATING SESSION REPORT...")
        self.endtime = t()
        r = run_report(self.starttime,self.endtime,self.batches_released,self.batches_searched,self.test_sheets_searched,self.labels_created,self.tests_requested,self.total_price_of_tests)
        r.print_run_report()
        logger.info("CLOSING SESSION..." + "\n")
        return super().closeEvent(a0)
        
    def write_batch_to_file(self):
       try:
          
        with open(APP_DIR / "saved_batches.txt", "a") as f:
          f.write(','.join(self.most_recent_request.list_form()))
          f.write("\n")
       except Exception as e:
          logger.error(e)
          logger.error("FAILED TO WRITE TO SAVED BATCHES")
          return
       logger.info("Saved batch ID " + self.most_recent_request.batchID + " in saved batches")
       return
          
        

    def get_selected_cell_batch_data(self,row,column):
        selected_cell = self.batchdatatable.item(row,column)
        self.selected_request = self.recent_requests[selected_cell.row()]
        self.batchIDinput.setText(self.selected_request[0])
        pyperclip.copy(self.selected_request[0] + " " + self.selected_request[1] + " " + todays_date())
    def annotate_state_change(self):
       if self.annotatesheetbox.isChecked():
            self.annotate = True
       else:
            self.annotate = False

    def timestamp_state_change(self):
           if self.timestampbox.isChecked():
                self.timestamp = True
           else:
                self.timestamp = False
           self.timestamp_label.setText("")
       
    def cache_check_in_values(self,sheetID,month,type_material):
        creds = None
      # The file token.json stores the user's access and refresh tokens, and is
      # created automatically when the authorization flow completes for the first
      # time.
        if os.path.exists(APP_DIR / "sheetstoken.json"):
            creds = Credentials.from_authorized_user_file(APP_DIR / "sheetstoken.json", SCOPES)
      # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
         if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
         else:
          flow = InstalledAppFlow.from_client_secrets_file(
              "credentials.json", SCOPES
          )
          creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(APP_DIR / "sheetstoken.json", "w") as token:
          token.write(creds.to_json())
        try:
            service = build("sheets", "v4", credentials=creds)
        
            # Call the Sheets API
            sheet = service.spreadsheets()
            result = (
                sheet.values()
                .get(spreadsheetId=sheetID, range=month + "!A2:AF2000")
                .execute()
            )
            match type_material:
                       case 'R': #raw material
                          try:
                            self.cached_RM_check_in_values[month] = result
                          except Exception as e:
                             logger.debug(e)
                             return 0
                       case 'P': #component
                          try:
                            self.cached_component_check_in_values[month] = result
                          except Exception as e:
                              logger.debug(e)
                              return 0
                       case 'L': #label
                        try:
                         self.cached_label_check_in_values[month] = result
                        except Exception as e:
                            logger.debug(e)
                            return 0
                       case _:
                          logger.warning("Material Type Not supported")
                          return 0
           
            
        except HttpError as e:
            logger.error(str(e))
            self.show_error(str(e))    
        return 0
    def cache_test_data_values(self,sheetID):
       cache = get_test_data(sheetID,"Standard Test Requests","!A:M")['values']
       if isinstance(cache, str):
          logger.error("ERROR IN get_test_data() routine")
          logger.error(cache)
       elif isinstance(cache,list):
          self.cached_test_values = cache
       else:
          logger.error("Error in caching test values")
    def cache_skip_values(self,sheetID):
       cache = get_test_data(sheetID,"SLE Status","!E:BC")['values']
       if isinstance(cache, str):
          logger.error(cache)
       elif isinstance(cache,list):
          self.cached_skip_values = cache
       else:
          logger.error("Error in caching skip values")
          logger.error(type(cache))
    def search_test_data(self,batch_data):
       test_data = 0
       try:
        i = 0
        for entry in self.cached_test_values:
            if entry[0] == batch_data.ingredientID:
                test_data = entry
                rownum = i
                break  
            i += 1
       except Exception as e:
          logger.error(e)
       if test_data == 0:
          logger.info("COULD NOT FIND TEST DATA IN CACHE. RECACHING...")
          self.cache_test_data_values(self.configs['test_request_sheet_ID'])
          
         
       i = 0
       for entry in self.cached_test_values:
                     try:  
   
                      if entry[0] == batch_data.ingredientID:

                          test_data = entry
                          rownum = i
                          
                          break  
                     
                     except Exception as e:
                      logger.error(e)
                     i += 1
       if test_data == 0:
          logger.error("COULD NOT FIND TEST DATA")
          return 0
       else:
          skip_value = self.get_skip_value(batch_data)
          if entry[7] == "PENDING":
              price = 0
          else: price = entry[7]
          data = td(ingredientID=entry[0],ingredient_name=entry[1],heavy_metals=yes_no_to_bool(entry[2]),routine_micros=yes_no_to_bool(entry[3]),standard_request=entry[4],request_method = entry[5],request_specs = entry[6],standard_price=price,skip=skip_value)
          return data
    def get_skip_value(self,batch):
              #return False #fix skip value check
              skip_data = "Not Found"
              
              column = None
              try:
              
               for entry in self.cached_skip_values:
                    
                    if entry[0] == batch.ingredientID and entry[1] == batch.vendor:
                       i = 0
                       for id in entry:
                          if id == batch.batchID:
                           column = i
                           break
                          i += 1  
              except Exception as e:
                 logger.error(e)
                 logger.error("here1")
              try:
                skip_data = skip_value_by_column(column)
              except Exception as e:
                  logger.error(e)
                  logger.error("here2")
              if str(skip_data) == "Not Found":
                 logger.info("COULD NOT FIND SKIP DATA IN CACHE. RECACHING...")
                 self.cache_skip_values(self.configs['skip_log_ID'])
                 try:
                        for entry in self.cached_skip_values:
                                            
                            if entry[0] == batch.ingredientID and entry[1] == batch.vendor:
                               i = 0
                               for id in entry:
                                 if id == batch.batchID:
                                   column = i
                                   break
                                 i += 1   
                 except Exception as e:
                           logger.error(e)
                           logger.error("here3")
                 try:
                    skip_data = skip_value_by_column(column)
                 except Exception as e:
                    logger.error(e)
                    logger.error("COULD NOT FIND SKIP DATA")
                    return 0
              if str(skip_data) == "Not Found":
                 logger.error("COULD NOT FIND SKIP DATA")
                 return 0
              else: return skip_data
    

    def search_data_from_sheet(self, batchID, type_material):
        if batchID == "":
           self.show_error("NO BATCH ID PROVIDED")
           return 1
        
        date = todays_date()
        match type_material:
           case 'R': #raw material
              try:
                month = month_from_batchID(batchID)
                sheetData = self.cached_RM_check_in_values[month]
                
              except Exception as e:
                 logger.debug(e)
                 return 0
           case 'P': #component
              try:
                month = month_from_batchID(batchID)
                sheetData = self.cached_component_check_in_values[month]
              except Exception as e:
                  logger.debug(e)
                  return 0
           case 'L': #label
                try:
                 if date == 0:
                    date,ok = QInputDialog.getText(self,"Label Recieving Date","Please input the label recieving date (MM/DD/YYYY)")
                    if not ok:
                       logger.info("USER CANCELLED LABEL REQUEST")
                       return 0
                 
                 month = convert_date_to_month_year(date)
                 sheetData = self.cached_label_check_in_values[month]
                except Exception as e:
                    logger.debug(str(e))
                    
                    return 0
           case _:
              logger.warning("Material Type Not supported")
              return 0
        row = 0
        zeroless_date = convert_between_date_formats(strip_date_zeros(date))
        try:
            for entry in sheetData['values']:
             try:
                row += 1
                
                if entry[0] == batchID and type_material != 'L':
                    
                    raw_material_info = entry
                    break   
                
                if type_material == 'L':
                      
                      if entry[0] == zeroless_date and entry[3] == batchID:
                          raw_material_info = entry
                          break
             except IndexError:
              logger.exception("FATAL APPLICATION ERROR")
              continue        
        except Exception: 
            logger.debug("Sheet Data could not be accessed")
            logger.exception("FATAL APPLICATION ERROR")
            return 0
        match type_material:
                   case 'R': #raw material
                       try:
                        data = raw_material_data(raw_material_info[0],raw_material_info[1],raw_material_info[2],raw_material_info[3],raw_material_info[4],raw_material_info[5],raw_material_info[9], raw_material_info[20],row=row)
                       except IndexError:
                        data = raw_material_data(raw_material_info[0],raw_material_info[1],raw_material_info[2],raw_material_info[3],raw_material_info[4],raw_material_info[5],raw_material_info[9],row=row)
                       except Exception as e:
                         logger.debug(e)
                         return 0
                   case 'P': #component
                      try:
                       data = raw_material_data(batchID=raw_material_info[0],ingredientID=raw_material_info[1],ingredient_name=raw_material_info[2],vendor=raw_material_info[3],vendor_lot_num=raw_material_info[4],PO_num=raw_material_info[5],expiration_date=raw_material_info[7], num_of_containers=raw_material_info[8],row=row)
                      except Exception as e:
                        logger.debug(e)
                        return 0
                   case 'L': #label
                    try:
                     data = raw_material_data(batchID=raw_material_info[3],ingredientID=raw_material_info[3],ingredient_name=raw_material_info[4],vendor=raw_material_info[5],vendor_lot_num=0,PO_num=raw_material_info[2],expiration_date="N/A", num_of_containers=raw_material_info[8],row=row)
                    except Exception as e:
                     logger.debug(e)
                     return 0                      
                   case _:
                      logger.warning("Material Type Not supported")
                      return 0
        return data
    def update_table(self):
       table = self.batchdatatable
       table.setRowCount(len(self.recent_requests))
       table.setColumnCount(10)
       table.setHorizontalHeaderLabels(["Batch ID", "Ingredient ID", "Name", "Vendor", "Vendor Lot #", "Expiration Date", "# Containers", "Duplicate Lot", "PO #", "Remove?"])

       for i, ([batchID,ingredientID,name,vendor,vendornum,expdate,numcontainers,duplot,ponum]) in enumerate(self.recent_requests):
          batch = QTableWidgetItem(batchID)
          ingredient = QTableWidgetItem(ingredientID)
          item_name = QTableWidgetItem(name)
          item_vendor = QTableWidgetItem(vendor)
          item_vendornum = QTableWidgetItem(vendornum)
          item_exp = QTableWidgetItem(expdate)
          num_of_conts = QTableWidgetItem(numcontainers)
          item_duplot = QTableWidgetItem(duplot)
          item_ponum = QTableWidgetItem(ponum)
          table.setItem(i, 0, batch)
          table.setItem(i, 1, ingredient)
          table.setItem(i, 2, item_name)
          table.setItem(i, 3, item_vendor)
          table.setItem(i, 4, item_vendornum)
          table.setItem(i, 5, item_exp)
          table.setItem(i, 6, num_of_conts)
          table.setItem(i, 7, item_duplot)
          table.setItem(i, 8, item_ponum)
          remove_button = QPushButton("✕") 
          remove_button.setStyleSheet(""" QPushButton { 
            color: red; 
            font-size: 16px; 
            font-weight: bold; 
            border: none; 
            background: transparent; 
            } QPushButton:hover { 
            color: darkred; 
            } """)
            # Store the current row index with the button 
          remove_button.clicked.connect( lambda checked=False, row=i: self.remove_recent_item(row) )  
          table.setCellWidget(i, 9, remove_button)
       self.batchdatatable = table
       self.update_test_table()
       return
    
    def update_test_table(self):
           table = self.testingtable
           table.setRowCount(len(self.to_be_tested))
           table.setColumnCount(4)
           table.setHorizontalHeaderLabels(["Batch ID", "Ingredient ID","Name","Remove?"])
    
           for i, ([batchID,ingredientID,name,vendor,vendornum,expdate,numcontainers,duplot,ponum]) in enumerate(self.to_be_tested):
              batch = QTableWidgetItem(batchID)
              ingredient = QTableWidgetItem(ingredientID)
              item_name = QTableWidgetItem(name)
              table.setItem(i, 0, batch)
              table.setItem(i, 1, ingredient)
              table.setItem(i, 2, item_name)
              # Remove button 
              remove_button = QPushButton("✕") 
              remove_button.setStyleSheet(""" QPushButton { 
              color: red; 
              font-size: 16px; 
              font-weight: bold; 
              border: none; 
              background: transparent; 
              } QPushButton:hover { 
              color: darkred; 
              } """)
              # Store the current row index with the button 
              remove_button.clicked.connect( lambda checked=False, row=i: self.remove_test_item(row) ) 
              table.setCellWidget(i, 3, remove_button)
           self.testingtable = table
           return

    def remove_test_item(self, row): 
       # Make sure the row is still valid 
       if 0 <= row < len(self.to_be_tested): 
          # Remove the corresponding entry from the underlying list 
          del self.to_be_tested[row] 
        # Rebuild the table 
       self.update_test_table()
    def remove_recent_item(self, row): 
       # Make sure the row is still valid 
       if 0 <= row < len(self.recent_requests): 
          # Remove the corresponding entry from the underlying list 
          del self.recent_requests[row] 
        # Rebuild the table 
       self.update_table()

    def create_labels_rm(self,batch_data):
        filename = "Labels/" + str(batch_data.ingredientID) + "-" + str(batch_data.batchID) + " label.pdf"
        label = Canvas(filename, pagesize= (10*inch, 5.5*inch))
        label.setFont("Times-Bold",75)
        label.drawString(0.5*inch,4*inch,"QC RM RELEASE")
        label.setFont("Times-Roman",35)
        label.drawString(0.5*inch,3*inch,"Item: ")
        label.drawString(6*inch,3*inch,"Lot: ")
        label.drawString(0.5*inch,2*inch,"Date: ")
        label.drawString(6*inch,2*inch,"By: ")
        label.drawString(1.5*inch,1*inch,"Expiration Date: ")
        label.setFont("Times-Bold",40)
        label.drawString(2*inch,3*inch,str(batch_data.ingredientID))
        label.drawString(7.5*inch,3*inch,str(batch_data.batchID))
        label.drawString(2*inch,2*inch,todays_date())
        label.drawString(7.5*inch,2*inch,self.configs['initials'])
        label.drawString(5*inch,1*inch,batch_data.expiration_date)
        #drawing = Drawing()
        #drawing.add(Line(1*inch,4*inch,2*inch,4*inch))
        label.save()
        #renderPDF.drawToFile(drawing, filename)
        return filename
    def create_labels_comp(self,batch_data):
        filename = "Labels/" + str(batch_data.ingredientID) + "-" + str(batch_data.batchID) + " label.pdf"
        label = Canvas(filename, pagesize= (10*inch, 5.5*inch))
        label.setFont("Times-Bold",50)
        label.drawString(0.5*inch,4*inch,"QC COMPONENT RELEASE")
        label.setFont("Times-Roman",35)
        label.drawString(0.5*inch,1*inch,"Name: ")
        label.drawString(6*inch,3*inch,"Lot: ")
        label.drawString(0.5*inch,1.5*inch,"Date: ")
        label.drawString(0.5*inch,2.25*inch,"Component Code: ")
        label.drawString(6*inch,1.5*inch,"By: ")
        label.drawString(0.5*inch,3*inch,"PO: ")
        label.setFont("Times-Bold",40)
        label.drawString(7.5*inch,3*inch,str(batch_data.batchID))
        label.drawString(2*inch,1.5*inch,todays_date())
        label.drawString(7.5*inch,1.5*inch,self.configs['initials'])
        label.drawString(2*inch,3*inch,batch_data.PO_num)
        label.drawString(5*inch,2.25*inch,batch_data.ingredientID)
        label.setFont("Times-Bold",20)
        label.drawString(2*inch,1*inch,str(batch_data.ingredient_name))
        #drawing = Drawing()
        #drawing.add(Line(1*inch,4*inch,2*inch,4*inch))
        label.save()
        #renderPDF.drawToFile(drawing, filename)
        return filename
    def create_labels_labels(self,batch_data):
        filename = "Labels/" + str(batch_data.ingredientID) + "-" + tt.strftime("%Y%m%d") + " label.pdf"
        label = Canvas(filename, pagesize= (10*inch, 5.5*inch))
        label.setFont("Times-Bold",50)
        label.drawString(1.5*inch,4.5*inch,"QC LABEL RELEASE")
        label.setFont("Times-Roman",35)
        label.drawString(0.5*inch,3.75*inch,"Product: ")
        label.drawString(0.5*inch,3*inch,"PO: ")
        label.drawString(4*inch,3*inch,"Date: ")
        label.drawString(0.5*inch,2*inch,"Label Code: ")
        label.drawString(0.5*inch,1*inch,"By: ")
        label.setFont("Times-Bold",40)
        label.drawString(1.5*inch,3*inch,batch_data.PO_num)
        label.drawString(5.5*inch,3*inch,todays_date())
        label.drawString(1.5*inch,1*inch,self.configs['initials'])
        label.drawString(4*inch,2*inch,batch_data.ingredientID)
        label.setFont("Times-Bold",25)
        label.drawString(2.5*inch,3.75*inch,str(compact_label_name(batch_data.ingredient_name)))
        #drawing = Drawing()
        #drawing.add(Line(1*inch,4*inch,2*inch,4*inch))
        label.save()
        #renderPDF.drawToFile(drawing, filename)
        return filename
    def create_labels_clicked(self):
       if not self.most_recent_request:
          self.display_clicked()
       if not self.selected_request: 
          try:
           request = self.most_recent_request
          except:
             logger.error("NO BATCH ID PROVIDED")
             self.show_error("NO BATCH ID PROVIDED")
             return
       else: request = self.selected_request
       request = self.most_recent_request
       batch_data = request
       if batch_data == None or batch_data.batchID in (0, 1):
          logger.error("NO BATCH ID PROVIDED")
          self.show_error("NO BATCH ID PROVIDED")
          return
       try:
        type_material = batch_data.batchID[0]
        if len(batch_data.batchID) >= 9:
            type_material = 'L'
        match type_material:
            case 'R':
                
                filename = self.create_labels_rm(batch_data)
                if int(batch_data.num_of_containers) <= 100:
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "Print " + batch_data.num_of_containers + " labels")
                else: 
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "WARNING: " + batch_data.num_of_containers + " LABELS REQUESTED. ASK FOR CLARITY.")
                if self.timestamp:
                    batch_data.row = row_num = str(int(batch_data.batchID[4] + batch_data.batchID[5] + batch_data.batchID[6]) + 1)
                    timestamp_sample(self.configs['RM_check_in_sheet_ID'],batch_data.row)
                    self.timestamp_label.setText("Sample Timestamped")
            case 'P':
                filename = self.create_labels_comp(batch_data) 
                if int(batch_data.num_of_containers) <= 100:
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "Print " + batch_data.num_of_containers + " labels")
                else: 
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "WARNING: " + batch_data.num_of_containers + " LABELS REQUESTED. ASK FOR CLARITY.")
                if self.timestamp:
                    batch_data.row = row_num = str(int(batch_data.batchID[4] + batch_data.batchID[5] + batch_data.batchID[6]) + 1)
                    timestamp_sample(self.configs['component_check_in_sheet_ID'],batch_data.row)
                    self.timestamp_label.setText("Sample Timestamped")
            case 'L':
                filename = self.create_labels_labels(batch_data) 
                if int(batch_data.num_of_containers) <= 100:
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "Print " + batch_data.num_of_containers + " labels")
                else: 
                    self.create_labels_label.setText("Labels created in " + filename + '\n' + "WARNING: " + batch_data.num_of_containers + " LABELS REQUESTED. ASK FOR CLARITY.")
                if self.timestamp:
                    timestamp_sample(self.configs['label_check_in_sheet_ID'],batch_data.row,"!M")
                    self.timestamp_label.setText("Sample Timestamped")        
            case _: 
                self.create_labels_label.setText("Error in creating labels")
                return
        
        self.labelsthread.filename = filename
        self.labelsthread.configs = self.configs
        self.labelsthread.start()
        self.labels_created.append([batch_data.ingredientID + " " + batch_data.batchID, "SUCCESSFULLY CREATED LABELS"])
        if self.timestamp:
            self.batches_released.append([batch_data.ingredientID + " " + batch_data.batchID + " ", "BATCH RELEASED"])
       except Exception as e:
          logger.error(str(e))
          self.show_error(str(e)) 
          self.labels_created.append([batch_data.ingredientID + " " + batch_data.batchID+ " ", "FAILED TO CREATE LABELS"])
          return
      
    def display_clicked(self):
        self.timestamp_label.setText("")
        self.progressBar.setValue(0)
        batchID = self.batchIDinput.text().upper()
        try:
            type_material = batchID[0]
        except Exception as e:
            logger.error(e)
            self.show_error("NO BATCH ID PROVIDED")
            return
        if len(batchID) < 7 or (len(batchID) > 7 and len(batchID) < 9):
            try:
               self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
               self.progressBar.setValue(0)
               self.recent_data_label.setText("Could not find batch data")
               logger.warning("Could not find batch data")
            except Exception:
                logger.exception("FATAL APPLICATION ERROR")
            return
        if len(batchID) >= 9:
            type_material = 'L'
        self.progressBar.setValue(5)
        batch_data = self.search_data_from_sheet(batchID,type_material)
        self.progressBar.setValue(10)
        if batch_data == 1: 
           self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
           self.progressBar.setValue(0)
           return
        if batch_data == 0:          
            match type_material:
               case 'R':
                  sheetID = self.configs['RM_check_in_sheet_ID'] 
               case 'P':
                  sheetID = self.configs['component_check_in_sheet_ID'] 
               case 'L':
                    sheetID = self.configs['label_check_in_sheet_ID']
               case _:
                  self.recent_data_label.setText("Material Type Not Supported")
                  logger.warning("Material Type Not Supported")
                  self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
                  return
            self.progressBar.setValue(15)
            date = 0
            if type_material == 'L':
                if date == 0:
                    try:
                            date,ok = QInputDialog.getText(self,"Label Recieving Date","Please input the label recieving date (MM/DD/YYYY)")
                            if not ok:
                             logger.info("USER CANCELLED LABEL REQUEST")
                             return 0
                            month = convert_date_to_month_year(date)
                    except Exception as e:
                        logger.error(str(e))
                        self.show_error("ERROR IN INPUT")
                        return
            else: month = month_from_batchID(batchID)
            self.progressBar.setValue(20)
            self.cache_check_in_values(sheetID,month,type_material)
            self.progressBar.setValue(30)
            batch_data=self.search_data_from_sheet(batchID,type_material)
            self.progressBar.setValue(40)
        if batch_data == 0:
           self.recent_data_label.setText("Could not find batch data")
           logger.warning("Could not find batch data")
           self.progressBar.setValue(0)
           self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
           return
        batch_data.print_data()
        self.batches_searched.append([batchID + " ",batch_data.ingredientID + " ","FOUND SUCCESSFULLY"])
        pyperclip.copy(batch_data.ingredientID + " " + batch_data.batchID + " " + todays_date())
        self.most_recent_request = batch_data
        self.write_batch_to_file()
        self.progressBar.setValue(50)
        self.recent_requests.append(batch_data.list_form())
        self.to_be_tested.append(batch_data.list_form())
        self.progressBar.setValue(75)
        self.update_table()
        self.recent_data_label.setText(batch_data.batchID + "," + batch_data.ingredientID + "," + batch_data.ingredient_name)
        self.progressBar.setValue(100)
        
    def search_sheet_clicked(self):
       if not self.batchIDinput:self.display_clicked()
        #this multithreading mess should move all the searching, annotating, and opening of a test sheet into another thread
       self.search_sheet_worker = search_sheet_worker()
       self.search_sheet_worker.configs = self.configs
       batchID = self.batchIDinput.text().upper()
       type_material = batchID[0]
       if len(batchID) < 7 or (len(batchID) > 7 and len(batchID) < 9):
            self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
            self.progressBar.setValue(0)
            self.recent_data_label.setText("Could not find batch data")
            logger.warning("Could not find batch data")
            return
       if len(batchID) >= 9:
            type_material = 'L'
       self.search_sheet_worker.most_recent_request = self.search_data_from_sheet(batchID,type_material)
       self.search_sheet_worker.selected_request = self.selected_request
       self.search_sheet_worker.annotate = self.annotate
       self.search_sheet_worker.error.connect(self.show_error)
       self.search_sheet_worker.progress.connect(self.update_test_sheet_progress_bar)
       self.search_sheet_worker.complete.connect(self.kill_search_thread)
       self.search_sheet_thread = QThread()
       self.search_sheet_thread.started.connect(self.search_sheet_worker.find_test_data_sheet)
       self.search_sheet_worker.moveToThread(self.search_sheet_thread)
       self.search_sheet_thread.start()
       
    def release_clicked(self):
       self.display_clicked()
       self.search_sheet_clicked()
       self.create_labels_clicked()
    def tustinbuttonclicked(self):
       self.tustinbar.setValue(0)
       progress_chunk = 50/8
       dummy_batch = raw_material_data("","","","","","","","","","")
       dummy_test_data = td("","","","","","","","","")
       for i in range(8): #erase previous SSF entries
        progress = (i+1)*progress_chunk
        write_to_ssf(dummy_batch,dummy_test_data,self.configs["ssf_sheet_ID"],self.configs["testing_log_sheet_ID"],11+i,blank=True)
        self.tustinbar.setValue(math.floor(progress))
       i = 0
       self.tustinbar.setValue(50)
       for entry in self.to_be_tested.copy():
          if i > 7:
             return
          batch = list_form_to_class_form(entry)
          progress = 50+(i+1)*progress_chunk
          data = self.search_test_data(batch)
          if yes_no_to_bool(batch.is_duplicate_lot):
              self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "TEST SKIPPED DUE TO LOT DUPLICATION"])
              logger.info("BATCH ID: " + batch.batchID + " SKIPPED DUE TO LOT DUPLICATION")
              self.show_error("BATCH ID: " + batch.batchID + " SKIPPED DUE TO LOT DUPLICATION")
              self.remove_test_item(self.to_be_tested.index(entry))
              self.update_test_table()
              continue
          if data == 0:
             data = td(ingredientID=batch.ingredientID,ingredient_name=batch.ingredient_name,heavy_metals=True,routine_micros=True,standard_request="",standard_price="",skip=False)
          result = write_to_ssf(batch,data,self.configs["ssf_sheet_ID"],self.configs["testing_log_sheet_ID"],11+i)
          if result == "SKIPPED":
              logger.info("BATCH ID: " + batch.batchID + " SKIPPED")
              self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "TEST SKIPPED DUE TO SLE STATUS"])
              self.show_error("BATCH ID: " + batch.batchID + " SKIPPED DUE TO SLE STATUS")
              self.remove_test_item(self.to_be_tested.index(entry))
              self.update_test_table()
              continue
          self.tustinbar.setValue(math.floor(progress))
          i+=1
          price = 0
          if data.heavy_metals:
            price += self.heavy_metals_price
            if data.routine_micros:
                price += self.routine_micros_price
                if data.standard_request != "PENDING":
                    if data.standard_price != "PENDING": price += int(data.standard_price)
                    self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "REQUESTED HEAVY METALS, ROUTINE MICROS, AND " + data.standard_request + " BY METHOD OF " + data.request_method + " FOR AN ESTIMATED TOTAL PRICE OF $" + str(price)])
                else:
                    self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "REQUESTED HEAVY METALS, AND ROUTINE MICROS FOR AN ESTIMATED TOTAL PRICE OF $" + str(price)])
            elif data.standard_request != "PENDING":
                self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "REQUESTED HEAVY METALS, AND " + data.standard_request + " BY METHOD OF " + data.request_method + " FOR AN ESTIMATED TOTAL PRICE OF $" + str(price)])
            else:
             self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "REQUESTED HEAVY METALS, FOR AN ESTIMATED TOTAL PRICE OF $" + str(price)])
          else:
             self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "NO HEAVY METALS REQUESTED"])
          self.total_price_of_tests += int(price)
          self.remove_test_item(self.to_be_tested.index(entry))
          self.update_test_table()
       self.tustinbar.setValue(100)
       
    def kill_search_thread(self,complete,id,error):
       if complete:
          self.test_sheets_searched.append([id + " ",error])
          self.search_sheet_thread.quit()  
    def update_test_sheet_progress_bar(self,progress):
       self.testsheetprogressbar.setValue(progress)
    def show_error(self, message):
        QMessageBox.critical(
            self,
            "Error",
            message
        )
          
        
    
    


if __name__ == "__main__":
    
    logger = logging.getLogger(__name__)
    logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.DEBUG)
    logger.debug('\n' + "--APPLICATION LAUNCHED AT " + str(datetime.now()) + "--" + '\n')
    config = read_config()
    logger.info(config)
    logger.info("QC Release 1.0.3 update test")
    try:
        app = QApplication(sys.argv)
        app.setWindowIcon(QIcon(str(APP_DIR / "jetpack_icon.ico")))
        window = MyApp()
        window.configs = config
        window.show()
        check_for_updates()
        update_timer = QTimer()
        update_timer.timeout.connect(window.check_update_ready)
        update_timer.start(1000)
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(e)
        logger.exception("FATAL APPLICATION ERROR")
        sys.exit(app.exec_())
        raise
        
