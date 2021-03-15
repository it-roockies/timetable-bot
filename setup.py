from setuptools import setup, find_packages


def parse_r(filename):
    return list(
        line.rstrip('\n') for line in open(f"./{filename}")
        if line and not line.startswith('#') and line.rstrip('\n')
    )


setup(
    name="timetablebot",
    packages=find_packages(exclude=("tests*", )),
    include_package_data=True,
    zip_safe=False,
    version="1.0.0",
    author="IT Roockies",
    author_email="ak@netsyno.com",
    description="Time table bot project.",
    long_description=
    "Telegram Time table bot for TTPU Students",
    url="https://google.com/",
    install_requires=parse_r('requirements.txt'),
    package_data={'timetablebot': ['README.md']}
)
