from setuptools import setup

setup(
    name='commsrepl',
    version='0.0.1',
    description='pico REPL communication protocol for python over serial.',
    long_description=open('README.md').read(),
    install_requires=['pyserial']
)
