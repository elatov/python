#!/usr/bin/env python3
import jenkins, os, smtplib
from email.mime.text import MIMEText

email_report = '/tmp/jen-plug.txt'
server = jenkins.Jenkins('http://jenkins:8081/jenkins', username='admin',
                         password='api-passwd')

# get the status of all the plugins
plugins = server.get_plugins()

# traverse each plugin installed and if it has an update
# add it to the mail report
for plugin_values in plugins.items():
    if plugins[plugin_values[0][0]]['hasUpdate']:
        plugin_name = plugin_values[0][1]
        plugin_version = plugins[plugin_values[0][0]]['version']
        with open(email_report, 'a') as f:
            f.write("{} ({})\n".format(plugin_name, plugin_version))

# send email if the mail report is not empty
if os.path.isfile(email_report):
    fp = open(email_report, 'rb')
    msg = MIMEText(fp.read().decode('utf-8'))
    fp.close()

    from_email = "jenkins@dom.int"
    to_email = "admin@dom.int"
    msg['Subject'] = 'Jenkins Plugin Updates Available'
    msg['From'] = from_email
    msg['To'] = to_email

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP('email.dom.int')
    s.sendmail(from_email, to_email, msg.as_string())
    s.quit()

# clean up the mail report
if os.path.exists(email_report):
    os.remove(email_report)
