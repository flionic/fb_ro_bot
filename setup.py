from distutils.core import setup

setup(
    name='Facebook Messenger Bot',
    version='0.3',
    packages=[''],
    install_requires=[
        'flask',
        'requests',
        'messengerbot',
        'mysqlclient'
    ],
    url='https://farbio.xyz',
    license='GNU',
    author='Bionic Leha',
    author_email='i@farbio.xyz',
    description='Using Facebook Messanger Bot API for Radio One page on FB'
)
