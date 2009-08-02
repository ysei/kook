###
### $Release: $
### $Copyright$
### $License$
###

import oktest
from oktest import *
import sys, os, re

from kook import KookRecipeError
from kook.cookbook import Cookbook, Recipe, TaskRecipe, FileRecipe
from kook.utils import write_file


bookname = 'Kookbook.py'

class KookCookbookTest(object):

    def setup(self, input):
        write_file(bookname, input)

    def after_each(self):
        if os.path.exists(bookname):
            os.unlink(bookname)


    def test_new(self):
        input = r"""
@recipe
def file_html(c):
  pass
"""[1:]
        self.setup(input)
        ## if bookname is not specified, Kookbook is not loaded
        book = Cookbook.new(None)
        ok(book, 'is a', Cookbook)
        ok(book.bookname, '==', None)
        ok(book.specific_file_recipes, '==', ())
        ## if bookname is specified, Kookbook is loaded automatically
        book = Cookbook.new(bookname)
        ok(book, 'is a', Cookbook)
        ok(book.bookname, '==', bookname)
        recipes = book.specific_file_recipes
        ok(recipes, 'is a', list)
        ok(len(recipes), '==', 1)
        ok(recipes[0], 'is a', FileRecipe)

    def test_load_file(self):
        book = Cookbook.new(None)
        ok(book.bookname, '==', None)
        ok(book.specific_file_recipes, '==', ())
        input = r"""
@recipe
def file_html(c):
    pass
"""[1:]
        self.setup(input)
        ## load Kookbook
        book.load_file(bookname)
        ok(book.bookname, '==', bookname)
        recipes = book.specific_file_recipes
        ok(recipes, 'is a', list)
        ok(recipes[0], 'is a', FileRecipe)

    def test_load__set_self_bookname(self):
        "set self.bookname"
        input = r"""
@recipe
def compile(c):
  pass
"""[1:]
        ## before loading, bookname is None
        book = Cookbook.new(None)
        ok(book.bookname, '==', None)
        ## after loaded, bookname is specified
        book.load(input, '<kookbook>')
        ok(book.bookname, '==', '<kookbook>')

    def test_load__task_recipes(self):
        input = r"""
@recipe      # without @product nor prefix
def build(c):
  pass

@recipe      # with 'task_' prefix
def task_build(c):
  pass

@recipe      # with @product
@product('build')
def task_build_files(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input, '<kookbook>')
        recipes = book.specific_task_recipes
        ok(recipes, 'is a', list)
        ok(len(recipes), '==', 3)
        expected = r"""
#<TaskRecipe
  byprods=(),
  desc=None,
  func=<function build>,
  ingreds=(),
  name='build',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok(recipes[0]._inspect(), '==', expected)
        expected = r"""
#<TaskRecipe
  byprods=(),
  desc=None,
  func=<function task_build>,
  ingreds=(),
  name='task_build',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok(recipes[1]._inspect(), '==', expected)
        expected = r"""
#<TaskRecipe
  byprods=(),
  desc=None,
  func=<function task_build_files>,
  ingreds=(),
  name='task_build_files',
  pattern=None,
  product='build',
  spices=None>
"""[1:-1]
        ok(recipes[2]._inspect(), '==', expected)

    def test_load__file_recipes(self):
        input = r"""
@recipe      # with @product and 'file_' prefix
@product('*.html')
def file_ext_html(c):
  pass

@recipe      # without @product
def file_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        # generic recipe
        ok(book.generic_file_recipes, 'is a', list)
        ok(len(book.generic_file_recipes), '==', 1)
        expected = r"""
#<FileRecipe
  byprods=(),
  desc=None,
  func=<function file_ext_html>,
  ingreds=(),
  name='file_ext_html',
  pattern='^(.*?)\\.html$',
  product='*.html',
  spices=None>
"""[1:-1]
        ok(book.generic_file_recipes[0]._inspect(), '==', expected)
        # specific recipe
        ok(book.specific_file_recipes, 'is a', list)
        ok(len(book.specific_file_recipes), '==', 1)
        expected = r"""
#<FileRecipe
  byprods=(),
  desc=None,
  func=<function file_html>,
  ingreds=(),
  name='file_html',
  pattern=None,
  product='html',
  spices=None>
"""[1:-1]
        ok(book.specific_file_recipes[0]._inspect(), '==', expected)

    def test_load__error_if_no_prefix_with_product(self):
        input = r"""
@recipe
@product('*.html')
def ext_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        def f():
            book.load(input)
        ok(f, 'raises', KookRecipeError, "ext_html(): prefix ('file_' or 'task_') required when @product() specified.")

    def test_load__re_pattern(self):
        input = r"""
import re
@recipe
@product(re.compile(r'.*\.html'))   # pass rexp
def file_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        recipe = book.generic_file_recipes[0]
        ok(recipe.pattern, 'is a', type(re.compile('dummy')))

    def test_load__materials(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ok(book.materials, '==', ('index.html', ))
        ## kook_materials should be tuple or list
        input = r"""
kook_materials = ('index.html')
"""[1:]
        book = Cookbook.new(None)
        def f():
            book.load(input)
        errmsg = "'index.html': kook_materials should be tuple or list."
        ok(f, 'raises', KookRecipeError, errmsg)

    def test_material_p(self):
        input = r"""
kook_materials = ('index.html', )
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ok(book.material_p('index.html'), '==', True)
        ok(book.material_p('index.txt'), '==', False)

    def test_find_recipe(self):
        ## for file recipes
        input = r"""
@recipe
@product('*.html')
def file_html(c):
  pass

@recipe
@product('index.html')
def file_index_html(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ## generic file recipe
        recipe = book.find_recipe('foo.html')
        ok(recipe, 'is a', FileRecipe)
        ok(recipe.name, '==', 'file_html')
        ## specific file recipe
        recipe = book.find_recipe('index.html')
        ok(recipe, 'is a', FileRecipe)
        ok(recipe.name, '==', 'file_index_html')
        ## for task recipe
        input = r"""
@recipe
@product('package_*')
def task_package(c):
  pass

@recipe
def package_123(c):
  pass
"""[1:]
        book = Cookbook.new(None)
        book.load(input)
        ## generic task recipe
        recipe = book.find_recipe('package_100')
        ok(recipe, 'is a', TaskRecipe)
        ok(recipe.name, '==', 'task_package')
        ## specific task recipe
        recipe = book.find_recipe('package_123')
        ok(recipe, 'is a', TaskRecipe)
        ok(recipe.name, '==', 'package_123')
        ## return None if not found
        ok(book.find_recipe('package123'), 'is', None)


if __name__ == '__main__':
    oktest.invoke_tests('Test$')
