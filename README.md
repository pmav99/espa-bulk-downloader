Automatically download all completed espa scenes to your local machine.  Each scene gets downloaded to a directory named after its respective order in the download directory.
# Installation
* Install python 2.7.
* Clone this repository: `git clone https://github.com/USGS-EROS/espa-bulk-downloader.git bulk-downloader`
* `cd bulk-downloader`
* `./download_espa_order.py -h`

### Runtime options
-e The email address used to submit the order

-o The order you wish to download.  Maybe also use `ALL`

-d The local directory to store downloaded scenes

Linux/Mac Example: `./download_espa_order.py -e your_email@server.com -o ALL -d /some/directory/with/free/space`
Windows Example: `C:\python27\python download_espa_order.py -e your_email@server.com -o ALL -d C:\some\directory\with\free\space`

# Notes
Retrieves all completed scenes for the user/order
and places them into the target directory.
Scenes are organized by order.

It is safe to cancel and restart the client, as it will
only download scenes one time (per directory)
 
If you intend to automate execution of this script,
please take care to ensure only 1 instance runs at a time.
Also please do not schedule execution more frequently than
once per hour.


    
