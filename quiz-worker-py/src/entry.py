from workers import Response, WorkerEntrypoint
from submodule import (
    get_pubs, post_pub, put_pub,
    get_visits, post_visit,
    post_comparison, put_comparison,
    get_rankings,
    index,
    login_page,
    login,
    profile_page,
)
from utils import decode_jwt_token
from urllib.parse import urlparse, parse_qs
from datetime import datetime

class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # return Response(get_hello_message())
        parsed_url = urlparse(request.url)
        pathname = parsed_url.path
        params = parse_qs(parsed_url.query)

        if request.method in ['POST', 'PUT']:
            body = await request.json()

        # Hopefully there are no '=' characters within the cookie itself!
        cookies = {
            cookie[0]: cookie[1]
            for cookie in [
                cookie_set.split('=')
                for cookie_set in request.headers.get('cookie', '').split('; ')
            ]
            if len(cookie) > 1
        }
        jwt_encoded = cookies.get('authToken')
        logged_in_user_id = None
        if jwt_encoded is not None:
            jwt_decoded = decode_jwt_token(jwt_encoded)
            if datetime.now() > jwt_decoded['expiry']:
                logged_in_user_id = None
            else:
                logged_in_user_id = jwt_decoded['user_id']

        # TODO: many of these API endpoints are not necessary (handled internally)! Remove them and their respective functions

        if pathname == '/api/pub':
            if request.method == 'GET':
                return await get_pubs(self.env.DB, params)
            elif request.method == 'POST':
                return await post_pub(logged_in_user_id, self.env.DB, body)
            elif request.method == 'PUT':
                return await put_pub(logged_in_user_id, self.env.DB, body)

        elif pathname == '/api/visit':
            if request.method == 'GET':
                return await get_visits(self.env.DB, params)
            elif request.method == 'POST':
                return await post_visit(logged_in_user_id, self.env.DB, body)

        elif pathname == '/api/comparison':
            if request.method == 'POST':
                return await post_comparison(logged_in_user_id, self.env.DB, body)
            elif request.method == 'PUT':
                return await put_comparison(logged_in_user_id, self.env.DB, body)

        elif pathname == '/api/rankings':
            if request.method == 'GET':
                return await get_rankings(self.env.DB, params)

        elif pathname == '/api/login':
            if request.method == 'POST':
                return await login(self.env.DB, body, self.env.PASSWORD_SALT)

        elif pathname == '/':
            # TODO: handle logged_in for login button and form visibility
            return await index(logged_in_user_id, self.env.DB, geoapify_key=self.env.GEOAPIFY_KEY)

        elif pathname == '/login':
            # TODO: handle logged_in for redirect to index
            return await login_page(self.env.DB)

        elif pathname == '/profile':
            return await profile_page(logged_in_user_id, self.env.DB)

        return Response(
            "No such endpoint"
        )
