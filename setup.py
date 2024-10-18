from setuptools import find_packages, setup

setup(
    name="developers-chamber",
    version="0.1.22",
    description="A small plugin which help with development, deployment, git",
    keywords="django, skripts, easy live, git, bitbucket, Jira",
    author="Druids team",
    author_email="matllubos@gmail.com",
    url="https://github.com/druids/django-project-info",
    license="MIT",
    package_dir={"developers_chamber": "developers_chamber"},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        "click>=8.1",
        "requests>=2.23.0",
        "python-dotenv==0.14.0",
        "python-hosts==0.4.6",
        "coloredlogs==10.0",
        "click-completion==0.5.2",
        "toml>=0.10.2",
    ],
    extras_require={
        "slack": [
            "slack-sdk==3.21.3",
        ],
        "aws": [
            "boto3<2",
        ],
        "qa": [
            "gitpython==3.1.30",
            "isort==5.12.0",
            "flake8>=7.0.0",
        ],
        "bitbucket": [
            "gitpython==3.1.30",
        ],
        "gitlab": [
            "gitpython==3.1.30",
        ],
        "jira": [
            "gitpython==3.1.30",
            "jira==2.0.0",
            "unidecode==1.1.1",
        ],
        "toggle": [
            "TogglPy==0.1.2",
        ],
        "git": [
            "gitpython==3.1.30",
        ],
    },
    entry_points={
        "console_scripts": [
            "pydev=developers_chamber.bin.pydev:cli",
        ]
    },
    zip_safe=False,
)
