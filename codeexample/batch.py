#This script creates multiple Designated Forest Maps at once
#requires DF_script.py in same folder

#import functions
from datetime import datetime
from DF_Script import *

#set up error logging
logging.basicConfig(filename=r'[file/server location redacted]')

#get and print the name of the user running the program
username = os.getlogin()
print('\nRunning as user ' + username)

#print some useful info
print("\nThis program allows you to make multiple DF maps at once.")
print("Enter each PID and DF number one by one as instructed.")
print("Once you are finished entering parcels, press enter to generate maps.\n")

try: #try/except clause for logging errors
    Propertylist = [] #create array to hold list of PIDs to process

    #Ask for info from user in a loop until user indicates they're done
    while True:
        newPID = input("Type one PID below (or press enter to process entered parcels) and then hit enter:\n") #get the property ID(s)
        if newPID != '': #if the user entered something
            newDFNumber = input("Type one DF Number below and then hit enter:\n") #ask for the associated designated forest number
            Propertylist.append([newPID,newDFNumber]) #append the entered values to the property list
        else:
            break #move on to the rest of the script

    propertycount = len(Propertylist) #find out how many properties were entered
    counter = 1 #set progress counter   

    #loop over the list of entered properties and process them one at a time
    for property in Propertylist: 
        print('\nMaking map ' + str(counter) + '/' + str(propertycount) + '...\n') #print progress info ("Making map 1/3...")
        
        DF_function(property[0],property[1]) #make pdfs of each entered property using DF_Script.py

        counter = counter + 1 #increment counter for progress indicator

    input('Program finished successfully, press ENTER to close') #indicates script is done running

except:
    error = traceback.format_exc() #gets whole stack trace
    installinfo = str(arcpy.GetInstallInfo()) #gets info about the ArcGIS install
    currenttime = datetime.now().strftime("%Y-%m-%d %H:%M:%S") #gets current date and time 
    errstring = '\n-user:' + str(username) + '\n-time: ' + currenttime + '\n-Script: DF batch (multiple)\n-installinfo:' + installinfo + '\n-error:' + str(error)
    logging.warning(errstring) #writes error info gathered above to a log file 
