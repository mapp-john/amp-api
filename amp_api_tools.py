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
from pandas import json_normalize,concat
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
*  1. URI Path (/v1/computers)                                                                *
*                                                                                             *
*  4. Save output to file                                                                     *
*                                                                                             *
***********************************************************************************************
''')
    # Set Variables for use
    debug = config['debug']
    api_id = config['api_id']
    api_key = config['api_key']
    server = config['server']

    # Request URI for GET
    uri = input('Please provide URI path: ').strip()
    url = f'https://{server}{uri}'

    # Setup AMP for Endpoints session and auth
    session = requests.session()
    session.auth = (api_id, api_key)
    try:
        # Get First page
        response = session.get(url)
        # Decode JSON response
        response_json = response.json()
        # Debug Print
        if debug: print(json.dumps(response_json,indent=4))

        # Add each item from the response data to a new dicitonary
        data = [
            item for item in response_json['data']
        ]
        # Paginate if needed
        while 'next' in response_json['metadata']['links']:
            next_url = response_json['metadata']['links']['next']
            response = session.get(next_url)
            response_json = response.json()
            for item in response_json['data']:
                # add each item to existing data dictionary
                data.update(item)

        # Ask if JSON output should be saved to File
        save = input('Would You Like To Save The JSON Output To File? [y/N]: ').lower()
        if save in (['yes','ye','y']):
            # Random Generated JSON Output File
            filename = ''
            for i in range(6):
                filename += chr(random.randint(97,122))
            filename += '.txt'
            print(f'*\n*\nRANDOM OUTPUT FILE CREATED... {filename}\n')
            with open(filename, 'w') as OutFile:
                OutFile.write(json.dumps(data,indent=4))
        elif save in (['no','n','']):
            print(json.dumps(data,indent=4))
    except:
        print(f'{traceback.format_exc()}')
    # Close Requests session
    session.close()

    return

#
#
#
# Define Policy Download as Function
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
        # Debug Print
        if debug: json.dumps(response_json)

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
# Define Policy Report as Function
def PolicyReport(config):
    print ('''
***********************************************************************************************
*                        Create Policy Comparison Report CSV Files                            *
*_____________________________________________________________________________________________*
*                                                                                             *
*  No user input required, reports will automatically be saved to current directory           *
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
        # Debug Print
        if debug: json.dumps(response_json)

        # Store policy links only for each product type
        policies = {'android':[],'ios':[],'linux':[],'mac':[],'network':[],'windows':[]}
        for policy in response_json['data']:
            policies[policy['product']].append(policy['links']['policy'])

        # Paginate if needed
        while 'next' in response_json['metadata']['links']:
            next_url = response_json['metadata']['links']['next']
            response = session.get(next_url)
            response_json = response.json()
            for policy in response_json['data']:
                # Store link, product, and name in existing dictionary
                policies[policy['product']].append(policy['links']['policy'])

        # Get script file path
        path = os.path.dirname(os.path.realpath(__file__))

        print(f'Number of polices found: {len(policies)}')
        print('Downloading Policies....\n')
        # Iterate over all policies for each product type separately
        for product,links in policies.items():
            # Skip any Apple IOS Policies
            if product == 'ios': continue
            # Get first Policy to create initial Pandas Dataframe, then delete from links
            policy_link = links[0]
            response = session.get(f'{policy_link}.xml')
            DF = json_normalize(xmltodict.parse(response.text))
            links.pop(0)
            # Iterate over remaining links if list not empty
            if len(links) >= 1:
                for policy_link in links:
                    response = session.get(f'{policy_link}.xml')
                    DFa = json_normalize(xmltodict.parse(response.text))
                    DF = concat([DF,DFa],ignore_index=True)

            # Change index columns and save as CSV
            DF.set_index(["Signature.Object.config.janus.policy.name","Signature.Object.config.janus.policy.uuid"],inplace=True)
            DF.to_csv(f'{product}_policy_report.csv')

            print(f'Polciy report completed for {product}... ')


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
        debug = config['debug']
        # Debug Print
        if debug: print('!\nDEBUG ENABLED!\n!')

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
*  3. Create Policy comparison reports                                                        *
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
*  3. Create Policy comparison reports                                                        *
*                                                                                             *
***********************************************************************************************
''')
        Loop = input('*\n*\nWould You Like To use another tool? [y/N]: ').lower()
        if Loop not in (['yes','ye','y']):
            break


