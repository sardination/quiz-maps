from workers import Response

from argon2 import PasswordHasher
import json
import random
from js import Object
from templates.index_template import INDEX_TEMPLATE
from templates.login_template import LOGIN_TEMPLATE
from templates.profile_template import PROFILE_TEMPLATE
from utils import (
    bradley_terry_simple,
    get_upcoming_events,
    create_jwt_token,
    logged_in_user,
)

async def index(logged_in_user_id, db, geoapify_key=None):
    pub_ranking = await _get_rankings(db, {})
    all_pubs = await _get_all_pubs(db)
    upcoming_events = get_upcoming_events(all_pubs)

    return Response(
        INDEX_TEMPLATE(
            logged_in_user_id,
            all_pubs,
            pub_ranking,
            upcoming_events,
            geoapify_key=geoapify_key
        ),
        headers={"Content-Type": "text/html"}
    )

async def login_page(db):
    return Response(
        LOGIN_TEMPLATE,
        headers={"Content-Type": "text/html"}
    )

async def profile_page(logged_in_user_id, db):
    if logged_in_user_id is None:
        return Response(
            "<html><body><p>User is not logged in.</p></body></html>",
            headers={"Content-Type": "text/html"}
        )

    user_visits = await _get_visits(db, {'user_id': logged_in_user_id})
    all_pubs = await _get_all_pubs(db)
    incomplete_comparisons = await _get_incomplete_comparisons(db, logged_in_user_id)

    return Response(
        PROFILE_TEMPLATE(
            user_visits,
            all_pubs,
            incomplete_comparisons,
        ),
        headers={"Content-Type": "text/html"}
    )

async def login(db, body, server_salt):
    failure_response = Response.json(
        {'message': 'No users with these credentials'},
        status=401
    )

    salted_password = body['password'] + server_salt

    query = (
        await db.prepare(
            "SELECT * FROM user WHERE username = ?"
        )
        .bind(body['username'])
        .run()
    )
    if len(query.results) == 0:
        return failure_response

    user = query.results[0]

    db_hashed_password = user.password
    ph = PasswordHasher()
    try:
        ph.verify(db_hashed_password, salted_password)
    except:
        return failure_response

    if ph.check_needs_rehash(db_hashed_password):
        (
            await db.prepare(
                "UPDATE user SET password = ? WHERE username = ?"
            )
            .bind(ph.hash(salted_password), body['username'])
        )

    return Response.json({
        'message': 'Successfully logged in',
        'token': create_jwt_token(user.id, user.username)
    })


async def _get_incomplete_comparisons(db, logged_in_user_id):
    query = (
        await db.prepare(
            """
            SELECT comparison.*, visit.pub_id, visit.date, pub.name AS pub_name FROM comparison
            LEFT JOIN visit
            ON comparison.visit_id = visit.id
            LEFT JOIN pub
            ON visit.pub_id = pub.id
            WHERE visit.user_id = ? AND comparison.better IS NULL
            """
        ).bind(logged_in_user_id)
        .run()
    )

    return query.results

async def _get_all_pubs(db):
    query = (
        await db.prepare(
            "SELECT * FROM pub"
        )
        .run()
    )
    return query.results
async def get_all_pubs(db):
    return Response.json(_get_all_pubs(db))

async def get_pubs(db, params):
    # TODO: make this an IS IN for multiple pub ids
    pub_id = params['id'][0]
    query = (
        await db.prepare(
            "SELECT * FROM pub WHERE id = ?",
        )
        .bind(pub_id)
        .run()
    )
    return Response.json(query.results)

@logged_in_user
async def post_pub(logged_in_user_id, db, body):
    query = (
        await db.prepare(
            """
                INSERT INTO pub (
                    place_id, name, address, frequency,
                    day_of_week, weeks_of_month, time, timezone,
                    lat, lng
                ) VALUES (?,?,?,?,?,?,?,?,?,?) RETURNING *
            """,
        )
        .bind(
            body['place_id'],
            body['name'],
            body['address'],
            body['frequency'],
            body['dayOfWeek'],
            ','.join(body.get('weeksOfMonth', [])),
            body['time'],
            body['timezone'],
            body['lat'],
            body['lng']
        )
        .run()
    )
    return Response.json(query.results)

@logged_in_user
async def put_pub(logged_in_user_id, db, body):
    query = (
        await db.prepare(
            """
                UPDATE pub
                SET name = ?, frequency = ?, day_of_week = ?, weeks_of_month = ?, time = ?
                WHERE id = ?
                RETURNING *
            """,
        )
        .bind(
            body['name'],
            body['frequency'],
            body['dayOfWeek'],
            ','.join(body.get('weeksOfMonth', [])),
            body['time'],
            body['id']
        )
        .run()
    )
    return Response.json(query.results)

async def _get_visits(db, where_cols):
    if len(where_cols.keys()) == 0:
        query = (
            await db.prepare(
                """
                SELECT visit.*, pub.name FROM visit
                LEFT JOIN pub
                ON visit.pub_id = pub.id
                """,
            )
            .run()
        )
    else:
        where_clauses = [
            f"visit.{col} = ?" for col in where_cols.keys()
        ]
        query = (
            await db.prepare(
                f"""
                SELECT visit.*, pub.name FROM visit
                LEFT JOIN pub
                ON visit.pub_id = pub.id
                WHERE {' AND '.join(where_clauses)}
                """,
            )
            .bind(*where_cols.values())
            .run()
        )

    return query.results
async def get_visits(db, params):
    # TODO: restrict access to visits to owning users?

    where_cols = {}

    if 'visit_id' in params.keys():
        visit_id = params['visit_id'][0]
        where_cols['visit_id'] = visit_id
    if 'pub_id' in params.keys():
        pub_id = params['pub_id'][0]
        where_cols['pub_id'] = pub_id
    if 'user_id' in params.keys():
        user_id = params['user_id'][0]
        where_cols['user_id'] = user_id

    return Response.json(_get_visits(db, where_cols))

@logged_in_user
async def post_visit(logged_in_user_id, db, body):
    query = (
        await db.prepare(
            "INSERT INTO visit (user_id, pub_id, date) VALUES (?,?,?) RETURNING *",
        )
        .bind(logged_in_user_id, body['pub_id'], body['date'])
        .run()
    )
    visit = query.results[0]

    # Find (up to) three random noninclusive visited pubs to compare against
    noninclusive_pubs = (
        await db.prepare(
            "SELECT DISTINCT pub_id AS id FROM visit WHERE pub_id != ?"
        ).bind(body['pub_id'])
        .run()
    ).results
    compare_pubs = random.sample(noninclusive_pubs, min(3, len((noninclusive_pubs))))

    response = Object.new()
    response.visit = visit

    if len(compare_pubs) > 0:
        # Create empty comparisons
        bind_values = []
        for compare_pub in compare_pubs:
            bind_values.extend([visit.id, compare_pub.id])

        comparison_query = (
            await db.prepare(
                f"INSERT INTO comparison (visit_id, compare_pub_id) VALUES {', '.join(["(?,?)"] * len(compare_pubs))} RETURNING *"
            ).bind(*bind_values)
            .run()
        )

        response.comparisons = comparison_query.results

    else:
        response.comparisons = []

    return Response.json(response)

async def _does_visit_belong_to_user(db, user_id, comparison_id):
    query = (
        await db.prepare(
            """
            SELECT * FROM comparison
            LEFT JOIN visit
            ON comparison.visit_id = visit.id
            WHERE comparison.id = ? AND visit.user_id = ?
            """
        )
        .bind(comparison_id, user_id)
        .run()
    )

    return len(query.results) > 0

@logged_in_user
async def post_comparison(logged_in_user_id, db, body):
    if not await _does_visit_belong_to_user(db, logged_in_user_id, body['visit_id']):
        return Response.json({})

    query = (
        await db.prepare(
            "INSERT INTO comparison (visit_id, compare_pub_id) VALUES (?,?) RETURNING *",
        )
        .bind(body['visit_id'], body['compare_pub_id'])
        .run()
    )
    return Response.json(query.results)

@logged_in_user
async def put_comparison(logged_in_user_id, db, body):
    if not await _does_visit_belong_to_user(db, logged_in_user_id, body['id']):
        return Response.json({})

    query = (
        await db.prepare(
            """
            UPDATE comparison
            SET better = ?
            WHERE id = ?
            RETURNING *
            """
        )
        .bind(body['better'], body['id'])
        .run()
    )

    return Response.json(query.results)

async def _get_rankings(db, params):
    # TODO: support getting rankings for just one user
    try:
        user_id = params['user_id'][0]
    except:
        pass

    # TODO: introduce recency bias

    # Get all comparisons and their visits
    query = (
        await db.prepare(
            """
            SELECT *
            FROM comparison
            LEFT JOIN visit
            ON comparison.visit_id = visit.id
            """
        )
        .run()
    )

    # Use bradley-terry to order using pairwise comparisons
    pub_list = list(set([e.pub_id for e in query.results]).union(set([e.compare_pub_id for e in query.results])))
    n_pub_ids = len(pub_list)
    pub_idx_map = {pub_list[i]: i for i in range(n_pub_ids)}
    pub_idx_map_rev = {i: pub_list[i] for i in range(n_pub_ids)}

    pairs = [
        (e.pub_id, e.compare_pub_id) if e.better else (e.compare_pub_id, e.pub_id)
        for e in query.results
    ]

    # Use list indices
    pairs = [(pub_idx_map[pub_a_id], pub_idx_map[pub_b_id]) for pub_a_id, pub_b_id in pairs]
    model_estimate = bradley_terry_simple(pairs, n_pub_ids)

    # Assign order to original pub ids
    pub_id_params = {pub_idx_map_rev[i]: model_estimate[i] for i in range(n_pub_ids)}
    pub_order = [pub_id for pub_id, param in sorted(pub_id_params.items(), key=lambda item: -item[1])]

    return pub_order
async def get_rankings(db, params):
    return Response.json(_get_rankings(db, params))

