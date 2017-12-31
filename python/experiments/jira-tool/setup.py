from setuptools import setup

setup(
    name='cbjira',
    version='0.1',
    py_modules=['cbjira'],
    install_requires=[
        'click',
    ],
    entry_points='''
        [console_scripts]
        jira=cbjira:topcli
    ''',
)
