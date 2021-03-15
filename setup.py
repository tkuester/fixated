from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fixated",
    python_requires=">=3.5",
    use_scm_version=True,
    author="Tim K",
    author_email="tpkuester@gmail.com",
    setup_requires=["setuptools_scm"],
    install_requires=["pyserial>=3.0"],
    description="A simple GPS daemon",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tkuester/fixated",
    packages=find_packages(),
    classifiers=[
        "Topic :: Communications",
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.5",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={
        "console_scripts": [
            "fixated = fixated.__main__:main",
        ]
    },
)
