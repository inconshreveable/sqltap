from setuptools import setup

setup(
    name = "sqltap",
    version = "0.1",
    description = "Profiling and introspection for applications using sqlalchemy",
    long_description = """Profiling and introspection for applications using sqlalchemy""",
    author = "aes",
    author_email = "alan@you-compete.com",
    url = "https://github.com/aes-/sqltap",
    packages = ["sqltap"],
    package_data = {"sqltap" : ["templates/*.mako"]},
    install_requires = [
        "SQLAlchemy >= 0.7",
        "Mako >= 0.3"
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Database'
    ]
)

