from setuptools import setup, find_packages

setup(
    name='django-project-info',
    version='1.0.0',
    description='A small plugin which takes a configuration (like Bower or npm) and it provides data via context'
    'processors.',
    keywords='django, project-info',
    author='Lukas Rychtecky',
    author_email='lukas.rychtecky@gmail.com',
    url='https://github.com/druids/django-project-info',
    license='MIT',
    package_dir={'project_info': 'project_info'},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'django>=1.11',
        'gitpython>=2.1.12',
        'click==7.0',
        'requests>=2.22.0',
    ],
    scripts=[
        'project_info/bin/release-version.py',
        'project_info/bin/release-git.py',
        'project_info/bin/release-bitbucket.py',
    ],
    zip_safe=False
)
