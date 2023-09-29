#This script generates a PDF for the designated forest program.
#see [file/server location redacted] for more info

#By Nick Thibault, Island County 2023

#Import packages
import arcpy
import os
import shutil
import stat
import logging
import traceback

#Creates designated forest dataset for use in layout_generator
def data_generator(PID):
    # Allow overwriting outputs
    arcpy.env.overwriteOutput = True

    with arcpy.EnvManager(scratchWorkspace="temp.gdb", 
                          workspace="temp.gdb"):
        #Select parcel
        print("Selecting Parcel")
        PIDexpression = "PID = " + PID
        [file/server location redacted] = "[file/server location redacted]"
        arcpy.analysis.Select(in_features=[file/server location redacted],
                              out_feature_class="Parcel", 
                              where_clause=PIDexpression)

        #Buffer selected parcel by 10 meters
        print("Buffering parcel")
        arcpy.analysis.Buffer(in_features="Parcel",
                                  out_feature_class="Parcel_buffer",
                                  buffer_distance_or_field="10 Meters", #if there are issues, turn this back to 800m
                                  method="PLANAR")

        #Clip tree soil index layer using the buffer from the previous step
        print("Clipping soil layer")
        Soil_TreeIndex = "[file/server location redacted]"
        arcpy.analysis.Clip(in_features=Soil_TreeIndex,
                                clip_features="Parcel_buffer",
                                out_feature_class="TreeSoil_clip",)

        #Delete fields to prep for union
        print("Deleting fields")
        arcpy.management.DeleteField(in_table="Parcel",
                                    drop_field=["appraisal_year",
                                                "assessed_value",
                                                "exemptions",
                                                "improvement_value",
                                                "land_value",
                                                "mailing_addr_city",
                                                "mailing_addr_state",
                                                "mailing_addr_zip",
                                                "mailing_addr1",
                                                "mailing_addr2",
                                                "mailing_addr3",
                                                "market_value",
                                                "ModifyDate",
                                                "physical_addr",
                                                "physical_addr_city",
                                                "physical_addr_state",
                                                "physical_addr_zip",
                                                "smartgov_url",
                                                "taxpayer",
                                                "water_source"],
                                    method="DELETE_FIELDS")

        #Union selected parcel and clipped tree layer
        print("Unionizing")
        arcpy.analysis.Union(in_features=[["Parcel", ""], ["TreeSoil_clip", ""]],
                                 out_feature_class="ParcelTree_Union",)

        #Add fields to hold calculated values
        print("Adding fields")
        arcpy.management.AddFields(in_table="ParcelTree_Union",
                                    field_description=[["DF_VALUE", "FLOAT", "Value", "", "", ""],
                                                        ["ACRE_RATIO", "FLOAT", "Acre Ratio", "", "", ""],
                                                        ["SQ_FT", "FLOAT", "Square Feet", "", "", ""]])

        #Clip soil to parcel layer
        print("Clipping soil to parcel")
        arcpy.analysis.Clip(in_features="ParcelTree_Union",
                                clip_features="Parcel",
                                out_feature_class="Soil_final",)

        #Calculate value field
        print("Calculating value field")
        arcpy.management.CalculateField(in_table="Soil_final",
                                            field="DF_VALUE",
                                            expression="!Val_Per_Acre2016! * !GIS_Acres!",)

        #Calculate acre ratio field
        print("Calculating acre ratio field")
        arcpy.management.CalculateField(in_table="Soil_final",
                                            field="ACRE_RATIO",
                                            expression="!legal_acreage! / !GIS_Acres!",)

        #Calculate square feet field
        print("Calculating square feet field")
        arcpy.management.CalculateField(in_table="Soil_final",
                                            field="ACRES",
                                            expression="!shape.geodesicArea@acres!",)

    return

#Sets up layout with provided datset and exports a PDF
def layout_generator(DF_num):
    #Connect to DF Map layout
    print("Connecting to project")
    DF_project = r"[file/server location redacted]"
    aprx = arcpy.mp.ArcGISProject(DF_project)
    aprx.defaultGeodatabase = r"[file/server location redacted]" #set gdb
    
    #Get map, mapframe and layout objects
    print("Getting Data")
    DF_map = aprx.listMaps("2023_DF_Map")[0]
    DF_layout = aprx.listLayouts("2023_DF_layout")[0]
    DF_Parcellayer = DF_map.listLayers("Soil_final")[0]
    DF_mapframe = DF_layout.listElements("mapframe_element")[0]

    #Set extent based on Soil_final layer
    print("Setting extent")
    DF_mapframe.camera.setExtent(DF_mapframe.getLayerExtent(DF_Parcellayer, False, True))
    current_scale = DF_mapframe.camera.scale
    print("Default Scale: " + str(round(current_scale)) + ":1")
    new_scale = current_scale * 1.1
    print("Updated scale: " + str(round(new_scale)) + ":1")
    DF_mapframe.camera.scale = new_scale

    #text element helper function
    def update_text(element,element_text):
        #get correct element
        element_object = DF_layout.listElements("TEXT_ELEMENT",element)[0] 
        #set element value
        element_object.text = element_text

        return

    #Set DF# text element
    print("Setting DF number to: " + DF_num)  
    update_text("DF_number_text", DF_num)

    #Get parcel number, legal acres, and GIS acres from layer
    fieldslist = ["ParcelNo","GIS_Acres","legal_acreage"] #set fields to be pulled
    with arcpy.da.SearchCursor(DF_Parcellayer,fieldslist) as SearchCursor: 
        for row in SearchCursor:
            ParcelNo = row[0]
            GIS_acres = round(row[1],2) #round to two decimal places
            legal_acres = round(row[2],2)
            if ParcelNo != "": #check if it's empty 
                break #we only need one set of each value because they're duplicated

    #Set parcel number text element 
    print("Setting parcel number text to: " + ParcelNo)
    update_text("Parcel Number Text", ParcelNo)

    #Set GIS acre text element
    print("Setting GIS acres text to: " + str(GIS_acres)) 
    update_text("GIS acre number text", GIS_acres)

    #Set legal acre text element
    print("Setting legal acres text to: " + str(legal_acres)) 
    update_text("Legal acre number text", legal_acres)

    #Export map as PDF
    print("Exporting map")
    pdf_location = r"[file/server location redacted]"
    if DF_num == "TEST":
        ParcelNo = ParcelNo + "_TEST"
    DF_layout.exportToPDF(pdf_location + "DF_" + ParcelNo + ".pdf") 
    print("Done exporting")

    return

def DF_function(PID,DF_num):
    #get current directory
    cwd = os.getcwd()
    print("Script directory: " + cwd)

    #set up new temp directory
    temp = r'C:\temp'
    tempdir = r"C:\temp\DFtemp"

    try: 
        os.mkdir(temp) #attempt to create c:\temp
    except OSError as error: #in case directory already exists
        #print(error)
        print('Temp exists')

    try:
        os.mkdir(tempdir) #create a new subdirectory for this script
    except OSError as error: 
        #print(error)
        print('DFtemp exists, cleaning up')
        shutil.rmtree(tempdir)

        os.mkdir(tempdir) #try making the directory again

    os.chdir(tempdir)
    print("Temporary directory: " + os.getcwd())

    #make temp geodatabase
    print("Creating temp.gdb")
    tempgdb = r"C:\temp\DFtemp\temp.gdb" #set location to check for temporary geodatabase
    if arcpy.Exists(tempgdb) == True: #if it exists
        arcpy.management.Delete(tempgdb) #delete it
        tempgdb = arcpy.CreateFileGDB_management(tempdir, "temp.gdb") #remake it
    else: #if it doesn't exist
        tempgdb = arcpy.CreateFileGDB_management(tempdir, "temp.gdb") #make it 

    data_generator(PID) #run the data_generator function with the input PID
    layout_generator(DF_num) #Run layout generator with DF# input

    #Delete temp files
    print("Cleaning up temporary files")
    tempdelete = arcpy.management.Delete(tempgdb) #remove gdb
    
    os.chdir(cwd) #change working directory out of temp file
    
    def remove_readonly(func, path, excinfo): #this just handles a common error
        os.chmod(path, stat.S_IWRITE) #make sure folder isn't read-only
        os.unlink(path) #make sure OS isn't using file
        func(path) #try removing folder again

    shutil.rmtree(tempdir, onerror=remove_readonly) #remove folder

if __name__ == '__main__': #run only if not in module (i.e. if not run from batch.py)
    #set up error logging
    logging.basicConfig(filename=r'[file/server location redacted]')

    #get and print the name of the user running the program
    username = os.getlogin()
    print('Running as: ' + username)

    #Ask the user what PID they want to process and what the associated DF# is
    PIDinput = input("Type PID below and press enter: \n")
    DF_num_input = input("Type DF number below and press enter (use 'TEST' if testing script): \n")

    #run main function
    try: 
        DF_function(PIDinput,DF_num_input)
    except: #runs if an error occurs
        error = traceback.format_exc() #gets whole stack trace
        installinfo = str(arcpy.GetInstallInfo()) #gets info about the ArcGIS install
        errstring = '\n-user:' + str(username) + '\n-installinfo:' + installinfo + '\n-error:' + str(error)
        logging.warning(errstring) #write error info to a log file 
