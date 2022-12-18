from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='pythonnuketools',
    version='0.1.1',
    description='Python library for modeling nuclear weapons effects and creating GIS artifacts',
    author='Lane Willard',
    author_email='lane.willard@gmail.com',
    url='https://github.com/lwillard/pythonnuketools',
    license='MIT',    
    py_modules=['lib/pythonnuketools'],
    install_requires=['numpy', 'scipy', 'affine', 'glasstone', 'shapely', 'simplekml']
)

