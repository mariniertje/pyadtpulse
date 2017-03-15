from setuptools import setup

__version__ = '0.0.1'

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# get the dependencies and installs
with open(path.join(here, 'requirements.txt'), encoding='utf-8') as f:
    all_reqs = f.read().split('\n')

install_requires = [x.strip() for x in all_reqs if 'git+' not in x]
dependency_links = [x.strip().replace('git+', '') for x in all_reqs if x.startswith('git+')]

setup(name='pyadtpulse',
      version='0.0.1',
      description='Library to interface with portal.adtpulse.com accounts',
      long_description=long_description,
      url='http://github.com/mariniertje/pyadtpulse',
	  download_url='https://github.com/mariniertje/pyadtpulse/archive/' + __version__,
      author='Jeroen Goddijn',
      author_email='mariniertje@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['docs', 'tests*']),
      include_package_data=True,
      install_requires=install_requires,
      dependency_links=dependency_links,
      zip_safe=True)
