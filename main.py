#!/usr/bin/env python

import os

from google.appengine.ext import db
from google.appengine.api import images
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

kTemplatesDir = os.path.join(os.path.dirname(__file__), 'templates')

# TODO(jgessner): move these utility functions into their own little class.
def getTemplatePath(template):
  return os.path.join(kTemplatesDir, template)

class Maker(db.Model):
  user = db.UserProperty()
  first_name = db.StringProperty()
  last_name = db.StringProperty()
  image = db.BlobProperty()
  tags = db.StringListProperty()


class MeritBadge(db.Model):
  name = db.StringProperty()
  description = db.StringProperty()
  requirements = db.StringProperty()
  image = db.BlobProperty()


class Index(webapp.RequestHandler):
  def get(self):
    template_values = {
    }
    self.response.out.write(template.render(getTemplatePath('index.html'),
                                            template_values))


class NewMaker(webapp.RequestHandler):
  def get(self):
    template_values = {
    }
    self.response.out.write(template.render(getTemplatePath('new_maker.html'),
                                            template_values))

  def post(self):
    maker = Maker()
    maker.first_name = self.request.get('first_name')
    maker.last_name = self.request.get('last_name')
    if self.request.get("image"):
      maker.image = images.resize(self.request.get("image"), 200, 200)
    tags = self.request.get("tags").split(",")
    for tag in tags:
      maker.tags.append(tag)
    maker.put()

    self.redirect('/')


class Makers(webapp.RequestHandler):
  def get(self):
    makers_query = Maker.all()
    makers = makers_query.fetch(100)
    template_values = {
      'makers': makers,
      'tag': self.request.get('tag')
    }
    self.response.out.write(template.render(getTemplatePath('makers.html'),
                                            template_values))

class Skills(webapp.RequestHandler):
  def get(self):
    skills = {}
    makers_query = Maker.all()
    makers = makers_query.fetch(100)
    for maker in makers:
      for skill in maker.tags:
        if not skills.has_key(skill):
          skills[skill] = 0
        skills[skill] += 1

    template_values = {
      'skills': skills
    }
    self.response.out.write(template.render(getTemplatePath('skills.html'),
                                            template_values))

class Search(webapp.RequestHandler):
  def get(self):
    have_results = False
    makers = []
    skill = self.request.get("skill")
    if skill != "":
      have_results = True
      makers_query = Maker.all()
      makers_query.filter("tags", skill)
      makers = makers_query.fetch(100)

    template_values = {
      'makers': makers,
      'skill': skill,
      'have_results': have_results,
    }
    self.response.out.write(template.render(getTemplatePath('search.html'),
                                            template_values))

def main():
  paths = [
    ('/', Index),
    ('/new_maker', NewMaker),
    ('/makers', Makers),
    ('/skills', Skills),
    ('/search', Search),
  ]
  application = webapp.WSGIApplication(paths, debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
