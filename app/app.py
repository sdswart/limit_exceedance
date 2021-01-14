import argparse
import json

from config import config
from queries import data_query, equipment_query
from model import run_algorithm

def info():
    with open('info.txt') as f:
        return f.read()

def main():
    ''' Run model and then quit
    '''
    run_algorithm(config)

parser = argparse.ArgumentParser(description='Limit exceedance')
parser.add_argument('--info', action='store_true',
                   help='get model info')
parser.add_argument('--path', dest='datapath', default='/data',
                  help='data path (default=/data)')
parser.add_argument('commands', nargs='*', )

args = parser.parse_args()
if __name__ == "__main__":
    if args.info:
        res=info()
    elif 'query' in args.commands:
        res=json.dumps(equipment_query)
    elif 'data' in args.commands:
        res=json.dumps(data_query)
    elif 'version' in args.commands:
        res=config.VERSION
    else:
        res=main()
