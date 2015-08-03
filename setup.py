from setuptools import setup, find_packages

setup(
    name='django-project-info',
    version='0.2.5',
    description="A small plugin which takes a configuration (like Bower or npm) and it provides data via context processors.",
    keywords='django, project-info',
    author='Lukas Rychtecky',
    author_email='lukas.rychtecky@gmail.com',
    url='https://github.com/LukasRychtecky/django-project-info',
    license='MIT',
    package_dir={'project_info': 'project_info'},
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'django>=1.6',
        'gitpython>=0.3.2.RC1',
    ],
    zip_safe=False
)
