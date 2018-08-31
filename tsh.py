#!/usr/bin/env python

import random
import imaplib
import smtplib
import email
import time
import sys
import subprocess
from getpass import getpass

import os
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

def asciiify(s):
    s = [ord(' ') if c == ord('\t') else c for c in s] # AT&T can't display tabs
    printable = lambda c: 32 <= c < 127 or c == ord('\r') or c == ord('\n')
    return "".join([chr(c) for c in s if printable(c)])

def force_print(s):
    sys.stdout.write(s)
    sys.stdout.flush()

def emails(inbox, phoneaddress):
    # adapted from https://codehandbook.org/how-to-read-email-from-gmail-using-python/
    # imap search query from https://stackoverflow.com/questions/22856198/how-to-get-unread-messages-and-set-message-read-flags-over-imap-using-python
    inbox.select("inbox")
    type, data = inbox.search(None, "(UNSEEN)", "OR", "(FROM \"%s\")" % phoneaddress["sms"], "(FROM \"%s\")" % phoneaddress["mms"])
    ids = data[0].split()
    if len(ids) == 0:
        return []

    result = []
    for i in range(int(ids[-1]), int(ids[0]) - 1, -1):
        type, data = inbox.fetch(str(i), "(RFC822)")

        for part in data:
            if isinstance(part, tuple):
                msg = email.message_from_string(part[1].decode("utf-8"))
                print(msg.is_multipart())

                # adapted from https://stackoverflow.com/questions/17874360/python-how-to-parse-the-body-from-a-raw-email-given-that-raw-email-does-not
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get("Content-Disposition"))

                        # skip any text/plain (txt) attachments
                        if "text" in ctype and "attachment" not in cdispo:
                            body = part.get_payload(decode=True)
                            break
                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                else:
                    body = msg.get_payload(decode=True)

                body = asciiify(body)
                print(body)
                body = body[body.find(".")+1:body.rfind(".\r\n")+1]
                result.append({
                    "sender": msg["From"],
                    "subject": msg["Subject"],
                    "body": body
                })

    return result

# adapted from http://naelshiab.com/tutorial-send-email-python/
def send(outbox, sender, password, receiver, message):
    identifier = "".join([chr(random.randint(32, 127)) for i in range(10)])
    try:
        outbox.sendmail(sender, receiver, "TO: %s\r\n%s\r\n\r\n%s" % (receiver, identifier, message))
    except smtplib.SMTPSenderRefused: # log in again on timeout
        force_print("connection timed out. Reconnecting... ")
        outbox.connect("smtp.gmail.com", 465)
        outbox.ehlo()
        outbox.login(sender, password)
        outbox.sendmail(sender, receiver, "TO: %s\r\n%s\r\n\r\n%s" % (receiver, identifier, message))

def send_screen(outbox, sender, password, receiver):
    identifier = "".join([chr(random.randint(32, 127)) for i in range(10)])

    subprocess.call(["sh", "getscr"])
    img_data = open("/tmp/temp_screenshot.jpg", "rb").read()
    msg = MIMEMultipart()
    msg['Subject'] = ''
    msg['From'] = sender
    msg['To'] = receiver

    text = MIMEText(identifier)
    msg.attach(text)
    image = MIMEImage(img_data, name=os.path.basename("/tmp/temp_screenshot.jpg"))
    msg.attach(image)

    try:
        outbox.sendmail(sender, receiver, msg.as_string())
    except smtplib.SMTPSenderRefused: # log in again on timeout
        force_print("connection timed out. Reconnecting... ")
        outbox.connect("smtp.gmail.com", 465)
        outbox.ehlo()
        outbox.login(sender, password)
        outbox.sendmail(sender, receiver, msg.as_string())

if __name__ == "__main__":
    WELCOME_MESSAGE = "tsh: sh via text message\r\n- reply to this message with shell commands\r\n- \"exit\" to exit"

    argc = len(sys.argv) - 1
    if argc > 0:
        number = sys.argv[1]
    else:
        number = input("Phone number (numbers only): ")

    gateways = {
        "Alltel": { "sms": "message.alltel.com", "mms": "mms.alltelwireless.com" },
        "AT&T": { "sms": "txt.att.net", "mms": "mms.att.net" },
        "T-Mobile": { "sms": "tmomail.net", "mms": "tmomail.net" },
        "Virgin Mobile": { "sms": "vmobl.com", "mms": "vmpix.com" }, # "sms.myboostmobile.com"
        "Sprint": { "sms": "messaging.sprintpcs.com", "mms": "pm.sprint.com" },
        "Verizon": { "sms": "vtext.com", "mms": "vzwpix.com" },
        "US Cellular": { "sms": "mms.uscc.net", "mms": "mms.uscc.net" }
    }
    while True:
        if argc > 1:
            service = sys.argv[2]
        else:
            service = input("Phone service: ")
        if service not in gateways:
            print("Error: unknown service \"%s\"" % service)
            print("Choose one of (%s)" % ", ".join([s for s in gateways]))
            if argc > 1:
                exit()
        else:
            gateway = gateways[service]
            break
    phoneaddress = { "sms": number + "@" + gateway["sms"], "mms": number + "@" + gateway["mms"] }

    if argc > 2:
        address = sys.argv[3]
    else:
        address = input("GMail: ")
    address += "@gmail.com"

    password = getpass("Password: ")

    force_print("Connecting... ")
    inbox = imaplib.IMAP4_SSL("imap.gmail.com")
    inbox.login(address, password)
    force_print("done.\n")

    # adapted from https://stackoverflow.com/questions/17332384/python-3-send-email-smtp-gmail-error-smtpexception
    force_print("Sending initial text... ")
    outbox = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    outbox.login(address, password)
    send(outbox, address, password, phoneaddress["sms"], WELCOME_MESSAGE)
    force_print("done.\n")

    while True:
        force_print("Retrieving requests... ")
        try:
            requests = emails(inbox, phoneaddress)
        except: # imaplib.abort: # timed out
            force_print("connection timed out. Reconnecting... ")
            inbox.logout()
            inbox = imaplib.IMAP4_SSL("imap.gmail.com")
            inbox.login(address, password)
            requests = emails(inbox, phoneaddress)
        requests = [r["body"] for r in requests] # get text message
        requests = [r[0:r.find("\r\n")] for r in requests] # first line only
        requests = requests[::-1] # execute earliest to latest
        if len(requests) == 0:
            force_print("got nothing.\n")
        else:
            force_print("got: \n\t%s\n" % "\n\t".join(requests))
        for request in requests:
            force_print("Processing request: %s\n" % request)
            if request.strip() == "exit":
                force_print("Exiting.\n")
                send(outbox, address, password, phoneaddress["mms"], "> exit\r\nExiting tsh.")
                outbox.quit()
                exit()
            if request.strip() == "getscr":
                force_print("Sending screenshot... ")
                send_screen(outbox, address, password, phoneaddress["mms"])
                force_print("done.\n")
                continue
            result = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read()
            result = asciiify(result)
            force_print("Output: %s\n" % result)
            force_print("Sending output to %s... " % phoneaddress["mms"])
            send(outbox, address, password, phoneaddress["mms"], "> %s\r\n%s" % (request, result))
            force_print("done.\n")
        time.sleep(3)
