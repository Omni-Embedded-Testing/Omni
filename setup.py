from setuptools import setup, find_packages

with open('./Omni/requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name='Omni',
    version='0.0.1',
    packages=find_packages(include=['Omni', 'Omni.*']),
    entry_points={
        "console_scripts": [
            "omni-backend-start=Omni.cli.omni_start:main",
            "omni-backend-stop=Omni.cli.omni_stop:main",  
        ],
    },
    license="",
    install_requires=requirements,
    package_data={'Omni': [
        'tests/unit_tests/gdb_responses/*.*', 'requirements.txt', 'README.md', 'LICENSE']},
    author='Erick Setubal Bacurau',
    author_email='your@email.com',
    description='A Framework for Integration Testing in Embedded Systems',
    url='https://github.com/eks-99th/Omni',
)
