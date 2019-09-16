from setuptools import setup, find_packages

setup(
    name='developers-chamber',
    version='0.0.11',
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
        'gitpython>=2.1.12',
        'click==7.0',
        'requests',
        'python-dotenv>=0.10.3',
        'boto3',
        'docker',
        'python-hosts',
    ],
    entry_points={'console_scripts': [
        'pydev=developers_chamber.bin.pydev:cli',
    ]},
    zip_safe=False
)
