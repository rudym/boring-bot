"""
The main entrypoint layer to our bot application. 
"""

import sys
import logging
import logging.config
import settings
from app import App

def main(debug=False):
    '''init logging'''
    kw = {
        'format': '[%(asctime)s] %(message)s',
        'datefmt': '%d/%m/%Y %H:%M:%S',
        'level': logging.INFO if debug else logging.DEBUG,
        'stream': sys.stdout,
    }
    logging.basicConfig(**kw)

    '''init app'''
    app = App()
    app.run(debug)
    
if __name__ == '__main__':
    main(settings.DEBUG)