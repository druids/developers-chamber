from setuptools import setup, find_packages

setup(
    name='developers-chamber',
    version='__version__',
    description='A small plugin which help with development, deployment, git',
    keywords='django, skripts, easy live, git, bitbucket, Jira',
    author='Druids team',
    author_email='matllubos@gmail.com',
    url='https://github.com/druids/django-project-info',
    license='MIT',
    package_dir={'developers_chamber': 'developers_chamber'},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'gitpython==3.1.0',
        'click==7.0',
        'requests==2.22.0',
        'python-dotenv==0.10.3',
        'boto3==1.9.230',
        'python-hosts==0.4.6',
        'isort==4.3.21',
        'coloredlogs==10.0',
        'click-completion==0.5.2',
        'jira==2.0.0',
        'unidecode==1.1.1',
        'TogglPy==0.1.1',
        'attrdict==2.0.1',
    ],
    entry_points={'console_scripts': [
        'pydev=developers_chamber.bin.pydev:cli',
    ]},
    zip_safe=False
)
