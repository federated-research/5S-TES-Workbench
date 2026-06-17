# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'five-safes-TES-workbench'
copyright = '2026, University of Nottingham'
author = 'University of Nottingham'
release = '0.2.5'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
import os
import sys

sys.path.insert(0, os.path.abspath('../../src'))  # Adjust to include your package

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
]
pygments_style = "sphinx"       # enable syntax highlighting

# Napoleon settings for Google/NumPy-style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

#html_theme = 'alabaster'
html_theme = 'furo'
html_static_path = ['_static']
