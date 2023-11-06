import os
import setuptools


with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = os.path.join(lib_folder, 'requirements.txt')

requirements = []
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        requirements = f.read().splitlines()


setuptools.setup(
    version='0.1.0',
    name='croco-web3-utils',
    author='Alexey',
    author_email='abelenkov2006@gmail.com',
    description='The package containing utilities to develop Web3-based projects',
    keywords='keywords',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/blnkoff/croco-web3-utils',
    project_urls={
        'Documentation': 'https://github.com/blnkoff/croco-web3-utils',
        'Bug Reports': 'https://github.com/blnkoff/croco-web3-utils/issues',
        'Source Code': 'https://github.com/blnkoff/croco-web3-utils',
    },
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS'
    ],
    python_requires='>=3.11',
    install_requires=requirements
)
