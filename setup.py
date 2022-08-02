from setuptools import setup, find_packages

setup(
    name='developers-chamber',
    version='0.0.64',
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
        'oauthlib==3.1.0',
        'gitpython==3.1.0',
        'click==7.0',
        'requests==2.23.0',
        'python-dotenv==0.14.0',
        'boto3<2',
        'python-hosts==0.4.6',
        'isort==4.3.21',
        'coloredlogs==10.0',
        'click-completion==0.5.2',
        'jira==2.0.0',
        'unidecode==1.1.1',
        'TogglPy==0.1.2',
        'flake8==4.0.1',
    ],
    entry_points={'console_scripts': [
        'pydev=developers_chamber.bin.pydev:cli',
    ]},
    zip_safe=False
)
