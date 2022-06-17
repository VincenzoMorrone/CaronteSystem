import datetime
import sys
import shutil
import imaplib
import email
from email.header import decode_header
import os
import csv
import requests
import colorlog
import logging
from pyzabbix.api import ZabbixAPI
import zbx as zbx


folderNameArray = []
read_mail_list = []

def check_old_folder()->bool:
    rootdir = '.'
    for file in os.listdir(rootdir):
        d = os.path.join(rootdir, file)
        if os.path.isdir(d):
            if (d.__contains__("FileScan_Report_")):
                shutil.rmtree(d)
                return True
    return False


def logger_config(name=None):
    import logging
    import colorlog
    if not name:
        log = logging.getLogger()  # root logger
    else:
        log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    format_str = '%(asctime)s %(levelname)-8s  %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    cformat = '%(log_color)s' + format_str
    colors = {'DEBUG': 'cyan',
              'INFO': 'green',
              'WARNING': 'bold_yellow',
              'ERROR': 'bold_red',
              'CRITICAL': 'bold_purple'}
    formatter = colorlog.ColoredFormatter(cformat, date_format,
                                          log_colors=colors)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)
    return log

logging = logger_config()



def getEmailDatetime(data):
    data1 = (str(data).split("+")[0].split(", ")[1]).strip()
    dataCorretta = datetime.datetime.strptime(data1, '%d %b %Y %H:%M:%S')
    return dataCorretta

def get_def():
    username = "lab4@whysecurity.it"
    password = "1234Vin"
    results = "["
    users = []

    def clean(text):
        return "".join(c if c.isalnum() else "_" for c in text)

    imap = imaplib.IMAP4_SSL("outlook.office365.com")
    # authenticate
    try:
        imap.login(username, password)
        logging.info("Login completato")
    except:
        logging.error("Login fallito")

    status, messages = imap.select('"{}"'.format("INBOX/FileScan Report"))

    messages = int(messages[0])
    N = messages
    DAYS = 15
    logging.info("Saranno scaricati " + str(N) + " messaggi degli ultimi " + str(DAYS) + " giorni.")

    for i in range(messages, messages - N, -1):
        # fetch the email message by ID
        res, msg = imap.fetch(str(i), "(RFC822)")
        for response in msg:

            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                if(getEmailDatetime(msg['Date']) > datetime.datetime.now() - datetime.timedelta(DAYS)):

                    # decode the email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding)
                    From, encoding = decode_header(msg.get("From"))[0]

                    if(subject.__contains__("FileScan Report") and read_mail_list.__contains__(subject) == False):
                        logging.info("Lettura mail: " + subject + " del giorno " + msg['Date'])
                        read_mail_list.append(subject)

                        if msg.is_multipart():

                            # iterate over email parts
                            for part in msg.walk():
                                # extract content type of email
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                try:
                                    # get the email body
                                    body = part.get_payload(decode=True).decode()
                                except:
                                    pass
                                if "attachment" in content_disposition:
                                    # download attachment
                                    filename = part.get_filename()
                                    if filename:
                                        folder_name = clean(subject)

                                        #imap.store(str(i),'+FLAGS','\\Deleted')


                                        if not os.path.isdir(folder_name):
                                            # make a folder for this email (named after the subject)
                                            os.mkdir(folder_name)
                                            if not(folderNameArray.__contains__(folder_name)):
                                                folderNameArray.append(folder_name)
                                        filepath = os.path.join(folder_name, filename)
                                        # download attachment and save it
                                        open(filepath, "wb").write(part.get_payload(decode=True))
                        else:
                            # extract content type of email
                            content_type = msg.get_content_type()
                            # get the email body
                            body = msg.get_payload(decode=True).decode()


                        if content_type == "csv":

                            # if it's HTML, create a new HTML file and open it in browser
                            folder_name = clean(subject)
                            #folderNameArray.append(folder_name)
                            if not os.path.isdir(folder_name):
                                # make a folder for this email (named after the subject)
                                os.mkdir(folder_name)
                            filename = "index.html"
                            filepath = os.path.join(folder_name, filename)
                            # write the file
                            open(filepath, "w").write(body)

    # close the connection and logout

    imap.close()
    imap.logout()
    stringMaker = ""
    #print(len(folderNameArray))
    for folder in folderNameArray:
        print(folder + '/File Details by Category.csv')
        with open(folder + '/File Details by Category.csv') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            c = 0
            conteggio = 0
            logging.warning("Verifico l'esistenza degli host su Zabbix. Può richiedere molto tempo...")

            for row1 in csv_reader:
                c += 1
                if (zbx.check_host_existence(row1[0]) == False ):
                    zbx.create_a_host(row1[0], "CaronteSystemGroup")
                    logging.warning(" Host non presente in Zabbix: " + row1[0] + " : è stato creato.")
                    users.append(row1[0])
                else:
                    logging.info("Host già presente: " + row1[0])
                if( (c % 50) == 0):
                    with open("log.txt", "a") as log_file:
                        log_file.write(str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")) + " Running...\n")


            logging.warning("Inizio ad inviare dati a Zabbix:")
        with open(folder + '/File Details by Category.csv') as csv_file1:
            csv_reader = csv.reader(csv_file1, delimiter=',')
            for row in csv_reader:
                c += 1
                val = 0
                if (row[7].__contains__("GB")):
                    row[7] = row[7].replace("GB", "")
                    val = float(row[7]) * 1000
                elif (row[7].__contains__("KB")):
                    row[7] = row[7].replace("KB", "")
                    val = float(row[7]) / 1000
                elif (row[7].__contains__("MB")):
                    row[7] = row[7].replace("MB", "")
                    val = float(row[7])
                logging.info("Invo dato: " + row[3] + " per host: " + row[0])
                requests.get("http://172.16.104.2:5005/?ip=172.16.104.2&hostname=" + row[0] + "&item=" + row[3].replace(" ","_")+"_NUMBER" + '&value="' + row[6] + '"')
                requests.get("http://172.16.104.2:5005/?ip=172.16.104.2&hostname=" + row[0] + "&item=" + row[3].replace(" ","_")+"_DIMENSION" + '&value="' + str(val) + '"')
                if ((c % 50) == 0):
                    with open("log.txt", "a") as log_file:
                        log_file.write(str(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")) + " Running... \n")

    for folder in folderNameArray:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    return results[:-1] + "]"

if __name__ == '__main__':
    logging.info(zbx.print_logo())
    logging.info("CaronteSystem")
    if(check_old_folder()):
        logging.warning("Elimino vecchie cartelle e-mail, l'ultima esecuzione software potrebbe non aver concluso bene.")
    get_def()
    logging.info("_*^*_| Carone has finished his work |_*^*_")

