import logging
from datetime import datetime
import time as tt
logger = logging.getLogger(__name__)
logging.basicConfig(filename='debug.log', encoding='utf-8', level=logging.DEBUG)

class run_report:
   def __init__(self,starttime,endtime,batches_released,batches_searched,test_sheets_searched,labels_created,testing_requested,total_cost):
         self.starttime = starttime
         self.endtime = endtime
         self.runtime = endtime - starttime
         self.batches_released = batches_released
         self.batches_searched = batches_searched
         self.test_sheets_searched = test_sheets_searched
         self.labels_created = labels_created
         self.testing_requested = testing_requested
         self.total_cost = total_cost


   def print_run_report(self):
       name = "Reports/RUN_REPORT_" + tt.strftime("%Y%m%d-%H%M%S" + ".txt")
       with open(name, "w", encoding="utf-8") as f:
        f.write("--RUN REPORT FOR " + tt.strftime("%Y%m%d-%H%M%S") + "--" + "\n")
        f.write("PROGRAM RAN FOR " + str(self.runtime) + " SECONDS"+ "\n")
        f.write("--BATCHES RELEASED--"+ "\n")
        for entry in self.batches_released:
           for entry2 in entry: 
            f.write(entry2)
           f.write("\n")
        f.write("--BATCHES CATALOGUED--"+ "\n")
        for entry in self.batches_searched:
                 
                 for entry2 in entry: 
                     f.write(entry2)
                 f.write("\n")
        f.write("--TEST SHEETS SEARCHED--"+ "\n")
        for entry in self.test_sheets_searched:
                    
                    for entry2 in entry: 
                     f.write(entry2)
                    f.write("\n")
        f.write("--LABELS CREATED--"+ "\n")
        for entry in self.labels_created:
                    
                    for entry2 in entry: 
                     f.write(entry2)
                    f.write("\n")
        f.write("--TESTING REQUESTED--"+ "\n")
        for entry in self.testing_requested:
                
                 for entry2 in entry: 
                     f.write(entry2)
                 f.write("\n")
        f.write("TOTAL ESTIMATED COST OF TESTING: $" + str(self.total_cost)+ "\n")
        f.write("--RUN REPORT FOR " + tt.strftime("%Y%m%d-%H%M%S") + "ENDS--")

class test_data:
   sle = 0
   def __init__(self, ingredientID, ingredient_name, heavy_metals=True, routine_micros=True, standard_request="",request_method = "", request_specs = "",standard_price=0,skip=False,rm_fg = True):
         self.ingredientID = ingredientID
         self.ingredient_name = ingredient_name
         self.heavy_metals = heavy_metals
         self.routine_micros = routine_micros
         self.standard_request = standard_request
         self.standard_price = standard_price
         self.skip = skip
         self.request_method = request_method
         self.request_specs = request_specs
         self.rm_fg = rm_fg
   def print_data(self):
       print([self.ingredientID,self.ingredient_name,self.heavy_metals,self.routine_micros,self.standard_request,self.standard_price,self.skip,self.request_method,self.request_specs])
        
class material_data:
   def __init__(self,batchID, ingredientID, ingredient_name, vendor, vendor_lot_num, expiration_date,num_of_containers, is_duplicate_lot="NO", PO_num = "0",row = 0,type_material = 'R'):
      self.batchID = batchID
      self.ingredientID = ingredientID
      self.ingredient_name = ingredient_name
      self.vendor = vendor
      self.vendor_lot_num = str(vendor_lot_num)
      self.expiration_date = expiration_date
      self.num_of_containers = num_of_containers
      self.is_duplicate_lot = is_duplicate_lot
      self.PO_num = PO_num
      self.row = row
      self.type_material = type_material

   def print_data(self):
      logger.info("Batch Number: " + self.batchID)
      logger.info("Ingredient ID: " + self.ingredientID)
      logger.info("Name: " + self.ingredient_name)
      logger.info("Vendor: " + self.vendor)
      logger.info("Vendor Lot Number: " + self.vendor_lot_num)
      logger.info("Expiration Date: " + self.expiration_date)
      logger.info("Number of containers: " + str(self.num_of_containers))
      logger.info("Duplicate lot: " + self.is_duplicate_lot)
      logger.info("PO #: " + str(self.PO_num))
      return
   def list_form(self):
      return [self.batchID,self.ingredientID,self.ingredient_name,self.vendor,self.vendor_lot_num,self.expiration_date,self.num_of_containers,self.is_duplicate_lot,self.PO_num,self.type_material]

       

def list_form_to_class_form(batch_data_list):
   a,b,c,d,e,f,g,h,i,j = batch_data_list
   return material_data(a,b,c,d,e,f,g,h,i,type_material=j)