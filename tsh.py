import imaplib
import smtplib
import email
import time
import sys
import subprocess
from getpass import getpass

def emails(inbox, phoneaddress):
    # adapted from https://codehandbook.org/how-to-read-email-from-gmail-using-python/
    # imap search query from https://stackoverflow.com/questions/22856198/how-to-get-unread-messages-and-set-message-read-flags-over-imap-using-python
    inbox.select("inbox")
    type, data = inbox.search(None, "(UNSEEN)", "(FROM \"%s\")" % phoneaddress)
    ids = data[0].split()
    if len(ids) == 0:
        return []

    result = []
    for i in range(int(ids[-1]), int(ids[0]) - 1, -1):
        type, data = inbox.fetch(str(i), "(RFC822)")

        for part in data:
            if isinstance(part, tuple):
                msg = email.message_from_string(part[1].decode("utf-8"))

                # adapted from https://stackoverflow.com/questions/17874360/python-how-to-parse-the-body-from-a-raw-email-given-that-raw-email-does-not
                if msg.is_multipart():
                    for part in msg.walk():
                        ctype = part.get_content_type()
                        cdispo = str(part.get("Content-Disposition"))

                        # skip any text/plain (txt) attachments
                        if ctype == "text/plain" and "attachment" not in cdispo:
                            body = part.get_payload(decode=True)  # decode
                            break
                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                else:
                    body = msg.get_payload(decode=True)

                try: # breaks if not utf-8, but oh well
                    body = body.decode("utf-8")
                except:
                    continue
                result.append({
                    "sender": msg["From"],
                    "subject": msg["Subject"],
                    "body": body
                })

    return result

# adapted from http://naelshiab.com/tutorial-send-email-python/
def send(outbox, sender, receiver, message):
    outbox.sendmail(sender, receiver, ".\r\n" + message)

def force_print(s):
    sys.stdout.write(s)
    sys.stdout.flush()

WELCOME_MESSAGE = "Welcome to tsh.\r\n- reply to this message with shell commands\r\n- \"exit\" to exit"
address = input("GMail: ") + "@gmail.com"
password = getpass("Password: ")
number = input("Phone number (numbers only): ")
gateways = {
    "Alltel": "message.alltel.com",
    "AT&T": "txt.att.net",
    "T-Mobile": "tmomail.net",
    "Virgin Mobile": "vmobl.com",
    "Sprint": "messaging.sprintpcs.com",
    "Verizon": "vtext.com",
    "Nextel": "messaging.nextel.com",
    "US Cellular": "mms.uscc.net"
}
while True:
    service = input("Phone service: ")
    if service not in gateways:
        print("Error: unknown service \"%s\"" % service)
        print("Choose one of (%s)" % ", ".join([s for s in gateways]))
    else:
        gateway = gateways[service]
        break
phoneaddress = number + "@" + gateway

force_print("Connecting... ")
inbox = imaplib.IMAP4_SSL("imap.gmail.com")
inbox.login(address, password)
force_print("done.\n")

# adapted from https://stackoverflow.com/questions/17332384/python-3-send-email-smtp-gmail-error-smtpexception
force_print("Sending initial text... ")
outbox = smtplib.SMTP_SSL("smtp.gmail.com", 465)
outbox.login(address, password)
send(outbox, address, phoneaddress, WELCOME_MESSAGE)
force_print("done.\n")

while True:
    force_print("Retrieving requests... ")
    requests = emails(inbox, phoneaddress)
    requests = [r["body"] for r in requests]
    requests = [r[0:r.find("\r\n")] for r in requests]
    requests = requests[::-1]
    if len(requests) == 0:
        force_print("got nothing.\n")
    else:
        force_print("got: %s\n" % "".join(["\n\t" + r for r in requests]))
    for request in requests:
        force_print("Processing request: %s\n" % request)
        if request.strip() == "exit":
            force_print("Exiting.\n")
            send(outbox, address, phoneaddress, "Exiting tsh.")
            outbox.quit()
            exit()
        result = subprocess.Popen(request, shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")
        force_print("Output: %s\n" % result)
        force_print("Sending output to %s... " % phoneaddress)
        send(outbox, address, phoneaddress, "> %s\r\n%s" % (request, result))
        force_print("done.\n")
    time.sleep(3)
