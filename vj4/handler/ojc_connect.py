from aiohttp import web_exceptions
from aioauth_client import OAuth2Client
import datetime
import asyncio
import random
import string

from vj4 import app
from vj4 import error
from vj4.model import user
from vj4.handler import base
from vj4.model import system


ojc_uniauth_client_params = {
  'client_id': '59f0ad47-ff6a-11e8-8ebc-2c534a035500_qj88wvsi8i880ss8k8gwc0kog8o4ckc0ok484s80g08w0gsc8',
  'client_secret': '40gv91hljp8g8ow0gsgos4gs44sc484cwkss00sk8o84ggwo4s',
  'redirect_uri': 'http://10.11.99.13/ojc/connect/uniauth',
  'scope': 'authorization_code user:info.basic app:internal_access.full'
}

class OujiangCollegeUnifiedAuthClient(OAuth2Client):
  access_token_url = 'http://10.11.99.9:8016/oauth/v2/token'
  authorize_url = 'http://10.11.99.9:8016/oauth/v2/auth'
  base_url = 'http://10.11.99.9:8016/'
  name = 'ojc_unified_auth'
  user_info_url = 'http://10.11.99.9:8016/api/oauth/user/info.basic'

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
    client = OujiangCollegeUnifiedAuthClient(client_id=ojc_uniauth_client_params['client_id'], client_secret=ojc_uniauth_client_params['client_secret']);
    client.params['redirect_uri'] = ojc_uniauth_client_params['redirect_uri']
    client.params['scope'] = ojc_uniauth_client_params['scope']
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
    except web_exceptions.HTTPBadRequest as e:
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
      await user.add(uid, ojcUser['username'], password, '{}@auth.iojc.cn'.format(ojcUser['schoolId']), self.remote_ip)
      await user.set_by_uid(uid, ojcId=ojcUser['schoolId'])
      await self.update_session(new_saved=False, uid=uid)

    self.json_or_redirect(self.reverse_url('domain_main'))

