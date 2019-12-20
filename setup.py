from setuptools import setup
import os

packages = []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

for dirpath, dirnames, filenames in os.walk('presamples'):
    # Ignore dirnames that start with '.'
    if '__init__.py' in filenames:
        pkg = dirpath.replace(os.path.sep, '.')
        if os.path.altsep:
            pkg = pkg.replace(os.path.altsep, '.')
        packages.append(pkg)

f = open('README.md')
readme = f.read()
f.close()

f = open('LICENSE')
license_text = f.read()
f.close()

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


setup(
    name='presamples',
    version="0.2.6",
    packages=packages,
    author="Pascal Lesage",
    author_email="pascal.lesage@polymtl.ca",
    install_requires=[
        'bw2calc',
        'bw2data',
        'numpy',
        'peewee',
        'scipy',
        'stats_arrays',
        'wrapt',
    ],
    url="https://github.com/PascalLesage/presamples",
    long_description=readme,
    long_description_content_type="text/markdown",
    description='Package to write, load, manage and verify numerical arrays, called presamples.',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Information Analysis',
        'Topic :: Scientific/Engineering :: Mathematics',
    ],
)
