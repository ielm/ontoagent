from setuptools import setup, find_packages

setup(
    name="OntoAgent",
    version="3.1.0",
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=[
        "OntoGraph==0.17.2",
        "pymongo==3.7.2",
        "Flask-Cors==3.0.3",
        "Flask-Socketio==3.2.1",
        "requests==2.18.4",
        "psycopg2-binary==2.8.3",
    ],
    dependency_links=["http://www.trulysmartagents.org/simple/ontograph"],
    author="Ivan Leon",
    author_email="i.leonmaldonado@gmail.com",
    description="OntoAgent architecture for designing and running an intelligent agent.",
    keywords="agent",
    project_urls={
        "Documentation": "https://app.nuclino.com/LEIA/OntoAgent",
        "Source Code": "https://bitbucket.org/leia-rpi/ontoagent/src/master/",
    },
)
