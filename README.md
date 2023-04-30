# Alphageist

## python-pptx

In order to get the python-pptx module to work you have to replace the pptx/compat/__ini__.py with the following:

```python
# encoding: utf-8

"""Provides Python 2/3 compatibility objects."""

import sys

import collections.abc

Mapping = collections.abc.Mapping
Sequence = collections.abc.Sequence

# As collections.abc.Container has been removed in Python 3.10, we use collections.abc.Collection as an alternative
if sys.version_info >= (3, 10):
    Container = collections.abc.Collection
else:
    Container = collections.abc.Container

if sys.version_info >= (3, 0):
    from .python3 import (  # noqa
        BytesIO,
        is_integer,
        is_string,
        is_unicode,
        to_unicode,
        Unicode,
    )
else:
    from .python2 import (  # noqa
        BytesIO,
        is_integer,
        is_string,
        is_unicode,
        to_unicode,
        Unicode,
    )
```

and class __PackageReader__ and ___ZipPkgReader__ in ppx/opc/seralized.py should be modified accordingly:

```python
from collections.abc import Iterable
```

...

```python
class PackageReader(Container, Iterable):
    """Provides access to package-parts of an OPC package with dict semantics.

    The package may be in zip-format (a .pptx file) or expanded into a directory
    structure, perhaps by unzipping a .pptx file.
    """

    def __init__(self, pkg_file):
        self._pkg_file = pkg_file

    def __contains__(self, pack_uri):
        """Return True when part identified by `pack_uri` is present in package."""
        return pack_uri in self._blob_reader

    def __getitem__(self, pack_uri):
        """Return bytes for part corresponding to `pack_uri`."""
        return self._blob_reader[pack_uri]

    def __iter__(self):
        """Iterate over the package parts."""
        return iter(self._blob_reader)

    def __len__(self):
        """Return the number of package parts."""
        return len(self._blob_reader)

    def rels_xml_for(self, partname):
        """Return optional rels item XML for `partname`.

        Returns `None` if no rels item is present for `partname`. `partname` is a
        |PackURI| instance.
        """
        blob_reader, uri = self._blob_reader, partname.rels_uri
        return blob_reader[uri] if uri in blob_reader else None

    @lazyproperty
    def _blob_reader(self):
        """|_PhysPkgReader| subtype providing read access to the package file."""
        return _PhysPkgReader.factory(self._pkg_file)
```

...

```python

class _ZipPkgReader(_PhysPkgReader, Iterable):
    """Implements |PhysPkgReader| interface for a zip-file OPC package."""

    def __init__(self, pkg_file):
        self._pkg_file = pkg_file

    def __contains__(self, pack_uri):
        """Return True when part identified by `pack_uri` is present in zip archive."""
        return pack_uri in self._blobs

    def __getitem__(self, pack_uri):
        """Return bytes for part corresponding to `pack_uri`.

        Raises |KeyError| if no matching member is present in zip archive.
        """
        if pack_uri not in self._blobs:
            raise KeyError("no member '%s' in package" % pack_uri)
        return self._blobs[pack_uri]

    def __iter__(self):
        """Iterate over the package parts."""
        return iter(self._blobs)

    def __len__(self):
        """Return the number of package parts."""
        return len(self._blobs)

    @lazyproperty
    def _blobs(self):
        """dict mapping partname to package part binaries."""
        with zipfile.ZipFile(self._pkg_file, "r") as z:
            return {PackURI("/%s" % name): z.read(name) for name in z.namelist()}
```
