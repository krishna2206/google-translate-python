from setuptools import setup, find_packages

VERSION = '2.0.2'
DESCRIPTION = 'A free and unlimited python API for google translate.'
LONG_DESCRIPTION = 'A free and unlimited python API for google translate, use the reverse engineered Google Translate Ajax API.'

setup(
    name="google-translate-python",
    version=VERSION,
    author="krishna2206",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=['requests'],
    keywords=['python', 'google', 'translate', 'translation', 'ajax', 'api'],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ]
)