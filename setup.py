from setuptools import setup, find_packages

setup(
    name='django-trackmodels-ritual',
    version='0.0.13',
    namespace_packages=['grimoire', 'grimoire.django'],
    packages=find_packages(exclude=['trackmodels_proj', 'trackmodels_proj.*', 'sample', 'sample.*']),
    package_data={
        'grimoire.django.tracked': [
            'locale/*/LC_MESSAGES/*.*',
            'templates/admin/*.html',
            'templates/admin/tracked/*.html',
        ]
    },
    url='https://github.com/luismasuelli/django-trackmodels-ritual',
    license='LGPL',
    author='Luis y Anita',
    author_email='luismasuelli@hotmail.com',
    description='The trackmodels library is useful to set creation/update/delete dates on models and track by them',
    install_requires=['Django>=1.7', 'python-dateutil>=2.6.1', 'python-cantrips>=0.7.5']
)
