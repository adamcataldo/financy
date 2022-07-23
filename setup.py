from setuptools import setup, find_packages

setup(
    name='financy',
    version='0.1.0',
    description='financy',
    author='Adam Cataldo',
    url='https://github.com/adamcataldo/financy',
    packages=find_packages(exclude=('tests', 'scripts'))
)
