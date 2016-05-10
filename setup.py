from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
from Cython.Distutils import build_ext


ext_modules = [Extension('join', ['join.pyx'],
                language='c++',
                extra_compile_args=["-O2"]
               )]

setup(
	name = 'Join module',
	cmdclass = {'build_ext': build_ext},
	ext_modules = ext_modules
)

