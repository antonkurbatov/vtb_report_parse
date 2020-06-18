import setuptools


def install_requires(rfile):
    with open(rfile) as fd:
        pkgs = fd.read().strip().splitlines()
    return pkgs


setuptools.setup(
    name='vtb_report_parse',
    version='0.0.1',
    description='VTB report parser',
    packages=setuptools.find_packages(),
    install_requires=install_requires('requirements.txt'),
    zip_safe=False,

    entry_points={
        'console_scripts': [
            'vtb_report_parse = vtb_report_parse.cli:main'
        ],
    }
)
