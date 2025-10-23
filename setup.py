from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="plc-tcpip-bridge",
    version="0.1.0",
    author="Konstantinos Katsampiris Salgado",
    author_email="katsampiris.konst@gmail.com",
    description="A Python library for communicating with PLCs over TCP/IP",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kkats-mech/plc-tcpip-bridge",
    packages=find_packages(),
    python_requires=">=3.7",
    license="MIT",
    keywords="plc scada industrial automation tcp ip siemens s7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)