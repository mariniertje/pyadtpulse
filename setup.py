from setuptools import setup

setup(name='pyadtpulse',
      version='0.0.1',
      description='Library to interface with portal.adtpulse.com accounts',
      url='http://github.com/mariniertje/pyadtpulse',
      author='Jeroen Goddijn',
      author_email='mariniertje@gmail.com',
      license='MIT',
      packages=['pyadtpulse'],
      install_requires=[
        "selenium",
	  ],
      zip_safe=True)