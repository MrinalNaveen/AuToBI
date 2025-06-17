# AuToBI-py

A Python wrapper and interfacing library around [AuToBI](https://github.com/AndrewRosenberg/AuToBI) that I wrote for my Bachelor's thesis. AuToBI is effectively the only publically available system for the automatic generation of prosody transcriptions, created by Andrew Rosenberg for his PhD in 2012.

Modern research uses AuToBI as a baseline but rarely interfaces with it directly (and when they do, they do so via the command line with all limitations that come with that, such as [AASP](https://github.com/UUDigitalHumanitieslab/AASP)), as modern tooling generally uses Python over Java.

AuToBI_py provides a simple Python interface for AuToBI's feature generation systems, as well as the parts of AuToBI that are available from the command line. Please check out the [README of the Python library](https://github.com/JJWRoeloffs/autobi_py/blob/master/python/README.md) for the Python documentation.

The project consists of three parts. AuToBI itself, which had to be forked and slightly rewritten to be able to provide the interface, an adapter that provides the JVM interface in Scala, and a python library that uses py4j to interface with this adapter and provide a cleaner python API.

## AuToBI

The AuToBI system for automatically generating prosody transcriptions, released under the Apache2 license. Only slightly modified for this version. There are two major changes to the original: the migration from Apache Ant to sbt, which is used for better cross-compiling, and the migration from Java 6 to Java 20, which was needed for loading the code into Python. Despite all these changes, the functional behavior should be identical to the original.

Build with sbt:

```sh
# Compile only autobi itself
sbt "autobi/compile"

# Create one "Uber-jar" that contains all dependencies
# Similar to how the original AuToBI was distributed
sbt "autobi/assembly"
```

Run tests:

```sh
sbt "autobi/test"
```

## Adapter

The AuTOBI adapter is a minimal Scala library written to turn the AuToBI application into a library. It exposes the core functionality of AuToBI in a way that makes it possible to interface it sensibly. Theoretically speaking, it could be used in any JVM language, however, it was written with py4j in mind, and thus key API functions only take strings as their inputs, making them less effective than one could expect of a native library.

Build with sbt:

```sh
# Compile only the adapter
sbt "adapter/compile"

# Compile the adapter into an "Uber-jar" that contains all dependencies.
# It is this exact jar that is being interfaced in the python library
sbt "adapter/assembly"
```

run tests:

```sh
# Currently, because of a lack of time, the test suite is only very minimal
sbt "adapter/test"
```

## Python library

The Python library is the part of this application that is expected to be used. This is the ultimate end-point of this project. It exposes the AuToBI adapter in a Python interface using py4j and contains some needed boilerplate for calling this Java/Scala code like it is native Python.

To run any Java or Scala code, a JVM needs to be running with the interfaced code available (through Java Reflections) in the jar. To compile this jar, move it to a location within the Python sources, and write the needed Python file to tell the other Python sources where it is, run:

```sh
sbt "python/assembly"
```

To work with the actual code, first `cd python`. After this, you are in a regular python library project. To run the tests run:

```sh
# Install current version of package locally to be able to test it.
python3 -m pip install -e .

python3 -m pytest --cov=autobi tests/
```
