from setuptools import setup

setup(
    name='django-trackmodels-ritual',
    version='1.0.0',
    packages=[
        'grimoire.django.tracked',
        'grimoire.django.tracked.models'
    ],
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
    install_requires=['Django>=2.2', 'python-dateutil>=2.6.1', 'python-cantrips>=1.0.0']
)