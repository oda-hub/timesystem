from setuptools import setup

setup(
        name='integral-timesystem',
        version='1.0',
        py_modules= ['timesystem'],
        package_data     = {
            "": [
                "*.txt",
                "*.md",
                "*.rst",
                "*.py"
                ]
            },
        install_requires=[
            'flask',
            'requests',
            'pylru',
        ],
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),
        )
