from setuptools import setup

setup(
  name = 'cloudchain',
  packages = ['cloudchain'], # this must be the same as the name above
  version = '0.1.2',
  description = 'Secure, easy secrets.',
  author = 'Jonathan Buys',
  author_email = 'jonathan.buys@targetsmart.com',
  url = 'https://github.com/targetsmart-devops/cloudchain.git',
  download_url = 'https://github.com/targetsmart-devops/cloudchain.git',
  keywords = ['secrets', 'password', 'account'],
  classifiers = [],
  install_requires=[
    'boto3==1.3.1',
    'botocore==1.4.18',
    'docutils==0.12',
    'futures==3.0.5',
    'jmespath==0.9.0',
    'python-dateutil==2.5.3',
    'six==1.10.0',
  ],
  entry_points={
    'console_scripts': ['cchain=cloudchain.command_line:main'],
  }
)
