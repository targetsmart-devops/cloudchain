import random
import string
import unittest
import tempfile

from cloudchain import cloudchain
from cloudchain.cloudchain import CloudChain
from cloudchain.cloudchain import CloudChainConfigError
from cloudchain.cloudchain import CloudChainError

FIXTURE_SERVICE_1 = 'test'
FIXTURE_USERNAME_1 = 'test'
FIXTURE_SECRET_1 = '(*&*&*&^@#$)(_'


def random_string(N=45):
    return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(N))


class MockTable:
    def __init__(self, table):
        self.t = table

    def get_item(self, Key):
        for k in Key:
            if k not in self.t:
                return {}
            if Key[k] != self.t[k]:
                return {}
        return self.t['return']

    def put_item(self, Item):
        return


class MockConnection:
    def __init__(self, table):
        self.table = table

    def Table(self, name):
        return self.table


class MockClient:
    def __init__(self, encrypted_text, decrypted_text):
        self.encrypted = {'CiphertextBlob': encrypted_text}
        self.decrypted = {'Plaintext': decrypted_text}

    def encrypt(self, KeyId, Plaintext, EncryptionContext):
        return self.encrypted

    def decrypt(self, CiphertextBlob, EncryptionContext):
        return self.decrypted


class MockBotoManager:
    def __init__(self, connection=None, client=None):
        self.client = client
        self.connection = connection

    def get_connection(self, service_name, aws_region_name=None, aws_endpoint_url=None):
        return self.connection

    def get_client(self, service_name, aws_region_name=None):
        return self.client


class TestCloudChain(unittest.TestCase):
    def setUp(self):
        table = MockTable({'Service': FIXTURE_SERVICE_1, 'Username': FIXTURE_USERNAME_1,
                           'return': {'Item': {'Secret': FIXTURE_SECRET_1}}})
        client = MockClient('onwfonadsfiasdfioanfon90j0ef0sfewnof', FIXTURE_SECRET_1)
        connection = MockConnection(table)
        self.cloud_chain = CloudChain('us-east-1', 'https://dynamodb.us-east-1.amazonaws.com', 'safedb',
                                      'alias/TS_Client_Key', MockBotoManager(client=client, connection=connection))

    def tearDown(self):
        self.cloud_chain = None

    def test_read_configfile(self):
        contents = """\
[dynamo]
region_name = test_region
endpoint_url = test_url
tablename = test_tablename

[IAMKMS]
keyalias = test_keyalias
"""
        tmp = tempfile.NamedTemporaryFile()
        tmp.write(contents)
        tmp.flush()
        config = cloudchain.read_configfile(tmp.name)
        self.assertEqual(config.get('dynamo', 'region_name'), 'test_region')
        self.assertEqual(config.get('dynamo', 'endpoint_url'), 'test_url')
        self.assertEqual(config.get('dynamo', 'tablename'), 'test_tablename')
        self.assertEqual(config.get('IAMKMS', 'keyalias'), 'test_keyalias')
        cloud_chain = cloudchain.get_default_cloud_chain()
        self.assertEqual(cloud_chain.region_name, 'test_region')
        self.assertEqual(cloud_chain.endpoint_url, 'test_url')
        self.assertEqual(cloud_chain.table_name, 'test_tablename')
        self.assertEqual(cloud_chain.key_alias, 'test_keyalias')

    def test_region_name_config_error(self):
        self.cloud_chain.set_region_name(None)
        self.assertRaises(CloudChainConfigError, self.cloud_chain.get_connection)

    def test_endpoint_url_config_error(self):
        self.cloud_chain.set_endpoint_url(None)
        self.assertRaises(CloudChainConfigError, self.cloud_chain.get_connection)

    def test_tablename_config_error(self):
        self.cloud_chain.set_table_name(None)
        self.assertRaises(CloudChainConfigError, self.cloud_chain.get_connection)

    def test_keyalias_config_error(self):
        self.cloud_chain.set_key_alias(None)
        self.assertRaises(CloudChainConfigError, self.cloud_chain.get_connection)

    def test_encryptcreds_not_empty(self):
        self.assertIsNotNone(self.cloud_chain.encrypt_credentials('string-to-encrypt'))

    def test_encryptcreds_not_same(self):
        self.assertNotEqual(
            self.cloud_chain.encrypt_credentials('string-to-encrypt'),
            'string-to-encrypt')

    def test_encryptcreds_long_string(self):
        self.assertGreater(len(self.cloud_chain.encrypt_credentials('string-to-encrypt')), 20)

    def test_savecreds_message(self):
        self.assertTrue(
            self.cloud_chain.save_credentials(
                FIXTURE_SERVICE_1,
                FIXTURE_USERNAME_1,
                FIXTURE_SECRET_1))

    def test_readcreds_found(self):
        self.assertIsNotNone(self.cloud_chain.read_credentials(FIXTURE_SERVICE_1, FIXTURE_USERNAME_1))

    def test_readcreds_service_not_found(self):
        self.assertRaises(CloudChainError,
                          self.cloud_chain.read_credentials, random_string(), FIXTURE_USERNAME_1)

    def test_readcreds_username_not_found(self):
        self.assertRaises(CloudChainError,
                          self.cloud_chain.read_credentials, FIXTURE_SERVICE_1, random_string())

    def test_readcreds_return_secret(self):
        self.assertEqual(self.cloud_chain.read_credentials(FIXTURE_SERVICE_1, FIXTURE_USERNAME_1),
                         FIXTURE_SECRET_1)

if __name__ == '__main__':
    # import logging
    # logging.basicConfig(level=logging.INFO)
    unittest.main()
