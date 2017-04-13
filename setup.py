from distutils.core import setup

setup(
    name='Facebook Messenger Bot',
    version='0.3',
    packages=['app'],
    install_requires=[
        'flask',
        'requests',
        'messengerbot',
        'mysqlclient'
    ],
    url='https://farbio.xyz',
    license='',
    author='Bionic Leha',
    author_email='i@farbio.xyz',
    description=''
)
