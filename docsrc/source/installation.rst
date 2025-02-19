.. _installation:

Installation
=========================

Requirements
------------

To install DeerLab, first install Python on your computer. Python can be downloaded from the `official Python distribution <https://www.python.org/>`_. There are
many online tutorials to guide you through the installation and setup (see `here <https://realpython.com/installing-python/>`_ for example). Make sure you install
one of the Python versions compatible with DeerLab, either **Python 3.6**, **3.7**, **3.8**, or **3.9**  

.. rubric:: Windows systems

For Windows systems it is important to ensure that the **Install launcher for all users (recommended)** and  the **Add Python 3.x to PATH** checkboxes at the bottom are checked. To test if python has been successfully  installed, open a terminal window and run the command::

	python

which should display the installed Python version and launch the Python command line. To exit, use the ``exit()`` command or close the console.

Installing DeerLab
---------------------

Installing from PyPI
*********************

A pre-built distribution can be installed using `pip <https://pip.pypa.io/en/stable/installing/>`_.

First, it is important to ensure that ``pip`` is up-to-date. From a terminal (preferably with administrative privileges) use the following command::

		python -m pip install --upgrade pip

Next, install DeerLab and all its dependencies via::

		python -m pip install deerlab

DeerLab installs the following packages:

* `matplotlib <https://matplotlib.org/>`_ - A comprehensive library for creating data visualizations with Python
* `memoization <https://pypi.org/project/memoization/>`_ - A powerful caching library for Python
* `pytest <https://docs.pytest.org/en/stable/>`_ - A Python testing framework
* `cvxopt <https://cvxopt.org/index.html>`_ - Free software package for convex optimization
* `numpy <https://numpy.org/>`_ -   The fundamental package for scientific computing with Python 
* `scipy <https://www.scipy.org/>`_ - Fundamental library for scientific computing
* `joblib <https://joblib.readthedocs.io/en/latest/>`_ - Library lightweight pipelining and parallelization.

The installed numerical computing packages (numpy, scipy, cvxopt) are linked against different BLAS libraries depending on the OS:

* Windows: linked against the Intel Matrix Kernel Library (MKL)
* Linux: linked against OpenBLAS
* Mac: linked against BLAS/LAPACK from the Accelerate framework

If an error occurs during or after the installation, please consult `this section <./installation_failed.html>`_ for a possible solution.


Installing from Anaconda
*************************

DeerLab is also distributed via the Anaconda repository and the ``conda`` package manager.

Open the Anaconda prompt (preferably with administrative privileges) or activate the Anaconda environment. Next install DeerLab via the ``conda`` package manager as follows::

	conda install deerlab -c JeschkeLab 

The package manager will automatically take care of installing all DeerLab dependencies. 


Importing DeerLab
------------------

As a Python package, DeerLab must be imported before using it. For this, use the ``import`` statement: ::

    import deerlab as dl

This makes DeerLab functions accessible via the abbreviated name ``dl``. For example, the function ``fit`` can be called via ``dl.fit``. We recommend to use ``dl`` as the standard import abbreviation for DeerLab.



Updating to the latest release 
--------------------------------
To upgrade an existing DeerLab installation to the latest released version, use the following command from a terminal:: 

		python -m pip install --upgrade deerlab

or if you are using Anaconda use the following command from the Anaconda prompt::

		conda update deerlab

Other installations 
-------------------

Installing specific versions
*****************************

Any DeerLab version released after v0.10.0 can be installed via ``pip`` using the following command matching the x.y.z to the desired version::

		python -m pip install deerlab==x.y.z

or via ``conda`` if you use Anaconda as follows::

		conda install deerlab=x.y.z

DeerLab version prior to 0.10 are written in MATLAB and are still available from an `archived repository <https://github.com/JeschkeLab/DeerLab-Matlab>`_. 
Download and installation instruction for the MATLAB environment are provided in the released documentation. MATLAB releases have been deprecated and no further support is provided.


Installing from source
*****************************

If you wish to contribute to DeerLab or like to get the latest updates as they come, install DeerLab from ``git``. If your OS has not ``git`` installed, you can download it and install it from the `official Git distribution <https://git-scm.com/>`_.
To download (clone) the repository, execute the following from the command line::

		git clone https://github.com/JeschkeLab/DeerLab.git
		
To update to the latest version, go the local directory where DeerLab has been downloaded and execute::
		
		git pull origin main 

Now in the DeerLab directory run the installation script as follows to install DeerLab:: 

		python -m setup.py install

In order to install DeerLab but be able to edit the code or update frequently without having to re-install the package, use the command::

		python -m setup.py develop

Any changes made to the source code will then immediate effect.

