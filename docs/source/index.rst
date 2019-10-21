.. pocketcorr documentation master file, created by
   sphinx-quickstart on Wed Jan 14 23:42:57 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

`Leuschner Radio Spectrometer <https://github.com/domagalski/leuschner-spectrometer>`__
=======================================================================================

The `Leuschner spectrometer <https://github.com/domagalski/leuschner-spectrometer>`__
is a FPGA design running on a ROACH, along with Python code communicating with
it using KATCP and reading data to FITS files. 

- `Presentation for the AY121 class about the spectrometer <leuschner-spec.pdf>`__
- `Leuschner Webcam <http://ugastro.berkeley.edu/leuschner/leuschnercam.html>`__
- `Casper Wiki <https://casper.berkeley.edu/wiki/Main_Page>`__

IDL Interface
-------------

Astro 121 students can use IDL to collect spectra and save them to a FITS file
with the IDL function `leuschner_rx
<https://github.com/domagalski/leuschner-spectrometer/blob/master/idl/leuschner_rx.pro>`__,
which is installed on the Leuschner Radio server onsite at the dish. Python
users can use the python function `read_spec() <#leuschner.Spectrometer.read_spec>`__,
which has the same functionality. The inputs of ``leuschner_rx`` are as follows:

- ``filename``: Name of the output FITS file.
- ``nspec``: Number of spectra to collect.
- ``lonra``: Either galacic longitude or right ascension, in degrees.
- ``latdec``: Either galactic latitude or declination, in degrees.
- ``system``: Coordinate system of coordinates. Either ga or eq.

The ``leuschner_rx`` function returns the status of the accumulation. If the
status is ``0``, then everything worked as intended. If not, then there was an
error. Here is an example of how ``leuschner_rx`` is run in IDL: ::

    IDL> status = leuschner_rx('spectra.fits', 100, 210.0, 0.0, 'ga')
    IDL> print, status
        0

Alternatively, one can do the same thing in python easily: ::

    >>> import leuschner
    >>> spec = leuschner.Spectrometer('10.0.1.2')
    >>> spec.read_spec('spectra.fits', 100, (210.0, 0), 'ga')

Installation
------------

All you need to do is run ``python setup.py install`` and the software
will be installed. The .bof file to be run on the ROACH is provided in the fpga
directory of the rpoco8 git repo. It must be placed in the ``/boffiles``
directory on the ROACH so that KATCP knows that it exists. The spectrometer code
refers to the basename of the bof file, ``spec_ds8_8192.bof`` as is, so that
shouldn't be changed. The IDL file
`leuschner_rx.pro <https://github.com/domagalski/leuschner-spectrometer/blob/master/idl/leuschner_rx.pro>`__,
which can be found in the ``idl`` directory of the `spectrometer git repo
<https://github.com/domagalski/leuschner-spectrometer>`__, can be placed
anywhere, and the name of the directory that it's placed needs to be added to
the environment variable ``IDL_PATH`` in order for IDL to know about it. If
there are lots messages stating ``WARNING: Cannot reach the ROACH. Skipping
integration.``, then place a 1 GiB network switch between the ROACH and the
computer communicating with it and those messages should hopefully go away.

Clocking the spectrometer
-------------------------

The input clock to the iADC on the ROACH board needs to be set to 768 MHz using
an external local oscillator. The reason for this frequency is because the iADC
needs to be clocked four times the speed of the FPGA on the ROACH. Due to
hardware constraints, the ROACH is running eight times the speed of the desired
sampling rate and the data is downsampled by a factor of eight in the time
domain. The actual sampling rate of the spectrometer is 24 MHz, giving a 12 MHz
bandwidth. The spectrometer has 8192 frequency channels, giving a resolution of
about 1.4 kHz.

Dependencies
------------

This software requires the modules
`numpy <http://www.numpy.org/>`__,
`pyephem <http://rhodesmill.org/pyephem/>`__,
`pyfits <http://www.stsci.edu/institute/software_hardware/pyfits>`__,
`corr <https://github.com/ska-sa/corr>`__, and whatever those modules
depend on. 

Leuschner Spectrometer Python API
================================

.. automodule:: leuschner
   :members:

