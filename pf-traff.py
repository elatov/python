#!/usr/bin/env python3
import urllib.request
import json
import smtplib
import os
from datetime import date, timedelta
from subprocess import call
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Get the previous month
prev = date.today().replace(day=1) - timedelta(days=1)
last_month = prev.month
lm_name = prev.strftime("%B")
y_of_last_month = prev.year

# configure plot files
data_file = "/tmp/bw-"+str(last_month)+"-"+str(y_of_last_month)+".data"
gnuplot_script = "/tmp/bw.gnu"
gnuplot_png = "/tmp/bw-"+str(last_month)+"-"+str(y_of_last_month)+".png"

# URL to grab the json from
url = "http://pf/vnstat_fetch_json.php"
with urllib.request.urlopen(url) as response:
    text = response.read()

# store the whole json object
data = json.loads(text.decode('utf-8'))

# just grab the interfaces
ints = data["interfaces"]

# only grab the WAN interface dictionary
for i in ints:
    if (i["nick"] == "WAN"):
        wan_int=i

# parse the months json and grab the totals for previous month
for b in wan_int["traffic"]["months"]:
    if (b["date"]["month"] == last_month):
        month_rx_total = b["rx"]
        month_tx_total = b["tx"]

# Conver to float gb and keep 2 decimal points
month_rx_gb = "%.2f" % (month_rx_total / 1024.0 / 1024)
month_tx_gb = "%.2f" % (month_tx_total / 1024.0 / 1024)

# Write out a file in format of "day_of_month rx_for_the_day tx_for_the_day"
with open(data_file, "w") as text_file:
    wan_int["traffic"]["days"].reverse()
    for b in wan_int["traffic"]["days"]:
        if (b["date"]["month"] == last_month):
            day = b["date"]["day"]
            rx = (b["rx"] * 1024)
            tx = (b["tx"] * 1024)
            text_file.write("%02d %s %s\n" % (day,rx,tx))

# Create GnuPlot Script
gplot_string = ("set title \""+str(lm_name)+" "+str(y_of_last_month)+"(Incoming: "+str(month_rx_gb)+" GB Outgoing: "+str(month_tx_gb)+" GB)\"\n"
               "set terminal png size 800,600 enhanced font \"Helvetica,10\"\n"
                "set output \""+str(gnuplot_png)+"\"\n"
                "set grid\n"
                "set style data histogram\n"
                "set style histogram cluster gap 1\n"
                "set style fill solid border -1 \n"
                "set boxwidth 0.9\n"
                "set xtic scale 0\n"
                "set format y \"%.2b%B\"\n"
                "plot \""+str(data_file)+"\"  using 2:xtic(1) title \"Incoming\",\"\"using 3:xtic(1) title \"Outgoing\" ")

### create script from the string
with open(gnuplot_script, "w") as text_file:
    text_file.write(gplot_string)

### Run gnuplot
call(["/usr/bin/gnuplot", gnuplot_script])
call(["/bin/cp", gnuplot_png,"/usr/local/bw/"])

# Email script
fromaddr = "bw@me"
toaddr = "admin@me"
 
msg = MIMEMultipart()
 
msg['From'] = fromaddr
msg['To'] = toaddr
msg['Subject'] = "Bandwidth usage for "+lm_name+" "+str(y_of_last_month)
 
body = "Graph"
 
msg.attach(MIMEText(body, 'plain'))
 
filename = gnuplot_png
attachment = open(filename, "rb")
 
part = MIMEBase('application', 'octet-stream')
part.set_payload((attachment).read())
encoders.encode_base64(part)
part.add_header('Content-Disposition', "attachment; filename= %s" % "graph.png")
 
msg.attach(part)
 
server = smtplib.SMTP('mail', 25)
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

# clean up files
os.remove(gnuplot_script)
os.remove(gnuplot_png)
os.remove(data_file)
