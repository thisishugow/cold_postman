# cold-postman  
**cold_postman** is a marketing tool to help users write cold mails in markdown and send them via a manageable csv file.


### Installation

`pip install cold_postman`


### Initialize the config

```bash
python -m cold_postman init db 
python -m cold_postman init config 
```
#### About `config.yaml`
```yaml
batch_num: 10 # mails sents per batch
password: ''  # password 
smtp_port: 587 # port
smtp_server: smtp.example.com # smtp server
user: 'example#example.com' # user mail
from: 'Mr.Example' 
```
#### About `control csv`

Control csv is the receiver list. Columns decribed as below:  
- `first_name`:  First name of the receiver.
- `last_name`:  Last name of the receiver.
- `email`:  Receiver's mail address.
- `last_sent`: Timestamp of last contact.
- `enabled`: (int) `[1, 0]`, `1`=*enabled*. `0`=*disabled*, which will be skiped while executing. 

### Send Mail
Command to start the sending task: 
```bash
# usage: __main__.py [-h] [-c CONFIG] [-d CRMDB] -m MESSAGE -t TITLE -s SIGNATURE [-a ATTACH]

# options:
#   -h, --help            show this help message and exit
#   -c CONFIG, --config CONFIG
#                         (Filepath) The file path of the config.
#   -d CRMDB, --crmdb CRMDB
#                         (Filepath) The file path of the crm DB.
#   -m MESSAGE, --message MESSAGE
#                         (Filepath) The email content in markdown.
#   -t TITLE, --title TITLE
#                         (str) The email title
#   -s SIGNATURE, --signature SIGNATURE
#                         (Filepath) The signature in markdown
#   -a ATTACH, --attach ATTACH
#                         (Filepath) The signature in markdown. 
python -m cold_postman -m message.md -t 'Subject of the Mail' -s signature.md -a attachment.zip
```  

### Prepare a markdown content
> The markdown content is converted to rtf via `markdown2`, which supports all the stardard syntax.    

The image wrapped in inline has to be written as following syntax.
```markdown
![image_cid](file_path.png)
```  
The alternative description will be applied as a cid in rtf, so please name it carefully and DO NOT be duplicated. To prevent from missing image, an absolute file path is recommended for attached image. 