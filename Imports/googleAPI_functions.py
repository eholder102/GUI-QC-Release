#google api interface
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from Imports.lubricant_funcs import *
from Imports.material_data import test_data as td


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]



def timestamp_sample(
     sheetID,row,col = "!R"
):
  value_input_option = "USER_ENTERED"
  row_num = str(row)
  range_name = convert_date_to_month_year(todays_date()) + col + row_num
  creds = None
  if os.path.exists("sheetstoken.json"):
      creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
      with open("sheetstoken.json", "w") as token:
        token.write(creds.to_json())
  
  # pylint: disable=maybe-no-member
  try:
    service = build("sheets", "v4", credentials=creds)

    values = [
        [
          str(datetime.now())
        ],
        
        # Additional rows
    ]
    data = [
        {"range": range_name, "values": values},
        # Additional ranges to update ...
    ]
    body = {"valueInputOption": value_input_option, "data": data}
    result = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=sheetID, body=body)
        .execute()
    )
    print(f"{(result.get('totalUpdatedCells'))} cells updated.")
    return result
  except HttpError as error:
    print(f"An error occurred: {error}")
    return error



def get_test_data(sheetID,sheet_name,value_range):
           creds = None
         # The file token.json stores the user's access and refresh tokens, and is
         # created automatically when the authorization flow completes for the first
         # time.
           if os.path.exists("sheetstoken.json"):
               creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
           with open("sheetstoken.json", "w") as token:
             token.write(creds.to_json())

           try:
               service = build("sheets", "v4", credentials=creds)
              
               # Call the Sheets API
               sheet = service.spreadsheets()
               
               result = (
                   sheet.values()
                   .get(spreadsheetId=sheetID, range=sheet_name + value_range)
                   .execute()
               )
               
               return result
           except Exception as e:
                print(e)
                return e
           
def write_to_ssf(batch_data,test_data, ssf_sheetID, test_log_sheetID, row_num=11,blank = False):
    batchID = batch_data.batchID
    if test_data.skip:
       return "SKIPPED"
    value_input_option = "USER_ENTERED"
    test_name = test_data.standard_request
    test_method = test_data.request_method
    specs = test_data.request_specs
    if test_data.heavy_metals:
       hm = "Heavy Metals, "
    else:
       hm = ""
    
    range_name = "TRF!B" + str(row_num)
    creds = None
    if os.path.exists("sheetstoken.json"):
        creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
        with open("sheetstoken.json", "w") as token:
          token.write(creds.to_json())
    
    # pylint: disable=maybe-no-member
    try:
      service = build("sheets", "v4", credentials=creds)
  
      values = [
          [
            test_data.ingredientID + "-" + test_data.ingredient_name,
            batchID,
            hm + test_name,
            "RM",
            test_method,
            specs
          ],
          
          # Additional rows
      ]
      data = [
          {"range": range_name, "values": values},
          # Additional ranges to update ...
      ]
      body = {"valueInputOption": value_input_option, "data": data}
      result = (
          service.spreadsheets()
          .values()
          .batchUpdate(spreadsheetId=ssf_sheetID, body=body)
          .execute()
      )
      print(f"{(result.get('totalUpdatedCells'))} cells updated.")
      if not blank: update_test_log(batch_data,test_data,test_log_sheetID)
      return result
    except HttpError as error:
      print(f"An error occurred: {error}")
      return error

def open_test_data_sheet(filename):
   try:
    subprocess.run(filename, shell=True)
    
   except:
      print("Error in opening test sheet")
   
   return

def check_skip_log(ingredientID):
      creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
      if os.path.exists("sheetstoken.json"):
          creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
          with open("sheetstoken.json", "w") as token:
            token.write(creds.to_json())
      
      try:
          service = build("sheets", "v4", credentials=creds)
      
          # Call the Sheets API
          sheet = service.spreadsheets()
          result = (
                      sheet.values()
                      .get(spreadsheetId="1rnRn7JNQtOGa11ogbovqtHfU3Au9CCM8j12w0PUmlCw", range="Raw Ingredients Skip Lot Tracking Template!A2:AF2000")
                      .execute()
                  )
          
          try:
              for entry in result['values']:
                  
                  if entry[2] == ingredientID:
                    print("SKIPPED")
                    skipped = True
                    return skipped
          except Exception as error: 
               pass
          skipped = False 
          return skipped
             
      except HttpError as error:
    # TODO(developer) - Handle errors from drive API.
        print(f"An error occurred: {error}")

def update_test_log(batch_data, test_data, sheetID):
    value_input_option = "USER_ENTERED"
    test_name = test_data.standard_request

    
    range_name = "2026 Raw Material Testing"
    creds = None
    if os.path.exists("sheetstoken.json"):
        creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
        with open("sheetstoken.json", "w") as token:
          token.write(creds.to_json())
    
    # pylint: disable=maybe-no-member
    method = ""
    lab1 = "Certified Labs _Tusc"
    lab2 = ""
    if test_data.routine_micros:
       method += "Routine Micros, "
       lab2= "Certified Labs _ Burbank"
    if test_data.heavy_metals:
       method += "Heavy Metals, "
    if test_data.request_method == "HPTLC" and test_data.standard_request == "ID":
        method += "ID_HPTLC"
    else:
       method += test_data.standard_request
    try:
      service = build("sheets", "v4", credentials=creds)
      values = [
          [
            batch_data.batchID,
            batch_data.ingredientID,
            batch_data.ingredient_name,
            batch_data.vendor,
            batch_data.vendor_lot_num,
            todays_date(),
            method,
            lab1 + "," + lab2,
            
          ],
          
          # Additional rows
      ]


      result = (
      service.spreadsheets()
        .values() 
        .append( 
           spreadsheetId=sheetID, 
           range="2026 Raw Material Testing!A:H", 
           valueInputOption="USER_ENTERED", 
           insertDataOption="INSERT_ROWS", 
           body={
            "values": values
            }
           ) 
           .execute() 
      )
      print(f"{(result.get('totalUpdatedCells'))} cells updated.")
      return result
    except HttpError as error:
      print(f"An error occurred: {error}")
      return error

def cache_test_log(sheetID):

    range_name = "2026 Raw Material Testing"
    creds = None
    if os.path.exists("sheetstoken.json"):
        creds = Credentials.from_authorized_user_file("sheetstoken.json", SCOPES)
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
        with open("sheetstoken.json", "w") as token:
          token.write(creds.to_json())
    
    # pylint: disable=maybe-no-member
    
    try:
      service = build("sheets", "v4", credentials=creds)
      sheet = service.spreadsheets()
      
      result = (
          sheet.values()
          .get(spreadsheetId=sheetID, range='2026 Raw Material Testing!A:H')
          .execute()
      )
    
      return result
    except HttpError as error:
      print(f"An error occurred: {error}")
      return error