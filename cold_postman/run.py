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
    parser.add_argument('-m','--message', help='(Filepath) The email content in markdown.', required=True)
    parser.add_argument('-t','--title', help='(str) The email title', required=True)
    parser.add_argument('-s','--signature', help='(Filepath) The signature in markdown', required=True)
    parser.add_argument('-a','--attach', help='(Filepath) The attachment', required=False)
    args = parser.parse_args()
    config_fn, _ = os.path.splitext(args.config)
    config = read_conf(config_fn)
    with open(args.message, 'r') as f:
        message = f.read()
    with open(args.signature, 'r') as f:
        signature = f.read()
    cp = ColdPostman(crm_db_path=args.crmdb, config=config)
    cp.set_md_content(message)
    cp.set_signature(signature)
    cp.set_title(args.title)
    if args.attach:
        cp.set_attach(args.attach)
    cp.run()

if __name__ == '__main__':
    main()
    