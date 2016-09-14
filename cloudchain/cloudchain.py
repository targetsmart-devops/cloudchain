import logging
import boto3
from base64 import b64encode
from base64 import b64decode
from configparser import RawConfigParser
import os
import os.path
import sys


class BotoManager:
    def __init__(self, aws_region_name=None, aws_endpoint_url=None):
        self.aws_region_name = aws_region_name
        self.aws_endpoint_url = aws_endpoint_url

    @staticmethod
    def __fail_if_none__(var, error):
        if var is None:
            raise CloudChainConfigError(error)

    def get_connection(self, service_name, aws_region_name=None, aws_endpoint_url=None):
        if aws_region_name is None:
            aws_region_name = self.aws_region_name
            BotoManager.__fail_if_none__(aws_region_name, 'Error CC1: Region name must be set.')
        if aws_endpoint_url is None:
            aws_endpoint_url = self.aws_endpoint_url
            BotoManager.__fail_if_none__(aws_endpoint_url, 'Error CC2: Endpoint URL must be set.')
        conn = boto3.resource(
            service_name,
            region_name=aws_region_name,
            endpoint_url=aws_endpoint_url
        )
        return conn

    def get_client(self, service_name, aws_region_name=None):
        if aws_region_name is None:
            aws_region_name = self.aws_region_name
            BotoManager.__fail_if_none__(aws_region_name, 'Error CC3: Region name must be set.')
        client = boto3.client(service_name, region_name=aws_region_name)
        return client


class CloudChainError(Exception):
    pass


class CloudChainConfigError(CloudChainError):
    pass


class CloudChain:
    def __init__(self, region_name=None,
                 endpoint_url=None, table_name=None,
                 key_alias=None, boto_manager=None,
                 bypass=False):
        """
        - region_name: AWS DynamoDB region, e.g., 'us-east-1'
        - endpoint_url: AWS DynamoDB endpoint, e.g., 'https://dynamodb.us-east-1.amazonaws.com'
        - table_name: AWS DynamoDB table name
        - keyalias: key alias, e.g., 'alias/TS_Client_Key'
        - boto_manager:
        - bypass: If set to True, read_credentials will always return None. This is useful for local development of feature that do not require secrets, without removing any cloudchain usage.
        """
        self.region_name = region_name
        self.endpoint_url = endpoint_url
        self.table_name = table_name
        self.key_alias = key_alias
        self.boto_manager = boto_manager
        self.bypass = bypass

    def set_region_name(self, region_name):
        self.region_name = region_name

    def set_endpoint_url(self, endpoint_url):
        self.endpoint_url = endpoint_url

    def set_table_name(self, table_name):
        self.table_name = table_name

    def set_key_alias(self, key_alias):
        self.key_alias = key_alias

    def set_boto_manager(self, boto_manager):
        self.boto_manager = boto_manager

    @staticmethod
    def read_configfile(configfile=None):
        """Read configuration values from a text file (ConfigParser
        format). If `configfile` argument is non-None it will be
        used. Otherwise, if a CLOUDCHAIN_CONFIG environment variable is
        set that value will be used for the location of the configuration
        file. If the environment variable is not set, then ~/.cchainrc is
        used as the default configuration file location.

        Example:

        [dynamo]
        region_name = us-east-1
        endpoint_url = https://dynamodb.us-east-1.amazonaws.com
        tablename = safedb

        [IAMKMS]
        keyalias = alias/Client_Key

        """
        if configfile is None:
            configfile = os.environ.get('CLOUDCHAIN_CONFIG', None)

            if configfile is None:
                configfile = os.path.expanduser('~') + '/.cchainrc'
                logging.debug("Configuration file is %s taken from ~/.cchainrc default", configfile)
            else:
                logging.debug("Configuration file is %s taken from CLOUDCHAIN_CONFIG environment variable", configfile)
        else:
            logging.debug("Configuration file is %s taken from function argument", configfile)

        if not os.path.isfile(configfile):
            raise CloudChainConfigError(
                "Configuration file %s not found" % configfile)

        config = RawConfigParser()
        config.read(configfile)
        region_name = config.get('dynamo', 'region_name')
        endpoint_url = config.get('dynamo', 'endpoint_url')
        tablename = config.get('dynamo', 'tablename')
        keyalias = config.get('IAMKMS', 'keyalias')
        logging.debug("Set region_name to %s", region_name)
        logging.debug("Set endpoint_url to %s", endpoint_url)
        logging.debug("Set tablename to %s", tablename)
        logging.debug("Set keyalias to %s", keyalias)

        return config

    def check_config(self):
        if self.region_name is None:
            raise CloudChainConfigError()
        if self.endpoint_url is None:
            raise CloudChainConfigError("endpoint_url is not set")
        if self.table_name is None:
            raise CloudChainConfigError("tablename is not set")
        if self.key_alias is None:
            raise CloudChainConfigError("keyalias is not set")

    def get_connection(self):
        self.check_config()
        conn = self.boto_manager.get_connection('dynamodb')
        return conn

    def comp64encrypt(self, secret):
        if (sys.version_info > (3, 0)):
            if isinstance(secret, str):
                secret = secret.encode('ascii')

            return b64encode(secret).decode('ascii')
        else:
            return b64encode(secret)

    def save_credentials(self, service, username, creds):
        if self.bypass:
            logging.warning("No cloudchain credentials were saved as bypass was True")
            return True
        saved_string = self.encrypt_credentials(creds)
        conn = self.get_connection()
        table = conn.Table(tablename)
        table.put_item(
            Item={
                'Service': service,
                'Username': username,
                'Secret': self.comp64encrypt(saved_string)
            }
        )
        return True

    def encrypt_credentials(self, creds):
        client = self.boto_manager.get_client('kms')
        encrypted_key = client.encrypt(
            KeyId=keyalias,
            Plaintext=creds,
            EncryptionContext={
                'string': 'string'
            }
        )

        secret = encrypted_key['CiphertextBlob']
        return secret

    def decrypt_credentials(self, creds):
        client = self.boto_manager.get_client('kms')
        decrypted_key = client.decrypt(
            CiphertextBlob=creds,
            EncryptionContext={
                'string': 'string'
            }
        )
        return decrypted_key['Plaintext']

    def read_credentials(self, service, username):
        if self.bypass:
            logging.warning("No cloudchain credentials were read as bypass was set to True")
            return None

        conn = self.get_connection()
        table = conn.Table(tablename)
        response = table.get_item(
            Key={
                'Service': service,
                'Username': username
            }
        )
        try:
            item = response['Item']
        except KeyError:
            raise CloudChainError("Query failed. The service or username value provided was not found")
        decrypted_credentials = self.decrypt_credentials(b64decode(item['Secret']))
        return decrypted_credentials


region_name = None
endpoint_url = None
tablename = None
keyalias = None
cloud_chain = None
bypass = False

def get_default_cloud_chain():
    global cloud_chain

    if cloud_chain is None:
        cloud_chain = CloudChain(region_name, endpoint_url, tablename, keyalias, BotoManager(region_name, endpoint_url), bypass)
    return cloud_chain


def read_configfile(configfile=None):
    global region_name
    global endpoint_url
    global tablename
    global keyalias

    config = CloudChain.read_configfile(configfile)
    region_name = config.get('dynamo', 'region_name')
    endpoint_url = config.get('dynamo', 'endpoint_url')
    tablename = config.get('dynamo', 'tablename')
    keyalias = config.get('IAMKMS', 'keyalias')

    return config


def checkconfig():
    if not any([region_name, endpoint_url, tablename, keyalias]):
        read_configfile()

    return get_default_cloud_chain().check_config()


def getconn():
    checkconfig()
    return get_default_cloud_chain().get_connection()


def savecreds(service, username, creds):
    return get_default_cloud_chain().save_credentials(service, username, creds)


def encryptcreds(creds):
    return get_default_cloud_chain().encrypt_credentials(creds)


def decryptcreds(creds):
    return get_default_cloud_chain().decrypt_credentials(creds)


def readcreds(service, username):
    return get_default_cloud_chain().read_credentials(service, username)
