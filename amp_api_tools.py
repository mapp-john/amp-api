# Import Required Modules
import os
import re
import sys
import csv
import json
import socket
import random
import netaddr
import getpass
import requests
import xmltodict
import traceback
from json.decoder import JSONDecodeError

#
#
#
# Define Blank URL Get Script as Function
def BlankGet(config):
    print ('''
***********************************************************************************************
*                             Basic URL GET Script                                            *
*_____________________________________________________________________________________________*
*                                                                                             *
* USER INPUT NEEDED:                                                                          *
*                                                                                             *
*  1. URI Path (/api/fmc_config/v1/domain/{domain_UUID}/object/networkgroups/{object_UUID})   *
*                                                                                             *
*  2. Expand output to show details of each object *(Not Supported with {object_UUID} GET)    *
*                                                                                             *
*  3. Limit output to a specific number of objects *(Not Supported with {object_UUID} GET)    *
*                                                                                             *
*  4. Save output to file                                                                     *
*                                                                                             *
*                                                                                             *
***********************************************************************************************
''')
    # Ask if JSON output should be saved to File
    save = input('Would You Like To Save The JSON Output To File? [y/N]: ').lower()
    if save in (['yes','ye','y']):
        # Random Generated JSON Output File
        filename = ''
        for i in range(6):
            filename += chr(random.randint(97,122))
        filename += '.txt'
        print(f'*\n*\nRANDOM OUTPUT FILE CREATED... {filename}\n')
        with open(filename, 'a') as OutFile:
            OutFile.write(json.dumps(JSON,indent=4))
    elif save in (['no','n','']):
        print(json.dumps(JSON,indent=4))

    return

#
#
#
# Define Blank URL Get Script as Function
def PolicyDownload(config):
    print ('''
***********************************************************************************************
*                             Download all Endpoint Policies                                  *
*_____________________________________________________________________________________________*
*                                                                                             *
* USER INPUT NEEDED:                                                                          *
*                                                                                             *
*  1. Save Policies as XML or JSON                                                            *
*                                                                                             *
***********************************************************************************************
''')
    # Set Variables for use
    debug = config['debug']
    api_id = config['api_id']
    api_key = config['api_key']
    server = config['server']

    # Setup AMP for Endpoints session and auth
    session = requests.session()
    session.auth = (api_id, api_key)
    # Policies URL
    url = f'https://{server}/v1/policies'
    try:
        # Get First page of Polices
        response = session.get(url)

        # Decode JSON response
        response_json = response.json()

        # Store policy link, product, and name in a dict {'link' : 'product_name'}
        policies = {
            policy['links']['policy']: f'{policy["product"]}_{policy["name"]}' for policy in response_json['data']
        }

        # Paginate if needed
        while 'next' in response_json['metadata']['links']:
            next_url = response_json['metadata']['links']['next']
            response = session.get(next_url)
            response_json = response.json()
            for policy in response_json['data']:
                # Store link, product, and name in existing dictionary
                policies[policy['links']['policy']] = f'{policy["product"]}_{policy["name"]}'

        # Get script file path
        path = os.path.dirname(os.path.realpath(__file__))

        # Build absolute path for 'policies' dir
        output_path = os.path.join(path, 'policies')

        # Check if output_path exists, create if not
        if not os.path.exists(f'{output_path}'):
            os.makedirs(f'{output_path}')

        print(f'Number of polices found: {len(policies)}')
        while True:
            save = input('Would you like to save Policies as XML or JSON? [xml/json]: ').lower().strip()
            if save in (['xml','xm','x']):
                save = 'xml'
                break
            elif save in (['json','jso','js','j','']):
                save = 'json'
                break
            else:
                print('INVALID ENTRY... ')

        print('Downloading Policies....\n')

        # Iterate over policies, download and save the XML as JSON to disk
        for count, (policy_link, name) in enumerate(policies.items(), start=1):
            guid = policy_link.split('/')[-1]
            response = session.get(f'{policy_link}.xml')
            # Save files as XML
            if save == 'xml':
                with open(f'{output_path}/{name}_{guid}.xml', 'w') as f:
                    f.write(response.text)
            # Save files as JSON
            elif save == 'json':
                with open(f'{output_path}/{name}_{guid}.json', 'w') as f:
                    f.write(json.dumps(xmltodict.parse(response.text),indent=4))
            print(f'{(len(policies)+1)-count }: {name} - DONE!')


    except:
        print(f'{traceback.format_exc()}')

    session.close()

    return





#
#
#
# Run Script if main
if __name__ == '__main__':
    #
    #
    #
    # Initial input request
    print ('''
***********************************************************************************************
*                                                                                             *
*                   Cisco AMP Cloud API Tools (Written for Python 3.6+)                       *
*                                                                                             *
***********************************************************************************************
*                                                                                             *
* USER INPUT NEEDED:                                                                          *
*                                                                                             *
*  1. JSON Config File (config.json) in current working directory                             *
*       IE:                                                                                   *
*       {                                                                                     *
*	"debug" : false,                                                                      *
*	"api_id": "xxxxxxxxxxxxxxxxxx",                                                       *
*	"api_key" : "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxx",                                       *
*	"server" : "api.amp.cisco.com"                                                        *
*                                                                                             *
*        }                                                                                    *
*                                                                                             *
***********************************************************************************************
''')

    Test = False
    while not Test:
        try:
            # Import variables to get configuration
            config = json.loads(open('config.json').read())
            print('Config File found...')
        except (FileNotFoundError,JSONDecodeError):
            print('Config File not found or invalid format...')
            create = input('Would you like to create the config file now? [y/N]: ').lower().strip()
            if create in (['yes','ye','y']):
                api_id = input('Enter API ID: ').strip()
                api_key = input('Enter API Key: ').strip()
                server = input('Enter AMP Server: ').strip()
                config = {
                    'debug':False,
                    'api_id':api_id,
                    'api_key':api_key,
                    'server':server
                }
                with open('config.json','w') as F:
                    F.write(json.dumps(config,indent=4))
            else:
                exit()
        server = config['server']
        # Validate FQDN
        if server[-1] == '/':
            server = server[:-1]

        # Perform Test Connection To FQDN
        s = socket.socket()
        print(f'Attempting to connect to {server} on port 443')
        try:
            s.connect((server, 443))
            print(f'Connecton successful to {server} on port 443')
            Test = True
        except Exception as e:
            print(f'Connection to {server} on port 443 failed: {e}')
            sys.exit()

    print ('''
***********************************************************************************************
*                                                                                             *
* TOOLS AVAILABLE:                                                                            *
*                                                                                             *
*  1. Basic URL GET                                                                           *
*                                                                                             *
*  2. Download all Endpoint Policies                                                          *
*                                                                                             *
*  3. Run Endpoint Policy comparison report                                                   *
*                                                                                             *
***********************************************************************************************
''')

    #
    #
    #
    # Run script until user cancels
    while True:
        Script = False
        while not Script:
            script = input('Please Select Script: ')
            if script == '1':
                Script = True
                BlankGet(config)
            elif script == '2':
                Script = True
                PolicyDownload(config)
            elif script == '3':
                Script = True
                PolicyReport(config)
            else:
                print('INVALID ENTRY... ')

        # Ask to end the loop
        print ('''
***********************************************************************************************
*                                                                                             *
* TOOLS AVAILABLE:                                                                            *
*                                                                                             *
*  1. Basic URL GET                                                                           *
*                                                                                             *
*  2. Download all Endpoint Policies                                                          *
*                                                                                             *
*  3. Run Endpoint Policy comparison report                                                   *
*                                                                                             *
***********************************************************************************************
''')
        Loop = input('*\n*\nWould You Like To use another tool? [y/N]: ').lower()
        if Loop not in (['yes','ye','y']):
            break


