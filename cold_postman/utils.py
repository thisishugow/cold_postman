from typing import Literal, Union
import yaml, json, logging
import os
import pandas as pd
from pandas.core.frame import DataFrame
import csv, sqlite3
log = logging.getLogger()

CONF_TEMPLATE = {
    'smtp_server':'smtp.example.org',
    'smtp_port':587,
    'user':'example',
    'password':'Pas$w0rd',
    'batch_num':10,
    'from':'',
    'unsubscribe':{
        'link':'',
        'subject':'Unsubscribe',
        'message':"I'd like to unsubscribe.",
    }
}

    

def read_conf(fp:Union[str, bytes, os.PathLike], format:Literal['yaml', 'json']='yaml', encoding:str='utf8')-> dict:
    """Read a ['yaml', 'json'] config.

    Args:
        fp (Union[str, bytes, os.PathLike]): file path of the config
        format (str, optional): the type of the config ['json', 'yaml'].  Defaults to 'yaml'.
        encoding (str, optional): encoding of the file. Defaults to 'utf8'.

    Returns:
        dict: config in dict. Example: 
        ```
        {
            'smtp_server':'smtp.example.org',
            'smtp_port':587,
            'user':'example',
            'password':'Pas$w0rd',
            'batch_num':100,
            'from':'',
            'unsubscribe':{
                'link':'',
                'subject':'Unsubscribe',
                'message':"I'd like to unsubscribe.",
            }
        }
        ```
    """
    res = {}
    _fp = os.path.realpath(fp) + f'.{format.strip()}' if format else os.path.realpath(fp)
    with open(_fp, 'r', encoding=encoding) as f:
        if not format or format.lower() in ['yaml', 'yml']:
            res = yaml.safe_load(f)
        elif format.lower() in ['json']:
            res = json.load(f)
    return res
    


def init_conf(fp:Union[str, bytes, os.PathLike]='config.yaml'):
    """Initialize a yaml config.

    Args:
        fp (Union[str, bytes, os.PathLike]): _description_
    """
    with open(fp, 'w', encoding='utf8') as f:
        yaml.dump(CONF_TEMPLATE, f)  


def init_crmdb(fp:os.PathLike='cold_postman_db',astype:Literal['csv', 'sqlite']='csv', df:DataFrame=None):
    """Initialize a database of CRM

    Args:
        fp (os.PathLike, optional): file path. Defaults to 'cold_postman_db'.
        astype (Literal[&#39;csv&#39;, &#39;sqlite&#39;], optional): save type. Defaults to 'csv'.
    """
    is_update_df = False if df is None else True
    if is_update_df:
        log.warning('Update the existing db.') 
    else:
        d = {
            'first_name':['Joe',],
            'last_name':['Wayne',],
            'email':['joe.wayne@example.org',],
            #'email_titie':['A Test Email'],
            #'email_content':['<b>Some <i>HTML</i> text</b> test <br> test!'],
            'last_sent':['2023-09-04T17:10:23.558397+08:00',],
            "enabled":[0, ]
        }
    dest_fp = f"{fp}.{astype}"
    if astype=='csv':
        if is_update_df:
            df.to_csv(dest_fp, index=False, quotechar='"', quoting=csv.QUOTE_ALL)
        else:
            pd.DataFrame(d).to_csv(dest_fp, index=False, quotechar='"', quoting=csv.QUOTE_ALL)
    else:
        con = sqlite3.connect(dest_fp)
        if is_update_df:
            df.to_sql('CRM', index=False, con=con, if_exists='replace')
        else:
            pd.DataFrame(d).to_sql('CRM', index=False, con=con, if_exists='append')

