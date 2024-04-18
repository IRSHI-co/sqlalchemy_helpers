from setuptools import setup, find_packages

setup(
    name='sqlalchemy_helpers',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        # list of required packages
        'sqlalchemy', 'marshmallow', 'flask-restx'
    ],
)