#!/usr/bin/env python

import logging
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
  badges = db.ListProperty(db.Key)

  def getImgSrc(self):
    if self.image:
      return '<img src="/pic?maker=%s" width=200 height=200 />' % self.key()
    else:
      return ""

  def getBadges(self):
    return MeritBadge.get(self.badges)

class MeritBadge(db.Model):
  name = db.StringProperty()
  description = db.StringProperty()
  requirements = db.StringProperty()
  image = db.BlobProperty()
  granters = db.ListProperty(db.Key)

  def getImgSrc(self):
    if self.image:
      return '<img src="/pic?badge=%s" width=200 height=200 />' % self.key()
    else:
      return ""

class Index(webapp.RequestHandler):
  def get(self):
    template_values = {
    }
    self.response.out.write(template.render(getTemplatePath('index.html'),
                                            template_values))


class NewMaker(webapp.RequestHandler):
  def get(self):
    badges = MeritBadge.all().fetch(100)
    template_values = {
      'badges': badges,
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
    badges = self.request.str_params.getall("badges")
    for badge in badges:
      logging.info("Badge is %s" % badge)
      meritBadge = MeritBadge.get(badge)
      if meritBadge:
        logging.info("Found a badge named %s" % meritBadge.name)
        maker.badges.append(meritBadge.key())
    maker.put()

    self.redirect('/')

class NewBadge(webapp.RequestHandler):
  def get(self):
    template_values = {}
    self.response.out.write(template.render(getTemplatePath('new_badge.html'),
                                            template_values))

  def post(self):
    badge = MeritBadge.all()
    badge.name = self.request.get('name')
    badge.description = self.request.get('description')
    badge.requirements = self.request.get('requirments')
    if self.request.get("image"):
      badge.image = images.resize(self.request.get("image"), 200, 200)
    badge.put()

    self.redirect('/badges')

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

class Pic(webapp.RequestHandler):
  def detect_mime_type(self, image):
    if image[1:4] == 'PNG': return 'image/png'
    if image[0:3] == 'GIF': return 'image/gif'
    if image[6:10] == 'JFIF': return 'image/jpeg'
    return None

  def get(self):
    if self.request.get("maker"):
      maker = Maker.get(self.request.get('maker'))
      if maker.image:
        filetype = self.detect_mime_type(maker.image)
        self.response.headers['Content-Type'] = filetype
        self.response.out.write(maker.image)
      else:
        self.response.out.write('no image found')
    elif self.request.get("badge"):
      badge = MeritBadge.get(self.request.get('badge'))
      if badge.image:
        filetype = self.detect_mime_type(badge.image)
        self.response.headers['Content-Type'] = filetype
        self.response.out.write(badge.image)
      else:
        self.response.out.write('no image found')

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

class Badges(webapp.RequestHandler):
  def get(self):
    badges_query = MeritBadge.all()
    badges = badges_query.fetch(100)
    template_values = {
      'badges': badges,
    }
    self.response.out.write(template.render(getTemplatePath('badges.html'),
                                            template_values))

class Search(webapp.RequestHandler):
  def get(self):
    have_results = False
    makers = []
    skill = self.request.get("skill")
    badge = self.request.get("badge")
    if skill:
      have_results = True
      makers_query = Maker.all()
      makers_query.filter("tags", skill)
      makers = makers_query.fetch(100)
    elif badge:
      have_results = True
      makers_query = Maker.all()
      makers_query.filter("badges", badge)
      makers = makers_query.fetch(100)

    template_values = {
      'makers': makers,
      'skill': skill,
      'badge': badge,
      'have_results': have_results,
    }
    self.response.out.write(template.render(getTemplatePath('search.html'),
                                            template_values))

def main():
  paths = [
    ('/', Index),
    ('/badges', Badges),
    ('/new_badge', NewBadge),
    ('/new_maker', NewMaker),
    ('/makers', Makers),
    ('/pic', Pic),
    ('/skills', Skills),
    ('/search', Search),
  ]
  application = webapp.WSGIApplication(paths, debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
