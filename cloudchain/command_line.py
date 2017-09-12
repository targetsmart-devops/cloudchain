from __future__ import print_function  # Python 2/3 compatibility

import argparse
import cloudchain
import json
from base64 import b64decode


def main():

    parser = argparse.ArgumentParser(description='Save or retrieve passwords.')

    parser.add_argument(
        '-u',
        '--user',
        help='User name'
    )

    parser.add_argument(
        '-e',
        '--service',
        help='Service or application'
    )

    parser.add_argument(
        '--export',
        help='Export all secrets, decrypted, to stdout'
    )

    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument(
        '-s',
        '--save',
        help='Save password to the cloudchain'
    )

    group.add_argument(
        '-r',
        '--read',
        action='store_true',
        help='Read password from the cloudchain'
    )

    args = vars(parser.parse_args())

    cloudchain.read_configfile()

    if (args['save']):
        cloudchain.savecreds(args['service'], args['user'], args['save'])
        print("Secret saved!")

    if (args['read']):
        print(cloudchain.readcreds(args['service'], args['user']))

    if (args['export']):
        localexport = []
        cloudchain.cache_creds()
        items = cloudchain.localcache["Items"]
                        
        for entry in items:
            if entry["Secret"]:
                decrypted = cloudchain.decryptcreds(b64decode(entry['Secret']))
            newitem = {"Service": entry["Service"], "Username": entry["Username"], "Secret": decrypted}
            localexport.append(newitem)
        print(json.dumps(localexport, sort_keys=True, indent=4, separators=(',', ': ')))
