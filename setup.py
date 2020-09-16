import setuptools

with open("README.md", "r") as fh:
   long_description = fh.read()

setuptools.setup(
   name="aurcore",
   version="0.1.0",
   author="Zenith00",
   author_email="z@zenith.dev",
   description="Aurora",
   long_description=long_description,
   long_description_content_type="text/markdown",
   url="https://github.com/Zenith00/aurora",
   packages=setuptools.find_packages(),
   classifiers=[
      "Programming Language :: Python :: 3",
   ],
   install_requires=[],
   tests_require=[]
)
