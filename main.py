import sys
import math
from time import time as t
import time as tt
import re
import os
import subprocess
import json
from datetime import datetime, timedelta

#GUI
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMessageBox, QPushButton, QInputDialog, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QThread, pyqtSignal, QObject,QTimer,QDate
from qcrelease import Ui_QCRelease

#graceful handling
import configparser
import logging

#timed reports
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.use("Agg")


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
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image
)
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from pathlib import Path

APP_VERSION = "1.2.2"
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
                            logger.info(status)
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

from PyQt5.QtCore import QThread, pyqtSignal


class ReportWorker(QThread):

    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(
        self,
        selected_time,
        pivot_date,
        skip_data,
        test_data,
        check_in_data,
        month,
        sheetID,
        overall_sle_data,
        output_path,
        sle_changes
    ):
        super().__init__()

        self.selected_time = selected_time
        self.pivot_date = pivot_date
        self.skip_data = skip_data
        self.test_data = test_data
        self.check_in_data = check_in_data
        self.month = month
        self.sheetID = sheetID
        self.overall_sle_data = overall_sle_data
        self.output_path = output_path
        self.sle_changes = sle_changes

    def run(self):

        try:

            self.progress.emit(0)

            # -----------------------------
            # CREATE REPORT DATA
            # -----------------------------

            r = timed_report(
                self.selected_time,
                self.pivot_date,
                self.skip_data,
                self.test_data,
                self.sle_changes
            )

            self.progress.emit(10)
            #r.get_top_25_sle()
            self.progress.emit(20)
            r.get_incoming(
                self.check_in_data,
                self.month
            )
            if r.selected_time == "ytd":
                months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                
                month_num = int(self.pivot_date[0:2])
                for i in range(month_num):
                    month = months[i]
                    year = self.pivot_date[6:10]
                    date_string = month + " " + year
                    month_year = date_string.upper()
                    r.get_incoming(self.check_in_data,
                                    month_year)
            self.progress.emit(30)

            r.get_test_log(
                self.sheetID
            )

            self.progress.emit(50)

            r.get_overall_sle(
                self.overall_sle_data
            )

            self.progress.emit(60)

            r.print_values()

            self.progress.emit(70)

            # -----------------------------
            # CREATE PDF
            # -----------------------------

            pdf = PDFReport(
                r,
                self.output_path,
                r.selected_time
                
            )

            pdf.create_pdf()

            self.progress.emit(100)

            self.finished.emit(str(self.output_path))

        except Exception as e:

            logger.exception("Error creating report")

            self.error.emit(str(e))

    def pdf_progress(self, value):

        # PDF is 70-100% of total operation
        overall_progress = 70 + int(value * 0.30)

        self.progress.emit(overall_progress)     

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
class PDFReport:
    selected_time = "week"
    selected_time_ly = "Weekly"

    def time_to_timely(self):
       match (self.selected_time):
          case "day":
             self.selected_time_ly = "Daily"
          case "week":
             self.selected_time_ly = "Weekly"
          case "month":
             self.selected_time_ly = "Monthly"
          case "ytd":
            self.selected_time = "year"
            self.selected_time_ly = "Yearly"
          case _:
             self.selected_time_ly = "N/A"

    def __init__(self, report, output_path,selected_time):
        """
        report      = completed timed_report object
        output_path = location where the PDF should be created
        """
        self.selected_time = selected_time
        self.time_to_timely()
        self.report = report
        self.output_path = Path(output_path)

        # Folder for temporary chart images
        self.chart_folder = self.output_path.parent / "report_charts"
        self.chart_folder.mkdir(exist_ok=True)

        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Title"],
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            spaceAfter=12
        )

        self.section_style = ParagraphStyle(
            "Section",
            parent=self.styles["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=8
        )

        self.subsection_style = ParagraphStyle(
            "Subsection",
            parent=self.styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=5
        )

        self.normal_style = ParagraphStyle(
            "NormalReport",
            parent=self.styles["Normal"],
            fontSize=9,
            leading=12
        )

        self.story = []

    # ---------------------------------------------------------
    # MAIN PDF CREATION
    # ---------------------------------------------------------

    def create_pdf(self):
        """
        Creates the complete PDF report.
        """

        doc = SimpleDocTemplate(
            str(self.output_path),
            pagesize=letter,
            rightMargin=0.55 * inch,
            leftMargin=0.55 * inch,
            topMargin=0.55 * inch,
            bottomMargin=0.55 * inch
        )

        self.story = []

        self.add_summary_page()
        self.story.append(PageBreak())

        self.add_skip_progress_page()
        #self.story.append(PageBreak())

        self.add_sle_changes_page()
        self.story.append(PageBreak())

        self.add_top_25_page()

        doc.build(
            self.story,
            onFirstPage=self.add_page_number,
            onLaterPages=self.add_page_number
        )

        self.cleanup_charts()

        return str(self.output_path)

    # ---------------------------------------------------------
    # PAGE NUMBER
    # ---------------------------------------------------------

    def add_page_number(self, canvas, doc):
        canvas.saveState()

        canvas.setFont("Helvetica", 8)

        canvas.drawRightString(
            letter[0] - 0.55 * inch,
            0.3 * inch,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    # ---------------------------------------------------------
    # PAGE 1
    # ---------------------------------------------------------

    def add_summary_page(self):

        start_date, end_date = self.get_report_dates()

        self.story.append(
            Paragraph(
                f"RM QC Report for the {self.selected_time} of {start_date}",
                self.title_style
            )
        )

        self.story.append(Spacer(1, 0.15 * inch))

        self.story.append(
            Paragraph(
                f"{self.selected_time_ly} Summary",
                self.section_style
            )
        )

        incoming = len(self.report.incoming['values'])
        duplicates = len(self.report.duplicate_lots)
        skips = len(self.report.sle_skips)

        tested = incoming - duplicates - skips

        summary_data = [
            ["Metric", "Value"],
            ["Incoming ingredients", str(incoming)],
            ["Duplicates", str(duplicates)],
            ["SLE skips", str(skips)],
            ["Tested", str(tested)],
            [
                "Estimated total cost of tests",
                f"${self.report.total_cost:,.2f}"
            ]
        ]

        self.story.append(
            self.make_table(
                summary_data,
                widths=[4.5 * inch, 2.0 * inch]
            )
        )

        self.story.append(Spacer(1, 0.25 * inch))

        self.story.append(
            Paragraph(
                "Testing Breakdown",
                self.section_style
            )
        )

        chart_path = self.create_testing_pie_chart(
            tested,
            skips,
            duplicates
        )

        self.story.append(
            Image(
                str(chart_path),
                width=5.0 * inch,
                height=3.5 * inch
            )
        )

    # ---------------------------------------------------------
    # PAGE 2
    # ---------------------------------------------------------

    def add_skip_progress_page(self):

        self.story.append(
            Paragraph(
                "Skip Lot Progress",
                self.title_style
            )
        )

        self.story.append(
            Paragraph(
                "SLE Status of Ingredients Received During the Reporting Period",
                self.section_style
            )
        )

        # ---------------------------------------------
        # SLE PIE CHARTS
        # ---------------------------------------------

        weekly_chart = self.create_sle_pie_chart(
            self.report.sle_graph_values,
            self.report.sle_graph_labels,
            f"{self.selected_time_ly} SLE Status"
        )

        overall_chart = self.create_sle_pie_chart(
            self.report.overall_sle_values,
            self.report.sle_graph_labels,
            "Overall SLE Status"
        )

        # Create smaller images so both fit on the same page
        weekly_image = Image(
            str(weekly_chart),
            width=3.1 * inch,
            height=2.3 * inch
        )

        overall_image = Image(
            str(overall_chart),
            width=3.1 * inch,
            height=2.3 * inch
        )

        # Put both charts side-by-side
        chart_table = Table(
            [
                [
                    Paragraph(
                        f"{self.selected_time_ly} SLE Distribution",
                        self.subsection_style
                    ),
                    Paragraph(
                        "Overall SLE Status",
                        self.subsection_style
                    )
                ],
                [
                    weekly_image,
                    overall_image
                ]
            ],
            colWidths=[3.25 * inch, 3.25 * inch]
        )

        chart_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),

                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ])
        )

        self.story.append(chart_table)

    # ---------------------------------------------------------
    # PAGE 3
    # ---------------------------------------------------------

    def add_sle_changes_page(self):

        self.story.append(
            Paragraph(
                "SLE Status Changes",
                self.title_style
            )
        )

        self.story.append(
            Paragraph(
                "SLE Status Changes During the Reporting Period",
                self.section_style
            )
        )

        if not self.report.sle_changes:

            self.story.append(
                Paragraph(
                    "No SLE status changes were recorded during this reporting period.",
                    self.normal_style
                )
            )

            return

        table_data = [
            [
                "Ingredient",
                "Vendor",
                "Previous SLE",
                "New SLE"
            ]
        ]

        for key, change in self.report.sle_changes.items():

            # Key is:
            # "INGREDIENT VENDOR"

            parts = key.split(" ", 1)

            ingredient = parts[0]
            vendor = parts[1] if len(parts) > 1 else ""

            table_data.append([
                ingredient,
                vendor,
                str(change.get("old", "")),
                str(change.get("new", ""))
            ])

        self.story.append(
            self.make_table(
                table_data,
                widths=[
                    1.5 * inch,
                    2.5 * inch,
                    1.0 * inch,
                    1.0 * inch
                ]
            )
        )

    # ---------------------------------------------------------
    # PAGE 4
    # ---------------------------------------------------------

    def add_top_25_page(self):

        self.story.append(
            Paragraph(
                "Top 25 Ingredients",
                self.title_style
            )
        )

        self.story.append(
            Paragraph(
                "Lots Received and SLE Status",
                self.section_style
            )
        )

        table_data = [
            [
                "Ingredient",
                "Lots Received",
                "SLE Status"
            ]
        ]

        for ingredient in self.report.top_25_ingredients:

            data = self.report.top_25_data.get(
                ingredient,
                []
            )

            lot_count = len(data) - 1

            # Get the SLE status from the stored data.
            # Your current format is:
            # [batchID, "SLE STATUS: X"]

            sle_statuses = []

            for entry in data:

                if len(entry) >= 2:

                    status = str(entry[1])

                    if "SLE STATUS:" in status:
                        status = status.replace(
                            "SLE STATUS:",
                            ""
                        ).strip()

                        sle_statuses.append(status)

            if sle_statuses:

                # Display the most recently encountered status.
                sle_status = sle_statuses[-1]

            else:
                sle_status = "N/A"

            table_data.append([
                ingredient,
                str(lot_count),
                sle_status
            ])

        self.story.append(
            self.make_table(
                table_data,
                widths=[
                    3.0 * inch,
                    1.5 * inch,
                    1.5 * inch
                ]
            )
        )
# ---------------------------------------------------------
# CHARTS
# ---------------------------------------------------------

    def create_testing_pie_chart(self, tested, skips, duplicates):

        values = [tested, skips, duplicates]
        logger.info(f"ACTUAL PIE VALUES: {values}")
        labels = ["Tested", "SLE Skips", "Duplicates"]

        total = sum(values)

        legend_labels = [
            f"{label} ({value / total * 100:.1f}%)" if total else f"{label} (0.0%)"
            for label, value in zip(labels, values)
        ]

        path = self.chart_folder / "testing_breakdown.png"

        fig, ax = plt.subplots(figsize=(6.5, 5))

        wedges, _ = ax.pie(
            values,
            startangle=90,
            counterclock=False,
            colors=[
                "#4C78A8",  # muted blue
                "#F2B134",  # muted amber
                "#D95F59"   # muted red
            ],
            wedgeprops={
                "linewidth": 1.5,
                "edgecolor": "white"
            }
        )

        ax.legend(
            wedges,
            legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.08),
            ncol=3,
            frameon=False
        )

        ax.set_title(
            "Testing Requests",
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.axis("equal")

        fig.tight_layout()
        fig.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return path


    def create_sle_pie_chart(self, values, labels, title):

        total = sum(values)

        legend_labels = [
            f"{label} ({value / total * 100:.1f}%)" if total else f"{label} (0.0%)"
            for label, value in zip(labels, values)
        ]

        path_name = title.lower().replace(" ", "_")
        path = self.chart_folder / f"{path_name}.png"

        fig, ax = plt.subplots(figsize=(6.5, 5))

        wedges, _ = ax.pie(
            values,
            startangle=90,
            counterclock=False,
            colors=[
                "#264653",
                "#2A9D8F",
                "#52B788",
                "#8AB17D",
                "#E9C46A",
                "#F4A261"
            ],
            wedgeprops={
                "linewidth": 1.5,
                "edgecolor": "white"
            }
        )

        ax.legend(
            wedges,
            legend_labels,
            loc="lower center",
            bbox_to_anchor=(0.5, -0.08),
            ncol=3,
            frameon=False
        )

        ax.set_title(
            title,
            fontsize=14,
            fontweight="bold",
            pad=15
        )

        ax.axis("equal")

        fig.tight_layout()
        fig.savefig(path, dpi=200, bbox_inches="tight")
        plt.close(fig)

        return path

    # ---------------------------------------------------------
    # TABLE CREATOR
    # ---------------------------------------------------------

    def make_table(self, data, widths=None):

        table = Table(
            data,
            colWidths=widths,
            repeatRows=1
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica"
                ),

                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                )
            ])
        )

        return table

    # ---------------------------------------------------------
    # DATE
    # ---------------------------------------------------------

    def get_report_dates(self):

        # Your pivot_date is already the date used by
        # timed_report. For a weekly report, calculate
        # Monday through Sunday.

        try:

            from datetime import datetime, timedelta

            date = datetime.strptime(
                self.report.pivot_date,
                "%m/%d/%Y"
            )

            monday = date - timedelta(
                days=date.weekday()
            )

            sunday = monday + timedelta(days=6)

            return (
                monday.strftime("%m/%d/%y"),
                sunday.strftime("%m/%d/%y")
            )

        except Exception:

            return (
                str(self.report.pivot_date),
                str(self.report.pivot_date)
            )

    # ---------------------------------------------------------
    # CLEANUP
    # ---------------------------------------------------------

    def cleanup_charts(self):

        if not self.chart_folder.exists():
            return

        for file in self.chart_folder.iterdir():

            try:
                file.unlink()
            except Exception:
                pass

        try:
            self.chart_folder.rmdir()
        except Exception:
            pass
class timed_report():
       available_times = ["day","week","month","ytd"] #how long the report will cover. ytd = year-to-date
       selected_time = ""
       pivot_date = ""
 #should always equal unrecieved + released - give or take a little
       unrecieved = [] 
       released = []
       duplicate_lots = []
       sle_skips = []
       total_cost = 0
       percent_skipped = 0 #len(duplicate_lots) + len(sle_skips) / len(released)
       percent_duplicates = 0 
       percent_sle_skipped = 0
       
       percent_at_sle_x = []
       skip_data = []
       sle_values = []
       sle0 = []
       sle1 = []
       sle2 = []
       sle3 = []
       sle4 = []
       sle5 = []
       sle0_5 = []
       test_log = []
       tests_requested_within_timeframe = []
       test_data = []
       incoming_ingredients = set()
       
       #report variables
       sle_graph_labels = ["SLE0", "SLE1","SLE2","SLE3","SLE4","SLE5"]
       sle_graph_values = []
       skipped_graph_labels = ["Tested","SLE Skips","Duplicates"]
       skipped_graph_values = []
       overall_sle_values = []

       #important ingredient codes
       top_25_ingredients = ['BRP000U','CPB000U','BRF000P','MRG000P','MCC102P','AML000P','OLE020S','ECH004S','RBR000P','POM000P','GQD000P','JCI-160','BRP000U','BBG097S','AAC000P','DLF041C','OFE101C','BDR000P','MGS000P','DCP023S','RSV098S','GMO060S','LEU000P','THE000P','MGG040S']
       top_25_data = {}
       top_25_sle = {}
       def sle_pie_chart(self,sle_values):
          plt.pie(sle_values,labels=self.sle_graph_labels)
          plt.title("SLE STATUS")
          

       def skipped_pie_chart(self,skipped_graph_values):
          plt.pie(self.skipped_graph_values,labels=self.skipped_graph_labels)
          plt.title("TESTING REQUESTS")
          

       def __init__(self,selected_time,pivot_date,skip_data,test_data,sle_changes):
        logger.info(f"--Report initiated for {selected_time}--")
        
        if self.valid_selected_time(selected_time):
           
           self.selected_time = selected_time
        else:
           
           self.selected_time = "week"
        self.pivot_date = pivot_date
        self.skip_data = skip_data
        self.test_data = test_data
        self.sle_changes = sle_changes
        for ingredient in self.top_25_ingredients:
           self.top_25_data[ingredient] = []

        self.unrecieved = []
        self.released = []
        self.duplicate_lots = []
        self.sle_skips = []

        self.percent_at_sle_x = []

        self.sle_values = []

        self.sle0 = []
        self.sle1 = []
        self.sle2 = []
        self.sle3 = []
        self.sle4 = []
        self.sle5 = []
        self.sle0_5 = []

        self.test_log = []
        self.tests_requested_within_timeframe = []

        self.incoming_ingredients = set()

        self.sle_graph_values = []
        self.skipped_graph_values = []
        self.overall_sle_values = []

        self.total_cost = 0
        self.get_top_25_sle()

       def valid_selected_time(self,selected_time):
          if selected_time in self.available_times:
             logger.info("Selected time valid")
             return True
          else:
            logger.warning("Selected time invalid")
            return False

       def check_valid_date(self,indate):
        try:
          date = convert_between_date_formats(strip_date_zeros(indate))
          pivot_date = convert_between_date_formats(strip_date_zeros(self.pivot_date))
          date_range = self.selected_time

          match (date_range):
            case "day":
                if pivot_date == date:
                   return True
                else:
                   return False
            case "week":
                dt = datetime.strptime(pivot_date,"%m/%d/%Y")
                week = [
                     convert_between_date_formats(strip_date_zeros((dt - timedelta(days=dt.weekday()) + timedelta(days=i)).strftime("%m/%d/%Y")))
                     for i in range(7)
                                    ]
                
                if date in week:
                   
                   return True
                else:
                   return False
                
            case "month":
                try:
                    pivot_month = datetime.strptime(
                        pivot_date,
                        "%m/%d/%Y"
                    ).month

                    date_month = datetime.strptime(
                        date,
                        "%m/%d/%Y"
                    ).month

                    return pivot_month == date_month

                except:
                    logger.exception("Invalid date")
                    return False

            case "ytd":
                try:

                    if pivot_date[-2:] == date[-2:]:

                     return True
                    else:
                     return False
                except:
                    logger.exception("Invalid date")
                    return False
            case _:
                return False
        except:
           logger.error("Error in check_valid_date")
           return True


       def search_test_data(self,batchID,ingredientID,vendor):
              test_data = 0
              try:
               i = 0
               for entry in self.test_data:
                   if entry[0] == ingredientID:
                       test_data = entry
                       rownum = i
                       break  
                   i += 1
              except Exception as e:
                 logger.error(e)
              if test_data == 0:
                 logger.info("COULD NOT FIND TEST DATA IN CACHE. RECACHING...")
                 self.test_data(self.configs['test_request_sheet_ID'])
                 
                
              i = 0
              for entry in self.test_data:
                            try:  
          
                             if entry[0] == ingredientID:
       
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
                 skip_value = self.get_skipped(ingredientID,vendor,batchID)
                 try:
                   if entry[7] == "PENDING" or entry[7] == None:
                     price = 0
                   else: price = entry[7]

                 except Exception as e:
                    logger.exception(e)
                    price = 0
                 
                 data = td(ingredientID=entry[0],ingredient_name=entry[1],heavy_metals=yes_no_to_bool(entry[2]),routine_micros=yes_no_to_bool(entry[3]),standard_request=entry[4],request_method = entry[5],request_specs = entry[6],standard_price=price,skip=skip_value)
                 
                 self.total_cost += int(data.standard_price)
                 
                 return data
       
       def get_sle_status(self,ingredientID,vendor,skip_data):
            for entry in skip_data:
             if len(entry) < 4:
              continue
             try:
                 if entry[2].strip() == ingredientID.strip() and entry[3].strip() == vendor.strip():

                    return int(entry[0])
             except IndexError:
                pass
                
       def seperate_by_sle_status(self):
          for entry in self.sle_values:
             match entry[3]:
                case 0:
                   self.sle0.append(entry)
                case 1:
                   self.sle1.append(entry)
                case 2:
                   self.sle2.append(entry)
                case 3:
                   self.sle3.append(entry)
                case 4:
                   self.sle4.append(entry)
                case 5:
                   self.sle5.append(entry)
                case _:
                   logger.info("Failed to assign entry")
          self.sle0_5.append(self.sle0)
          self.sle0_5.append(self.sle1)
          self.sle0_5.append(self.sle2)
          self.sle0_5.append(self.sle3)
          self.sle0_5.append(self.sle4)
          self.sle0_5.append(self.sle5)
                    
       def get_incoming(self,check_in_data,month):

          new_values = []

          for row in check_in_data[month]['values']:
                if not row or not str(row[0]).strip():
                    continue

                # YTD already gets the correct months from test_report()
                if self.selected_time == "ytd":
                    new_values.append(row)
                    continue

                # Other report types need date filtering
                try:
                    if self.check_valid_date(row[13]):
                        new_values.append(row)
                except IndexError:
                    # No date available, so add without date checking
                    new_values.append(row)
          if not hasattr(self, 'incoming'):
            self.incoming = {'values': []}
            logger.info(
                f"GET_INCOMING START: {month} | "
                f"current total = {len(self.incoming['values']) if hasattr(self, 'incoming') else 0}")
         
          logger.info(f"{month}: adding {len(new_values)} entries")
          self.incoming['values'].extend(new_values)
          logger.info(f"{month}: total is now {len(self.incoming['values'])}")
          logger.info("Got Incoming")
          logger.info(f"YTD total after {month}: {len(self.incoming['values'])}")
          for entry in new_values:   
             check_skip = True

             try:
                self.incoming_ingredients.add(entry[1])
             except:
                logger.exception("Failed to add ingredient")
             try:
                if yes_no_to_bool(entry[20]):
                    self.duplicate_lots.append(entry)
                    check_skip = False
             except IndexError:
                 logger.exception("Index Error")
             try:
                if not entry[16].strip():
                    self.unrecieved.append(entry)
             except IndexError:
                logger.exception("Index Error")
             try:
                if entry[17].strip():
                    self.released.append(entry)
             except IndexError:
                logger.exception("Index Error")
             try:
                sle = self.get_sle_status(entry[1],entry[3],self.skip_data)
                self.sle_values.append([entry[0],entry[1],entry[3],sle])
             except:
                logger.exception("Error in sle values")
             try:
                #print(f"Calling get_skipped on {entry[0]} {entry[1]}")
                if check_skip and self.get_skipped(entry[1],entry[3],entry[0]):
                        if entry not in self.sle_skips:
                            self.sle_skips.append(entry)
             

             except:
                logger.exception("Error in get_skipped")
             try:
                if entry[1] in self.top_25_ingredients:
                       self.top_25_data[entry[1]].insert(
                        0,
                        [entry[0], f"SLE STATUS: {sle}"]
                    )
             except:
                logger.exception("Error in checking top 25 status")
                
          #print(len(self.duplicate_lots))
          
          self.percent_duplicates = len(self.duplicate_lots)/len(self.incoming['values']) * 100

       
       def get_skipped(self,ingredientID,vendor,batchID):
              #return False #fix skip value check
              skip = "Not Found"
              
              column = None
              #print(f"Checking {batchID} {ingredientID}")
              
              for entry in self.skip_data:
                 try: 
                    if len(entry) < 4:
                        continue  
                    
                    if entry[2] == ingredientID and entry[3] == vendor:
                       i = 0
                       for id in entry:
                          
                          if id == batchID:
                           column = i
                           break
                          i += 1  
                 except Exception as e:
                  logger.error(e)
                 

              try:
               skip = skip_value_by_column(column)
              except Exception as e:
               logger.error(e)
               logger.error("COULD NOT FIND SKIP DATA")
               return 0
              if str(skip) == "Not Found":
                 logger.error("COULD NOT FIND SKIP DATA")
                 return 0
              else: return skip

       def get_top_25_sle(self):
        with open("sles.json", "r") as f:
            self.top_25_sle_data = json.load(f)

        for ingredient in self.top_25_ingredients:

            sle = "N/A"
            
            try:

                ingredient_id = ingredient.strip().upper()
                sle_values = []

                for key, value in self.top_25_sle_data.items():

                    key = key.replace("\r", "").replace("\n", "").strip().upper()

                    # Get ingredient ID from beginning of key
                    key_ingredient = key.split()[0]

                    if key_ingredient == ingredient_id:
                        sle_values.append(int(value))

                if sle_values:
                    sle = max(sle_values)

                self.top_25_data[ingredient] = [
                    ["", f"SLE STATUS: {sle}"]
                ]

            except Exception:
                logger.exception("Error getting SLE status")
       
       def get_test_log(self,sheetID):
          self.test_log = cache_test_log(sheetID)['values']
          for entry in self.test_log:
            try:
             if len(entry) < 8:
                continue
             
             if self.check_valid_date(entry[5]): #TODO: update to work within specified range
                
                self.tests_requested_within_timeframe.append(self.search_test_data(entry[0],entry[1],entry[2]))
            except:
               logger.exception("Error in get_test_log")
       
       def get_overall_sle(self,overall_data):
          data = overall_data
          
          for i in range(6):
             self.overall_sle_values.append(float([data[i][2]][0]))

       def print_values(self):
          self.seperate_by_sle_status()
          
          sle_values = []
          sle_graph_values = []
          self.percent_sle_skipped = (round(len(self.sle_skips)/len(self.incoming['values'])*100,2))
          self.percent_skipped = ((len(self.sle_skips)+len(self.duplicate_lots))/len(self.incoming['values'])*100)
          total_sle = sum(len(group) for group in self.sle0_5)
          for i in range(6):
             #print(self.sle0_5)
             self.sle_graph_values.append(len(self.sle0_5[i]))
             self.percent_at_sle_x.append(round(len(self.sle0_5[i])/total_sle*100,2)) #TODO: account for duplicate ingredients
         

          logger.info("SELECTED TIME")
          logger.info(self.selected_time)
          logger.info("PERCENT DUPLICATES")
          logger.info(f"{round(self.percent_duplicates,2)}%")
          logger.info("PERCENT SLE SKIPS")
          logger.info(f"{round(self.percent_sle_skipped,2)}%")
          logger.info("PERCENT SKIPPED LOTS")
          logger.info(f"{round(self.percent_skipped,2)}%")
          logger.info(f"#Duplicates: {len(self.duplicate_lots)}")
          logger.info(f"#SLE Skips: {len(self.sle_skips)}")
          logger.info(f"#Total: {len(self.incoming['values'])}")
          logger.info(f"Total Estimated Cost Of Tests: {self.total_cost}")
          logger.info(f"PERCENT SLE 0: {self.percent_at_sle_x[0]}%, 1: {self.percent_at_sle_x[1]}%, 2: {self.percent_at_sle_x[2]}%, 3: {self.percent_at_sle_x[3]}%, 4: {self.percent_at_sle_x[4]}%, 5: {self.percent_at_sle_x[5]}%,")
          logger.info("TOP 25 INGREDIENTS RECEIVED")
          logger.info(self.top_25_data)
          logger.info("INCOMING INGREDIENTS")
          logger.info(self.incoming_ingredients)
          logger.info("OVERALL SLE")
          logger.info(self.overall_sle_values)
          self.sle_pie_chart(self.sle_graph_values)
          self.sle_pie_chart(self.overall_sle_values)
          self.skipped_graph_values = []
          tested = len(self.incoming['values']) - len(self.duplicate_lots) - len(self.sle_skips)
          logger.info(f"Incoming: {len(self.incoming['values'])}")
          logger.info(f"Duplicates: {len(self.duplicate_lots)}")
          logger.info(f"SLE skips: {len(self.sle_skips)}")
          logger.info(f"Tested: {tested}")
          self.skipped_graph_values.append(tested)
          self.skipped_graph_values.append(len(self.sle_skips))
          self.skipped_graph_values.append(len(self.duplicate_lots))
          self.skipped_pie_chart(self.skipped_graph_values)
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
    label_request_date = 0

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

    #timed report variables
    selected_date_range = ""
    pivot_date = str(todays_date())

    changes = {}
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
        self.actionOpen.triggered.connect(self.open_clicked)
        self.actionSave.triggered.connect(lambda: self.create_save_file("qc_release_save_" + tt.strftime("%Y%m%d-%H%M%S") + ".json"))
        self.actionSave_As.triggered.connect(self.save_as_clicked)
        self.actionRefresh_Check_In_Data.triggered.connect(self.cache_rm_clicked)
        self.actionRefresh_Component_Check_In_Data.triggered.connect(self.cache_comp_clicked)
        self.actionRefresh_Label_Check_In_Data.triggered.connect(self.cache_label_clicked)
        self.actionRefresh_Test_and_Skip_Data.triggered.connect(self.cache_test_clicked)
        self.report_test_button.clicked.connect(self.test_report)
        self.dayButton.toggled.connect(lambda:self.update_selected_range("day"))
        self.weekButton.toggled.connect(lambda:self.update_selected_range("week"))
        self.monthButton.toggled.connect(lambda:self.update_selected_range("month"))
        self.yearButton.toggled.connect(lambda:self.update_selected_range("ytd"))
        self.report_date.setDate(QDate.currentDate())
        self.report_date.userDateChanged.connect(self.update_pivot_date)
        self.report_progress_bar.setValue(0)
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

    def create_save_file(self,filename):
     try:
       state = {
              
              "cached_RM_check_in_values":self.cached_RM_check_in_values,
              "cached_component_check_in_values":self.cached_component_check_in_values,
              "cached_label_check_in_values":self.cached_label_check_in_values,
              "cached_test_values":self.cached_test_values,
              "cached_skip_values":self.cached_skip_values,
              "recent_requests":self.recent_requests,
              "to_be_tested":self.to_be_tested,
              "batches_released":self.batches_released,
              "labels_created":self.labels_created,
              "batches_searched":self.batches_searched,
              "test_sheets_searched":self.test_sheets_searched,
              "tests_requested":self.tests_requested,
              "total_price_of_tests":self.total_price_of_tests,
       } 
       if isinstance(self.most_recent_request, list):
          state["most_recent_request"] = self.most_recent_request
       elif isinstance(self.most_recent_request,raw_material_data): 
          state["most_recent_request"] = self.most_recent_request.list_form()
       
       if not os.path.exists(APP_DIR / "Save_Files"): os.makedirs(APP_DIR / "Save_Files")
       save_path = APP_DIR / "Save_Files" / f"{filename}"
       with open(save_path, "w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)

       logger.info("Program state saved")

     except Exception as e:
        logger.exception(e)
        logger.exception("Could not save program state")

    def load_save_file(self,file):
       try:
        with open(file, "r", encoding="utf-8") as f:
             state = json.load(f)
        self.most_recent_request = state.get("most_recent_request", None)

        self.cached_RM_check_in_values = state.get(
            "cached_RM_check_in_values", {}
        )

        self.cached_component_check_in_values = state.get(
            "cached_component_check_in_values", {}
        )

        self.cached_label_check_in_values = state.get(
            "cached_label_check_in_values", {}
        )

        self.cached_test_values = state.get(
            "cached_test_values", []
        )

        self.cached_skip_values = state.get(
            "cached_skip_values", []
        )

        self.recent_requests = state.get(
            "recent_requests", []
        )

        self.to_be_tested = state.get(
            "to_be_tested", []
        )

        self.batches_released = state.get(
            "batches_released", 0
        )

        self.labels_created = state.get(
            "labels_created", 0
        )

        self.batches_searched = state.get(
            "batches_searched", 0
        )

        self.test_sheets_searched = state.get(
            "test_sheets_searched", 0
        )

        self.tests_requested = state.get(
            "tests_requested", 0
        )

        self.total_price_of_tests = state.get(
            "total_price_of_tests", 0
        )

        self.update_table()
        self.update_test_table()
        logger.info("Program state loaded")

       except Exception as e:
         logger.exception(e)
         logger.exception("Could not load program state")
          
    def open_clicked(self):
        save_folder = APP_DIR / "Save_Files"
        if save_folder.exists():
            start_location = str(save_folder)
        else:
            start_location = str(APP_DIR)
        filename, _ = QFileDialog.getOpenFileName(
        self,
        "Open File",
        start_location,
        "All Files (*.*)"
        )

        if filename:
           self.load_save_file(filename)

    def save_as_clicked(self):
        save_folder = APP_DIR / "Save_Files"
        if save_folder.exists():
         start_location = str(save_folder)
        else:
         start_location = str(APP_DIR)

        filename, _ = QFileDialog.getSaveFileName(
        self,
        "Save As",
        start_location,
        "JSON Files (*.json);;All Files (*.*)"
        )
        if filename:
          self.create_save_file(filename)
        

    def update_selected_range(self,selection):
       self.selected_date_range = selection
       return

    def report_finished(self,file):
        self.report_progress_bar.setValue(100)
        logger.info("Report finished")
        os.startfile(str(file))
    def report_error(self, error):
        logger.error(error)
        QMessageBox.critical(self, "Report Error", error)

    def update_pivot_date(self):
       value = self.report_date.date()
       self.pivot_date = value.toString("MM/dd/yy")
       logger.info(self.pivot_date)
       
       return
    
    def test_report(self):
        self.cache_rm_clicked()
        self.cache_test_data_values(self.configs['test_request_sheet_ID'])
        self.cache_skip_values(self.configs['skip_log_ID'])
        self.find_sle_changes()
        self.report_progress_bar.setValue(0)
        if self.selected_date_range == "ytd":
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

        

            converted_date = convert_between_date_formats(self.pivot_date)
            month_num = int(converted_date.split("/")[0])
            year = converted_date.split("/")[2]



            for i in range(month_num):
                month = months[i]
                month_year = f"{month} {year}".upper()

                self.cache_check_in_values(
                    self.configs['RM_check_in_sheet_ID'],
                    month_year,
                    'R'
                )
        self.report_worker = ReportWorker(
        self.selected_date_range,
        self.pivot_date,
        self.cached_skip_values,
        self.cached_test_values,
        self.cached_RM_check_in_values,
        convert_date_to_month_year(todays_date()),
        self.configs['testing_log_sheet_ID'],
        get_test_data(
            self.configs['skip_log_ID'],
            "SLE Status",
            "!A25:C30"
        )['values'],
        APP_DIR / "Reports" /
        f"RM_QC_Report_{self.pivot_date.replace('/', '-')}.pdf",
        self.changes
    )

        self.report_worker.progress.connect(self.report_progress_bar.setValue)
        self.report_worker.finished.connect(lambda file: self.report_finished(APP_DIR / "Reports" /
                f"RM_QC_Report_{self.pivot_date.replace('/', '-')}.pdf"))
        self.report_worker.error.connect(
            lambda error: self.report_error(error)
        )

        self.report_worker.start()

    def cache_rm_clicked(self):
       try:
        self.cache_check_in_values(self.configs['RM_check_in_sheet_ID'],convert_date_to_month_year(todays_date()),'R')
        QMessageBox.information(self,"Done","RM Check In Values for " + str(convert_date_to_month_year(todays_date())) + " cached successfully.")
       except Exception as e:
          logger.exception("RM Cache Failed")
          self.show_error(e)
    def cache_comp_clicked(self):
           try:
            self.cache_check_in_values(self.configs['component_check_in_sheet_ID'],convert_date_to_month_year(todays_date()),'P')
            QMessageBox.information(self,"Done","Component Check In Values for " + str(convert_date_to_month_year(todays_date())) + " cached successfully.")
           except Exception as e:
              logger.exception("Component Cache Failed")
              self.show_error(e)
    def cache_label_clicked(self):
           try:
            self.cache_check_in_values(self.configs['label_check_in_sheet_ID'],convert_date_to_month_year(todays_date()),'L')
            QMessageBox.information(self,"Done","Label Check In Values for " + str(convert_date_to_month_year(todays_date())) + " cached successfully.")
           except Exception as e:
              logger.exception("Label Cache Failed")
              self.show_error(e)
    def cache_test_clicked(self):
           try:
            self.cache_test_data_values(self.configs['test_request_sheet_ID'])
            QMessageBox.information(self,"Done","Test data values cached successfully.")
            self.cache_skip_values(self.configs['skip_log_ID'])
            QMessageBox.information(self,"Done","Skip data values cached successfully.")
           except Exception as e:
              logger.exception("Test Cache Failed")
              self.show_error(e)
    def closeEvent(self, a0):
        logger.info("GENERATING SESSION REPORT...")
        self.endtime = t()
        r = run_report(self.starttime,self.endtime,self.batches_released,self.batches_searched,self.test_sheets_searched,self.labels_created,self.tests_requested,self.total_price_of_tests)
        r.print_run_report()
        self.create_save_file("qc_release_save_" + tt.strftime("%Y%m%d-%H%M%S")+ ".json")
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
          
    def update_sle_data(self):
     
            sles = {} 

            for entry in self.cached_skip_values:
                  if len(entry) < 4: continue
                  try:  
                    title = entry[2] + " " + entry[3]
                    sles[title] = int(entry[0])
                  except Exception as e:
                        logger.exception(e)
                        logger.exception("Could not save SLE statuses")
                        continue
            save_path = APP_DIR / "sles.json"
            with open(save_path, "w", encoding="utf-8") as file:
                json.dump(sles, file, indent=4)
        
                logger.info("SLE STATUSES SAVED")

    def fetch_sle_data(self):
        
        save_path = APP_DIR / "sles.json"

        with open(save_path, "r", encoding="utf-8") as file:
            sles = json.load(file)  
        return sles
    def find_sle_changes(self):
        old_sles = self.fetch_sle_data()
        self.update_sle_data()
        new_sles = self.fetch_sle_data()
        changed_sles = {}

        for key in old_sles.keys() | new_sles.keys():
            if old_sles.get(key) != new_sles.get(key):
                changed_sles[key] = {
                    "old": old_sles.get(key),
                    "new": new_sles.get(key)
                }
        print(changed_sles)
        self.changes = changed_sles
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
       logger.info("Attempting to cache skip values")
       cache = get_test_data(sheetID,"SLE Status","!D:BC")['values']
       if isinstance(cache, str):
          logger.error(cache)
       elif isinstance(cache,list):
          self.cached_skip_values = cache
       else:
          logger.error("Error in caching skip values")
          logger.error(type(cache))
       return
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
          try:
            if entry[7] == "PENDING" or entry[7] == None:
              price = 0
            else: price = entry[7]
          except Exception as e:
             logger.exception(e)
             price = 0
          data = td(ingredientID=entry[0],ingredient_name=entry[1],heavy_metals=yes_no_to_bool(entry[2]),routine_micros=yes_no_to_bool(entry[3]),standard_request=entry[4],request_method = entry[5],request_specs = entry[6],standard_price=price,skip=skip_value)
          return data
    def get_skip_value(self,batch):
              #return False #fix skip value check
              skip_data = "Not Found"
              
              column = None
              try:
              
               for entry in self.cached_skip_values:
                    
                    if entry[2] == batch.ingredientID and entry[3] == batch.vendor:
                       i = 0
                       for id in entry:
                          if id == batch.batchID:
                           column = i
                           break
                          i += 1  
              except Exception as e:
                 logger.error(e)
                 
              try:
                skip_data = skip_value_by_column(column)
              except Exception as e:
                  logger.error(e)
                  
              if str(skip_data) == "Not Found":
                 logger.info("COULD NOT FIND SKIP DATA IN CACHE. RECACHING...")
                 self.cache_skip_values(self.configs['skip_log_ID'])
                 try:
                        for entry in self.cached_skip_values:
                                            
                            if entry[2] == batch.ingredientID and entry[3] == batch.vendor:
                               i = 0
                               for id in entry:
                                 if id == batch.batchID:
                                   column = i
                                   break
                                 i += 1   
                 except Exception as e:
                           logger.error(e)
                           
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
                date = self.label_request_date
                try:
                 if date == 0:
                    date,ok = QInputDialog.getText(self,"Label Recieving Date","Please input the label recieving date (MM/DD/YYYY)")
                    self.label_request_date = date
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
             row += 1
             try:
                

                if type_material != 'L' and entry[0] == batchID:
                    
                    raw_material_info = entry
                    break   
                
                if type_material == 'L':

                      if entry[0].strip() == zeroless_date and entry[3].strip() == batchID:
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
        if len(batchID) < 7:
            try:
               self.batches_searched.append([batchID + " ", "FAILED TO FIND"])
               self.progressBar.setValue(0)
               self.recent_data_label.setText("Could not find batch data")
               logger.warning("Could not find batch data")
            except Exception:
                logger.exception("FATAL APPLICATION ERROR")
            return
        if len(batchID) >= 8:
            type_material = 'L'
            self.label_request_date = 0
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
                date = self.label_request_date
                if date == 0:
                    try:
                            date,ok = QInputDialog.getText(self,"Label Recieving Date","Please input the label recieving date (MM/DD/YYYY)")
                            self.label_request_date = date
                            logger.info(date)
                            if not ok:
                             logger.info("USER CANCELLED LABEL REQUEST")
                             return 0
                
                            
                    except Exception as e:
                        logger.error(str(e))
                        self.show_error("ERROR IN INPUT")
                        return
                month = convert_date_to_month_year(date)
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



    def show_checkbox_popup(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("On COA")
        dialog.resize(400, 150)
        layout = QtWidgets.QVBoxLayout(dialog)

        checkboxes = []

        options = [
            "Dietary",
            "Heavy Metals",
            "Micros",
        ]

        for option in options:
            checkbox = QtWidgets.QCheckBox(option)
            layout.addWidget(checkbox)
            checkboxes.append(checkbox)

        button = QtWidgets.QPushButton("OK")
        layout.addWidget(button)

        button.clicked.connect(dialog.accept)

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            selected = [
                checkbox.text()
                for checkbox in checkboxes
                if checkbox.isChecked()
            ]

            print(selected)
            return selected

        return []   
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
              hm = False
              rm = False
              logger.info("BATCH ID: " + batch.batchID + " SKIPPED")
              selected = self.show_checkbox_popup()
              if "Dietary" in selected:
                 data.standard_request = "ID"
                 #data.request_method = "HPTLC"
                 data.request_specs = "Conforms to Reference Standard"
                 data.standard_price = 140
              if "Heavy Metals" not in selected:
                 hm = True
              if "Micros" not in selected:
                rm = True
              data.skip = False
              data.heavy_metals = hm
              data.routine_micros = rm
              result = write_to_ssf(batch,data,self.configs["ssf_sheet_ID"],self.configs["testing_log_sheet_ID"],11+i)
              self.tests_requested.append([batch.batchID + " " + batch.ingredientID + " ", "TEST SKIPPED DUE TO SLE STATUS"])
              self.show_error("BATCH ID: " + batch.batchID + " SKIPPED DUE TO SLE STATUS")

              self.update_test_table()
              if not selected:
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
    logger.info("Version 1.0.7")
    config = read_config()
    logger.info(config)
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
        
