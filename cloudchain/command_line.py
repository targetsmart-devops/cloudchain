from __future__ import print_function  # Python 2/3 compatibility

import argparse
import cloudchain


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

    group = parser.add_mutually_exclusive_group(required=True)
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
