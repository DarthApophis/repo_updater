"""
Setup module that builds the distributable and installs it
"""
import os.path

from setuptools import setup
from setuptools.command.install import install
from setuptools.command.sdist import sdist

PACKAGE_NAME = "repo_updater"
DESCRIPTION = "A tool which can perform continuously update on a local repository."


class SdistPhaseCommand(sdist):
    """
    Sdist phase class. This class contains the basic sdist methods that
    are called during a "python setup.py sdist" command.
    """


    def initialize_options(self):
        """
        Something like "__init__" for sdist command chain
        """
        sdist.initialize_options(self)

    def finalize_options(self):
        """
        Methods to be used after the options are successfully initialized.
        """
        sdist.finalize_options(self)

    def run(self):
        """
        Running sdist command along with other needed methods (before and after run command)
        """
        sdist.run(self)

    def make_distribution(self):
        """
        Used to call methods after run command
        """
        sdist.make_distribution(self)


class PostInstallCommand(install):
    """
    Install phase class. This class contains the basic install methods that
    are called during a "pip install dist/" command.
    """
    def run(self):
        install.run(self)


def get_install_requirements():
    with open(os.path.join("requirements.txt")) as f:
        ir = f.read().splitlines()
    return ir


setup(
    name=PACKAGE_NAME,
    version="0.0.1",
    description=DESCRIPTION,
    entry_points={
        "console_scripts": [
            "repo_updater=repo_updater:main.main",
        ],
    },
    cmdclass={
        "sdist": SdistPhaseCommand,
        "install": PostInstallCommand
    },
    packages=[
        "repo_updater"
    ],
    include_package_data=True,
    install_requires=get_install_requirements(),
    author="Albert Calinescu",
    author_email="albert_calinescu@yahoo.com",
    url="N/A",
    license="@TBD",
)
