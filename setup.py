from setuptools import setup, find_packages

setup(
    name='developers-chamber',
    version='0.0.1',
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
        'requests>=2.22.0',
    ],
    entry_points={'console_scripts': [
        'release-version=developers_chamber.bin.release_version:cli',
        'release-git=developers_chamber.bin.release_git:cli',
        'release-bitbucket=developers_chamber.bin.release_bitbucket:cli',
    ]},
    zip_safe=False
)
