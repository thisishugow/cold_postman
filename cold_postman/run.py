import argparse, sys, os, logging
from cold_postman.postman import ColdPostman
from cold_postman import read_conf, init_conf, init_crmdb
logging.basicConfig(format='%(asctime)s - %(name)s - [%(levelname)s]: %(message)s', datefmt='[%Y-%m-%d %H:%M:%S]')
log = logging.getLogger()
log.setLevel(logging.INFO)


def main():
    argv = [ a.strip() for a in sys.argv[1:]]
    cmd_ = '' if len(argv)==0 else argv[0]
    if 'init' == cmd_:
        try:
            fp = None if len(argv) <=2 else argv[2]
            if 'config' == argv[1]:
                if fp:
                    init_conf(argv[2])
                else: 
                    init_conf()
            elif 'db' == argv[1]:
                if fp:
                    fn, ext = os.path.splitext(fp)
                    init_crmdb(fn, ext.strip('.'))
                else:
                    init_crmdb()
            else:
                raise Exception('Invalid arg')
        except Exception as e:
            print('\n\tHINT: Please use `init config <filepath>` or `init db <filepath>`\n')

        return 
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-c','--config', help='(Filepath) The file path of the config.', default='config', required=False)
    parser.add_argument('-d','--crmdb', help='(Filepath) The file path of the crm DB.', default='cold_postman_db.csv', required=False)
    parser.add_argument('-m','--message', help='(Filepath) REQUIRED. The email content in markdown/html.', required=True)
    parser.add_argument('-t','--title', help='(str) REQUIRED. The email title', required=True)
    parser.add_argument('-s','--signature', help='(Filepath) REQUIRED. The signature in markdown', required=True)
    parser.add_argument('-a','--attach', help='(Filepath) The attachment', required=False)
    parser.add_argument('-u','--unsubscribe', help='(Bool) [True, False] Enable a unsubscribe link. Default=True', required=False, default=True)
    parser.add_argument('-i','--interval', help='(Int) Interval (secs) between batchs. Default=10', required=False, default=10)
    args = parser.parse_args()
    config_fn, _ = os.path.splitext(args.config)
    config = read_conf(config_fn)
    with open(args.message, 'r') as f:
        message = f.read()
    with open(args.signature, 'r') as f:
        signature = f.read()
    cp = ColdPostman(crm_db_path=args.crmdb, config=config)
    _, extname = os.path.splitext(args.message)
    if extname.lower() == '.html':
        cp.set_html_content(message)
    elif extname.lower() == '.md':
        cp.set_md_content(message)
    else:
        _msg = "⚠️ WARNING: Message must be a file of .html or .md"
        print( '\x1b[33;20m' + _msg + '\x1b[0m')
        sys.exit(1)
    cp.set_signature(signature)
    cp.set_title(args.title)
    if args.attach:
        cp.set_attach(args.attach)
    unsubscribe = False if str(args.unsubscribe).lower() == 'false' else True
    cp.set_unsubscribe(unsubscribe)
    cp.batch_interval = args.interval
    cp.run()

if __name__ == '__main__':
    main()
    