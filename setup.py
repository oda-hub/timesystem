from distutils.core import setup

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
        license='Creative Commons Attribution-Noncommercial-Share Alike license',
        long_description=open('README.md').read(),
        )
