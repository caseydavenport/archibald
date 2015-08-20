import requests
from oauth_hook import OAuthHook
from requests import request
from urlparse import parse_qs
import webbrowser
import csv
import pdb
import time

GET_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_token'
AUTHORIZATION_URL = 'https://api.login.yahoo.com/oauth/v2/request_auth'
REQUEST_TOKEN_URL = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
CALLBACK_URL = 'oob'

class AuthException(Exception):
	pass

class YHandler(object):

	def __init__(self, authf):
		self.authf = authf
		self.authd = self.get_authvals_csv(self.authf)


	def get_authvals_csv(self, authf):
		vals = {}	#dict of vals to be returned
		with open(authf, 'rb') as f:
			f_iter = csv.DictReader(f)
			vals = f_iter.next()
		return vals
		

	def write_authvals_csv(self, authd, authf):
		f = open(authf, 'wb')
		fieldnames = tuple(authd.iterkeys())
		headers = dict((n,n) for n in fieldnames)
		f_iter = csv.DictWriter(f, fieldnames=fieldnames)
		f_iter.writerow(headers)
		f_iter.writerow(authd)
		f.close

	def reg_user(self):
		init_oauth_hook = OAuthHook(consumer_key=self.authd['consumer_key'], consumer_secret=self.authd['consumer_secret'])
		req = requests.Request('POST', REQUEST_TOKEN_URL, params={'oauth_callback': CALLBACK_URL})
		req = init_oauth_hook(req)
		session = requests.session()
		response = session.send(req.prepare())
		qs = parse_qs(response.text)
		self.authd['oauth_token']= (qs['oauth_token'][0])
		self.authd['oauth_token_secret'] = (qs['oauth_token_secret'][0])
		
		#now send user to approve app
		print "You will now be directed to a website for authorization.\n\
		Please authorize the app, and then copy and paste the provide PIN below."
		print "URL: %s?oauth_token=%s" % (AUTHORIZATION_URL, self.authd['oauth_token'])
		self.authd['oauth_verifier'] = raw_input('Please enter your PIN:')
		print "OAuth Verifier: %s" % self.authd['oauth_verifier']
		
		#get final auth token
		self.get_login_token()

	def get_login_token(self):
		#oauth_hook = OAuthHook(access_token=self.authd['oauth_token'], 
	#			access_token_secret=self.authd['oauth_token_secret'], 
#				consumer_key=self.authd['consumer_key'], 
#				consumer_secret=self.authd['consumer_secret'])
                signature = "%s%%26%s" % (self.authd['consumer_secret'], self.authd['oauth_token_secret'])
                timestamp = int(time.time())
                FMT = "%s?oauth_consumer_key=%s&oauth_signature_method=PLAINTEXT&oauth_verion=1.0&oauth_verifier=%s&oauth_token=%s&oauth_signature=%s&oauth_timestamp=%s&oauth_nonce=1228169662"
                URL = FMT % (GET_TOKEN_URL,
			self.authd['consumer_key'],
			self.authd['oauth_verifier'],
			self.authd['oauth_token'],
                        signature, timestamp)
          
		req = requests.Request('POST', URL) 
		#req = oauth_hook(req)
		req.headers.update({'oauth_verifier': self.authd['oauth_verifier']})
		session = requests.session()
		response = session.send(req.prepare())

		qs = parse_qs(response.content)
		print ("Get login token: %s" % qs)
		
		self.authd.update(map(lambda d: (d[0], (d[1][0])), qs.items()))
		self.write_authvals_csv(self.authd, self.authf)
		print("Login token response: %s" % response)
		return response

	def refresh_token(self):
		oauth_hook = OAuthHook(access_token=self.authd['oauth_token'], access_token_secret=self.authd['oauth_token_secret'], consumer_key=self.authd['consumer_key'], consumer_secret=self.authd['consumer_secret'])
		request = requests.Request("POST", GET_TOKEN_URL, {'oauth_session_handle': self.authd['oauth_session_handle']})
                request = oauth_hook(request)
		session = requests.session()
                response = session.send(request.prepare())
		qs = parse_qs(response.content)
		self.authd.update(map(lambda d: (d[0], (d[1][0])), qs.items()))
		self.write_authvals_csv(self.authd, self.authf)

	def call_api(self, url, req_meth='GET', data=None, headers=None):
                req = requests.Request(req_meth, url, data=data, headers=headers)
		req_oauth_hook = OAuthHook(self.authd['oauth_token'], self.authd['oauth_token_secret'], self.authd['consumer_key'], self.authd['consumer_secret'], header_auth=True)
                req = req_oauth_hook(req)
		session = requests.session()
                resp = session.send(req.prepare())
		#print resp.text
		return resp 

	def api_req(self, querystring, req_meth='GET', data=None, headers=None):
		base_url = 'http://fantasysports.yahooapis.com/fantasy/v2/'
		url = base_url + querystring
		self.refresh_token()
		if ('oauth_token' not in self.authd) or \
			('oauth_token_secret' not in self.authd) or \
			(not (self.authd['oauth_token'] and self.authd['oauth_token_secret'])):
			self.reg_user()
		query = self.call_api(url, req_meth, data=data, headers=headers)
		if query.status_code != 200: #We have both authtokens but are being rejected. Assume token expired. This could be a LOT more robust
			self.refresh_token()
			query = self.call_api(url, req_meth, data=data, headers=headers)
		if query.status_code != 200:
			print "Query failed: %s" % query.status_code
			print query.text
			raise AuthException()
		return query
