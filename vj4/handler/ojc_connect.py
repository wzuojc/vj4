from aioauth_client import OAuth2Client
import aiohttp
import datetime
import asyncio
import random
import string
import yarl
import xmltodict

from vj4 import app
from vj4 import error
from vj4.model import user
from vj4.handler import base
from vj4.model import system
from vj4.util import options


class OujiangCollegeUnifiedAuthClient(OAuth2Client):
  def __init__(self):
    self.access_token_url = '{}/oauth/v2/token'.format(options.ojc_connect_uniauth_base_url)
    self.authorize_url = '{}/oauth/v2/auth'.format(options.ojc_connect_uniauth_base_url)
    self.base_url = format(options.ojc_connect_uniauth_base_url) + '/'
    self.name = 'ojc_unified_auth'
    self.user_info_url = '{}/api/oauth/user/info.basic'.format(options.ojc_connect_uniauth_base_url)
    super().__init__(client_id=options.ojc_connect_uniauth_client_id, client_secret=options.ojc_connect_uniauth_client_secret)
    self.params['redirect_uri'] = '{}/ojc/connect/uniauth'.format(options.url_prefix)
    self.params['scope'] = options.ojc_connect_uniauth_scope

  @staticmethod
  def user_parse(data):
    """Parse information from provider."""
    yield 'id', data.get('data').get('id')
    yield 'username', data.get('data').get('username')

def random_string(n: int):
  return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(n))


@app.route('/ojc/connect/uniauth', 'ojc_connect_uniauth', global_route=True)
class ConnectUnifiedAuthHandler(base.Handler):
  async def get(self):
    client = OujiangCollegeUnifiedAuthClient()
    if client.shared_key not in self.request.query:
      client.params['state'] = random_string(8)
      await self.update_session(oauth_ojc_state=client.params['state'])
      self.redirect(client.get_authorize_url())
      return

    if self.session.get('oauth_ojc_state') != self.request.query.get('state'):
      raise error.ThirdPartyConnectError(client.name, 'state {} doesn\'t match {}'.format(self.request.query.get('state'), self.session.get('oauth_ojc_state')))

    try:
      await client.get_access_token(self.request.query)
      _, uniAuthUserReturn = await client.user_info()
      ojcUser = uniAuthUserReturn['data']
    except aiohttp.web_exceptions.HTTPBadRequest as e:
      raise error.ThirdPartyConnectError(client.name, e)

    udoc = await user.get_by_ojcId(ojcUser['schoolId'])
    if udoc:
      await asyncio.gather(user.set_by_uid(udoc['_id'],
                                           loginat=datetime.datetime.utcnow(),
                                           loginip=self.remote_ip),
                           self.update_session(uid=udoc['_id']))
    else:
      uid = int(ojcUser['schoolId']) if ojcUser['schoolId'].isnumeric() else await system.inc_user_counter()
      password = random_string(16)
      await user.add(uid, ojcUser['username'], password, '{}@me.iojc.cn'.format(ojcUser['schoolId']), self.remote_ip)
      await user.set_by_uid(uid, ojcId=ojcUser['schoolId'])
      await self.update_session(new_saved=False, uid=uid)

    self.json_or_redirect(self.reverse_url('domain_main'))

@app.route('/ojc/connect/wzu', 'ojc_connect_wzu', global_route=True)
class ConnectWzuPortalHandler(base.Handler):
  async def get(self):
    auth_url = yarl.URL.build(
      scheme='http',
      host='rz.wzu.edu.cn',
      path='/zfca/login',
      port=80,
      query={
        'service': '{}/ojc/connect/wzu'.format(options.url_prefix)
      }
    )
    if 'ticket' not in self.request.query:
      self.redirect(str(auth_url))
      return

    try:
      auth_url.with_path('/zfca/serviceValidate')
      auth_url.update_query({
        'ticket': self.request.query.get('ticket')
      })
      async with aiohttp.ClientSession() as session:
        async with session.get(str(auth_url)) as resp:
          doc = xmltodict.parse(resp.text())
          raise error.ThirdPartyConnectError('wzu_cas', doc)
    except Exception as e:
      raise error.ThirdPartyConnectError('wzu_cas', e)

    # udoc = await user.get_by_ojcId(ojcUser['schoolId'])
    # if udoc:
    #   await asyncio.gather(user.set_by_uid(udoc['_id'],
    #                                        loginat=datetime.datetime.utcnow(),
    #                                        loginip=self.remote_ip),
    #                        self.update_session(uid=udoc['_id']))
    # else:
    #   uid = int(ojcUser['schoolId']) if ojcUser['schoolId'].isnumeric() else await system.inc_user_counter()
    #   password = random_string(16)
    #   await user.add(uid, ojcUser['username'], password, '{}@me.iojc.cn'.format(ojcUser['schoolId']), self.remote_ip)
    #   await user.set_by_uid(uid, ojcId=ojcUser['schoolId'])
    #   await self.update_session(new_saved=False, uid=uid)
    #
    # self.json_or_redirect(self.reverse_url('domain_main'))