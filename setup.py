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
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Manufacturing",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        # No external dependencies required for core library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
        ],
    },
    keywords="plc scada industrial automation tcp ip siemens s7",
    project_urls={
        "Bug Reports": "https://github.com/kkats-mech/plc-tcpip-bridge/issues",
        "Source": "https://github.com/kkats-mech/plc-tcpip-bridge",
        "Documentation": "https://github.com/kkats-mech/plc-tcpip-bridge#readme",
    },
)