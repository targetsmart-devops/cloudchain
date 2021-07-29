from setuptools import setup

setup(
    name='cloudchain',
    packages=['cloudchain'],  # this must be the same as the name above
    version='0.1.7',
    description='Secure, easy secrets.',
    author='Jonathan Buys',
    author_email='jonathan.buys@targetsmart.com',
    url='https://github.com/targetsmart-devops/cloudchain.git',
    download_url='https://github.com/targetsmart-devops/cloudchain.git',
    keywords=['secrets', 'password', 'account'],
    classifiers=[],
    install_requires=[
        'boto3',
    ],
    entry_points={
        'console_scripts': ['cchain=cloudchain.command_line:main'],
    }
)
