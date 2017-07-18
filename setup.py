import setuptools

import devdocs_cli

setuptools.setup(
    name='devdocs-cli',
    version=devdocs_cli.__version__,
    url='https://github.com/kdeal/devdocs-cli',

    author='Kyle Deal',
    author_email='kdeal@kyledeal.com',

    description='Devdocs integration for alfred',
    long_description=open('README.rst').read(),

    packages=setuptools.find_packages('.', exclude=('tests*',)),

    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'devdocs = devdocs_cli.__main__:main',
        ]
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
