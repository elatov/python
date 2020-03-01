#!/usr/bin/env python3
import urllib.request
import json
import datetime
import smtplib
from email.mime.text import MIMEText
import os

query_file = "/usr/local/apps/elasticsearch/kub-error-query.txt"
with open(query_file, 'r') as myfile:
    query = json.load(myfile)

url = 'http://1.1.1.1:9200/_search?pretty'
# have to send the data as JSON
data = json.dumps(query)

# Prepare the request
req = urllib.request.Request(url)
req.add_header('Content-Type', 'application/json; charset=utf-8')
byte_data = data.encode('utf-8')   # needs to be bytes
req.add_header('Content-Length', len(byte_data))

# Get the response into a variable
with urllib.request.urlopen(req, byte_data) as response:
    out = response.read()

# store the whole json object and decoded it
data = json.loads(out.decode('utf-8'))

# Write out the Header of the table
with open('/tmp/es-kub-res.txt', 'w') as f:
    f.write("<html>\n\t<head></head>\n\t<body>\n\t\t<p><table>\n\t" +
            "<tr><td>Date</td><td>Kind</td><td>Name</td><td>Message</td></tr>\n")

# Parse each line and write out kubernetes events to the html report
for i in data['hits']['hits']:
    date = i['_source']['@timestamp']
    temp_date = date.split(".")[0]
    d = datetime.datetime.strptime(temp_date, '%Y-%m-%dT%H:%M:%S')
    conv_date = datetime.date.strftime(d, "%m/%d/%y %H:%M:%S")

    with open('/tmp/es-kub-res.txt', 'a') as f:
        if "kubernetes" in i['_source']:
            kind = i['_source']['kubernetes']['event']['involved_object']['kind']
            name = i['_source']['kubernetes']['event']['involved_object']['name']
            message = i['_source']['kubernetes']['event']['message']
            f.write("<tr><td>" + conv_date + "</td><td>" + kind + "</td><td>" + name
                    + "</td><td>" + message + "</td></tr>\n")

# write out the closing html format
with open('/tmp/es-kub-res.txt', 'a') as f:
    f.write("\t\t</table></p>\n\t</body>\n</html>")

# Prepare email
with open('/tmp/es-kub-res.txt') as fp:
    # Create a text/plain message
    msg = MIMEText(fp.read())

from_email = "machine@me"
to_email = "admin@me"

d = {'from_email': from_email, 
    'to_email': to_email, 
    'subject': "K8S Events 24 Hours", 
    'body': msg.as_string()}

message = """From: {from_email}
To: {to_email}
MIME-Version: 1.0
Content-type: text/html
Subject: {subject}

{body}
""".format(**d)

# send email
try:
    smtpObj = smtplib.SMTP('10.0.0.2')
    smtpObj.sendmail(from_email, to_email, message)
    # print ("Successfully sent email")
except SMTPException:
    print("Error: unable to send email")

# clean up
if os.path.exists("/tmp/es-kub-res.txt"):
    os.remove("/tmp/es-kub-res.txt")
