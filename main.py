#!/usr/bin/env python

__author__ = 'bigendian@gmail.com'

import logging
import wsgiref.handlers
import cgi, cgitb
import os
import sys
from getimageinfo import getImageInfo
from google.appengine.ext import db
from google.appengine.api import mail
from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.api import images
from google.appengine.api.images import im_feeling_lucky
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

class AdminHandler(webapp.RequestHandler):

	def get(self):

		template_name = "admin.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		values = {
				'page_title': "ADMIN -- Welcome to Nothing Tees!",
			}

		# Respond to the request by rendering the template
		self.response.out.write(template.render(path, values))


class UnknownHandler(webapp.RequestHandler):
	def get(self):
		self.redirect('/')

	def post(self):
		self.redirect('/')


class DetailHandler(webapp.RequestHandler):

	def get(self):

		template_name = "detail.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		## Get shirt data from database
		product = db.get(self.request.get("id"))

		values = {
				'page_title': "Welcome to Nothing Tees!",
				'product': product,
			}

		# Respond to the request by rendering the template
		self.response.out.write(template.render(path, values))

	
class UploadHandler(webapp.RequestHandler):

	def __init__ (self):

		self.user = users.get_current_user()


	def post(self):

		## Identify desired template
		template_name = "upload.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		user = users.get_current_user()

		if not self.user:
			self.redirect(users.create_login_url(self.request.uri))

		msg = None

		author = None
		if users.get_current_user():
			author = users.get_current_user()

		description = self.request.get("description")
		title       = self.request.get("title")
		price       = float(self.request.get("price"))
		image       = self.request.get("image")
		imageblob   = db.Blob(image)
		imagetype   = getImageInfo(image)

		product = Product(author = author, title = title, description = description, price = price, image = imageblob, imagetype = imagetype[0])

		product.put()
		msg = "New product uploaded!"

		body = None

		values = { 
				'page_title': "ADMIN -- Welcome to Nothing Tees!",
				'author': "THIS IS __author__",
				'version': 1,
				'body': body,
				'msg': msg,
			}

		self.response.out.write(template.render(path, values))

	def get(self):

		template_name = "upload.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		body = None

		values = { 
				'page_title': "ADMIN -- Welcome to Nothing Tees!",
				'author': "THIS IS __author__",
				'version': 1,
				'body': body,
			}

		self.response.out.write(template.render(path, values))


## Admin edit products page handler
class EditHandler (webapp.RequestHandler):

	def get(self):

		template_name = "edit.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		query_str = "SELECT * FROM Product ORDER BY date DESC"
		products = db.GqlQuery(query_str)

		# This generates our shopping list form and writes it in the response
		body = None

		values = { 
				'page_title': "ADMIN -- Welcome to Nothing Tees!",
				'author': "THIS IS __author__",
				'body': body,
				'version': 1,
				'products': products,
			}

		self.response.out.write(template.render(path, values))

	def post(self):

		## Identify desired template
		template_name = "edit.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		user = users.get_current_user()

#		if not self.user:
#			self.redirect(users.create_login_url(self.request.uri))

		product = db.get(self.request.get("id"))

		msg = None

		if users.get_current_user():
			author = users.get_current_user()
			product.author = author

		if self.request.get("delete"):
			delete = self.request.get("delete")
			logging.info('DEBUG: Permanently deleting item: %s' % product.title)
			msg = "Product deleted: %s" % product.title
			product.delete()

		else:

			if self.request.get("available"):
				description = self.request.get("available")
				logging.info('DEBUG: avilable == %s' % str(description))
				product.available = True
			else:
				product.available = False
	
			if self.request.get("title"):
				title = self.request.get("title")
				product.title = title
	
			if self.request.get("description"):
				description = self.request.get("description")
				product.description = description
	
			if self.request.get("price"):
				price       = float(self.request.get("price"))
				product.price = price
	
			if self.request.get("image"):
				image       = self.request.get("image")
				imageblob   = db.Blob(image)
				imagetype   = getImageInfo(image)
				product.image = image
	
			product.put()

			msg = "New product uploaded!"

		self.redirect('/admin/edit')



## ImageHandler class serves images from the database
class ImageHandler (webapp.RequestHandler):

	def get(self):

		shirt = db.get(self.request.get("id"))
		thumb = self.request.get("thumb")
		thumbsize = self.request.get("thumbsize")

		size = 400

		if shirt.image:
			self.response.headers['Content-Type'] = shirt.imagetype

			if (thumb == "1"):
				size = 150

			if (thumbsize):
				size = int(thumbsize)

			self.response.out.write(images.resize(shirt.image, size, size))

		else:
			self.response.out.write("No image")

class MainHandler(webapp.RequestHandler):

	def get(self):

		template_name = "main.html"

		# Construct the path to the template
		directory = os.path.dirname(__file__)
		path = os.path.join(directory, 'templates', template_name)

		body = ""

		query_str = "SELECT * FROM Product WHERE available = True ORDER BY date DESC"
		shirts = db.GqlQuery(query_str)

		values = {
				'page_title': "Welcome to Nothing Tees!",
				'body': body,
				'shirts': shirts,
				'author': "THIS IS __author__",
				'version': 1
			}


		# Respond to the request by rendering the template
		self.response.out.write(template.render(path, values))

class Product(db.Model):
	author      = db.UserProperty()
	description = db.StringProperty(required=True,multiline=True)
	title       = db.StringProperty(required=False,multiline=False)
	image       = db.BlobProperty(required=True)
	imagetype   = db.StringProperty(required=True)
	date        = db.DateTimeProperty(auto_now_add=True)
	price       = db.FloatProperty(default=19.99)
	available   = db.BooleanProperty(default=True)
	recommended = db.ListProperty(db.Key)
#	tags        = db.ListProperty(db.Key)
#	categories  = db.CategoryProperty()


class ProductForm(djangoforms.ModelForm):
	class Meta:
		model = Product
		exclude = ['image', 'author', 'tags', 'categories']


def main():

	address = os.environ["REMOTE_ADDR"]

	octets = address.split(".")

	## Rusty Pelican: 209.20.186.225
#	if (octets[0] != "209" or octets[1] != "20" or octets[2] != "186"):
#	if (octets[0] != "127" or octets[1] != "0" or octets[2] != "0"):
#	if (octets[0] != "209" or octets[1] != "162" or octets[2] != "142"):
#		print "Content-type: text/html\n\nNothing Tees Coming Soon!"
#		sys.exit()


	application = webapp.WSGIApplication([
		('/',             MainHandler),
		('/img',          ImageHandler),
		('/detail',       DetailHandler),
		('/admin',        AdminHandler),
		('/admin/edit',   EditHandler),
		('/admin/upload', UploadHandler),
		('/.*',           UnknownHandler),

	], debug=True)

	run_wsgi_app(application)

if __name__ == '__main__':
	main()
