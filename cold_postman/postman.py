# Send an HTML email with an embedded image and a plain text message for
# email clients that don't want to display the HTML.
from email import encoders
from email.mime.base import MIMEBase
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from markdown2 import markdown as md
import re, os
from time import sleep
import pandas as pd
import pendulum
from pandas.core.frame import DataFrame

from cold_postman import init_crmdb

log = logging.getLogger()

REST_SEC:int = 10
INTERVAL:float = 0.2
VERBOSE = False

class ColdPostman:
    def __init__(self, *, crm_db_path: os.PathLike, config: dict = None) -> None:
        """_summary_

        Args:
            crm_db_path (os.PathLike): Control table (accepts .csv, sqlite3)
            config (dict, optional): config. Defaults to None.
        """
        self.title: str = None
        self.md_content: str = None
        self.config: dict = config
        self.crm_db_path: os.PathLike = crm_db_path
        self.crm_db: DataFrame = self._read_crm(crm_db_path)
        self.rtf: str = None
        self.attachments:list = []
        self.signature: str = None
        self.from_ = config['from']

    def set_title(self, title: str):
        """set the mail title

        Args:
            title (str): mail title
        """
        self.title = title
        

    def set_signature(self, signature:str):
        """set the mail signature

        Args:
            signature (str): signature in markdown
        """
        self.signature = md(signature)
        self._md_signature = signature

    def set_md_content(self, md_content: str):
        """Set the markdown content. The method will transform it and set to mail's rtf

        Args:
            md_content (str): the content in markdown.
        """
        self.md_content = md_content
        
    def set_from_(self, alias:str):
        """Set the sendor alias

        Args:
            alias (str): sendor alias. 
        """
        self.from_ = alias
    
    def set_attach(self, files:list | str):
        if type(files) == str:
            files = [files,]
        self.attachments = files

    def run(self):
        """start to send mail."""

        df: DataFrame = self.crm_db
        receivers = df[df["enabled"] == 1][["first_name", "last_name", "email"]]
        log.info(f"""Start to connect to: {self.config["smtp_server"]}:{self.config["smtp_port"]}""")
        smtp = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
        if smtp.ehlo()[0] != 250:
            raise Exception(f"SMTP Server responsed code: {smtp.ehlo()[0] }")
        log.info(f"""Connected successfully. Login with user: {self.config['user']}""")
        smtp.starttls()
        smtp.login(self.config["user"], self.config["password"])
        log.info(f"""Login successfully.""")
        rest_sec: int = REST_SEC
        batch_cnt: int = 0
        update_states: list = []
        rtf: str = md(self.md_content) + self.signature
        image_dict = extract_images_from_md(self.md_content + self._md_signature)
        log.debug(image_dict)
        image_cids:list = []
        for cid, url in image_dict.items():
            tmp = url_to_cid(url, cid)
            image_cids.append(tmp)
        for j in image_cids:
            _cid, _url, _ = j
            rtf = rtf.replace(_url, f"""cid:{_cid}""")

        # Start sending task.
        for i, row in receivers.iterrows():
            self.msg_root: MIMEMultipart = MIMEMultipart()
            self.msg_root['Subject'] = self.title
            self.msg_root['From'] = self.from_
            self.rtf = rtf
            first_name, last_name, email_addr = row
            name = f"{first_name} {last_name}"
            _rtf: str = f"<br>Hi {name},<br><br>" + self.rtf 
            log.debug(_rtf)
            msg_text = MIMEText(_rtf, "html")
            self.msg_root.attach(msg_text)

            # Attach images
            for j in image_cids:
                _, _, img = j
                self.msg_root.attach(img)
            
            # Attach files
            for file in self.attachments:
                with open(file, 'rb') as fp:
                    add_file = MIMEBase('application', "octet-stream")
                    add_file.set_payload(fp.read())
                encoders.encode_base64(add_file)
                add_file.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file))
                self.msg_root.attach(add_file)
            self.msg_root['To'] = email_addr
            try:
                smtp.sendmail(self.config["user"], email_addr, self.msg_root.as_string())
            except Exception as e:
                log.info(f"""Failed on '{name}'-'{email_addr}'.""")
                log.error(e, exc_info=VERBOSE)
                continue
            batch_cnt += 1
            update_states.append((i, pendulum.now()))
            log.info(f"""Sent to '{name}'-'{email_addr}' successfully.""")
            sleep(INTERVAL)  # rest for avoiding to be detected as DDos
            if batch_cnt >= self.config['batch_num']:
                sleep(rest_sec)  # rest for avoiding to be detected as DDos
        smtp.close()
        self._update_crm(updates=update_states)

    def _read_crm(self, crm_db_path: os.PathLike) -> DataFrame:
        """_summary_

        Returns:
            DataFrame: be like
            ```
            {
                'first_name':['Joe',],
                'last_name':['Wayne',],
                'email':['joe.wayne@example.org',],
                'last_sent':['2023-09-04T17:10:23.558397+08:00',],
                "enabled":[1, ]
            }
            ```
        """

        fp: str = crm_db_path
        df: DataFrame = None
        _, extname = os.path.splitext(fp.lower())
        if extname == ".csv":
            df = pd.read_csv(fp)
        else:
            import sqlite3

            con = sqlite3.connect(fp)
            df = pd.read_sql("SELECT * FROM CRM", con=con)
        return df

    def _update_crm(self, updates: list) -> None:
        """update "last_sent" in the CRM database

        Args:
            updates (list): the list consist of `(id, timestamp<str>)`
            ```
            [(1, '2023-09-04T17:10:23.558397+08:00'),]
            ```
        """
        df = self.crm_db
        for i in updates:
            idx, update_dtt = i
            df.at[idx, "last_sent"] = update_dtt
        fn, extn = os.path.splitext(self.crm_db_path)
        init_crmdb(fn, extn.strip('.'), df)


def extract_images_from_md(md:str) -> dict:
    """Extract all images and their cids and return as a dict.  

    Args:
        md (str): the markdown string

    Returns:
        dict: the key-value pair of cid and and img url. Example: {'cid_1':'https:www.example.com/img1.png'}
    """
    d = {}
    pattern = r"!\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, md)
    for match in matches:
        d[match[0]] = match[1]
    return d


def url_to_cid(url: str, cid: str):
    """Register the image to MIMEImage

    Args:
        url (str): path of image
        cid (str): cid of image

    Returns:
        tuple: (cir<str>, url<str>, <MIMEImage>)
    """
    with open(url, "rb") as f:
        msgImage = MIMEImage(f.read())
        # Define the image's ID as referenced above
        msgImage.add_header("Content-ID", cid)
    return (cid, url, msgImage)
