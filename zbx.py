import logging
from pyzabbix import ZabbixMetric, ZabbixSender
from pyzabbix.api import ZabbixAPI
import requests

#ZAPI: Rappresenta l'istanza della connessione con zabbix

ZABBIX_URL = "http://172.16.104.2:80"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"


try:
    ZAPI = ZabbixAPI(url=ZABBIX_URL, user=ZABBIX_USER, password=ZABBIX_PASSWORD)
except:
    logging.error("Connessione a Zabbix fallita.")

def get_zabbix_url(): return ZABBIX_URL
def get_zabbix_usr(): return ZABBIX_USER
def get_zabbix_psw(): return ZABBIX_PASSWORD


def print_logo():
    return ("""\
    
    
    
   _____                      _          _____           _                 
  / ____|                    | |        / ____|         | |                
 | |     __ _ _ __ ___  _ __ | |_ ___  | (___  _   _ ___| |_ ___ _ __ ___  
 | |    / _` | '__/ _ \| '_ \| __/ _ \  \___ \| | | / __| __/ _ \ '_ ` _ \ 
 | |___| (_| | | | (_) | | | | ||  __/  ____) | |_| \__ \ ||  __/ | | | | |
  \_____\__,_|_|  \___/|_| |_|\__\___| |_____/ \__, |___/\__\___|_| |_| |_|
                                                __/ |                      
                                               |___/                       
                 _*^*_Created for WhySecurity_*^*_
    """)





def get_template_id(template_name:str)->str:
    return (ZAPI.do_request('template.get',{'output':'extend','filter':{'host':[template_name]}})['result'])[0]['templateid']


def assign_template(group_name:str, template_name:str)->bool:
    try:
        id = get_template_id(template_name)
        group_id = get_group_info(group_name)[1]

        ZAPI.do_request('template.massadd',{'templates':[{'templateid':id}],'groups':[{'groupid':group_id}]})
    except:
        print("OK")


def get_all_host():
    return ZAPI.host.get(monitored_host=1,output='extend')

def check_host_existence(nome_host:str)->bool:
    hosts = get_all_host()
    host = [host['host'] for host in hosts if(host['host'] == nome_host)]
    return True if host else False

#Ritorna le informazioni relative ad un gruppo cercato per nome, il risultato coniene il ['Nome gruppo','ID gruppo']
def get_group_info(group_name:str)->[]:
    all_groups = ZAPI.do_request('hostgroup.get')
    risultato = []
    for group in all_groups['result']:
        if(group['name'] == group_name):
            risultato.extend((group['name'],group['groupid']))
            break
    return risultato

def create_a_host(nome_host:str,group_name:str)->bool:
    try:
        group_id = get_group_info(group_name)[1] # Il primo elemento contiene l'id del gruppo
        ZAPI.do_request('host.create', {'host': nome_host, 'groups': {'groupid': group_id, 'name': group_name}})
        return True
    except:
        logging.error("Classe Zabbix.py: Non è stato creato l'host.")
        return False


def get_host_id(nome_host:str)->str:
    try:
        return ZAPI.host.get(monitored_host=1,output='extend',filter={'host':nome_host})[0]['hostid']
    except:
        logging.error("Impossibile ricavare ID dell'host inserito. Errore nel nome probabilmente.")

#TYPE:
# 0 - Zabbix agent;      2 - Zabbix trapper;           3 - Simple check;
# 5 - Zabbix internal;   7 - Zabbix agent (active);    9 - Web item;
# 10 - External check;   11 - Database monitor;        12 - IPMI agent;
# 13 - SSH agent;        14 - Telnet agent;            15 - Calculated;
# 16 - JMX agent;        17 - SNMP trap;               18 - Dependent item;
# 19 - HTTP agent;       20 - SNMP agent;              21 - Script
#VALUE TYPE:
# 0-numeric float;   1-character;     2-log;   3-numeric unsigned;   4-text.
def create_item(nome_host:str,nome_item:str,key:str,type_item:int,value_type:int)->bool:
    return True if ZAPI.do_request('item.create',{'hostid':get_host_id(nome_host),'name':nome_item,'key_':key,'type':type_item,'value_type':value_type}) else False

def create_trigger(description:str,expression:str,severity:int,host_name:str)->bool:
    if expression.__contains__("{HOSTNAME}"): expression=expression.replace("{HOSTNAME}",host_name)
    return True if ZAPI.do_request('trigger.create',{"description": description,"expression": expression,'priority':severity}) else False


def get_item(nome_host:str,filter_name = None):
    if(filter_name is not None and len(filter_name)>1):
        return ZAPI.do_request('item.get',{"output": "extend","hostids": get_host_id(nome_host),'search':{'key_':filter_name}})
    else:
        return ZAPI.do_request('item.get',{"output": "extend","hostids": get_host_id(nome_host)})


def get_all_trigger_description(host_name:str)->[]:
    risultato = []
    triggers = get_triggers_of_host(host_name)
    for single_trig in triggers['result']:
        risultato.append(single_trig['description'])
    return risultato

def get_triggers_of_host(host_name:str)->[]:
    return ZAPI.do_request('trigger.get',{'host':host_name})


if __name__ == '__main__':
    print(assign_template("Discovered hosts","CaronteSystem"))



    # zapi.do_request('trigger.create',{"description": "Processor load is too high ",
    #                                   "expression": "last(/PCUT-RIGANTI/dependent.item)=0",
    #                                   "tags": [
    #                                       {
    #                                           "tag": "service",
    #                                           "value": "{{ITEM.VALUE}.regsub(\"Service (.*) has stopped\", \"\\1\")}"
    #                                       },
    #                                       {
    #                                           "tag": "error",
    #                                           "value": ""
    #                                       }
    #                                   ]})
